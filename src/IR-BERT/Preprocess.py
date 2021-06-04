import sys
sys.path.append("..")


def get_path_conf(filename):
	path_mp = {}
	with open(filename, 'r', encoding='utf-8') as f:
		for line in f:
			li = line[:-1].split('=')
			path_mp[li[0]] = li[1]
	return path_mp


# word split
def word_cut(s):
	s = re.sub("[\s+\.\!\/_,$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）]+", " ", s)
	return s.split(' ')


import os
import json
import re
from tqdm import tqdm
from elasticsearch import Elasticsearch
from nltk.stem.porter import *

# get file path conf
path_mp = get_path_conf('/Users/udhavsethi/dev/ref/TREC_background_linking/src/path.cfg')
es = Elasticsearch()
stemmer = PorterStemmer()
INDEX_NAME = "wapo21"


def extract_body(args = None):
    contents = args[0]
    body = ''
    for p in contents:
        if type(p).__name__ == 'dict':
            if 'subtype' in p and p['subtype'] == 'paragraph':
                paragraph = p['content'].strip()
                # Replace <.*?> with ""
                paragraph = re.sub(r'<.*?>', '', paragraph)
                body += ' ' + paragraph
    return body


def filter_kicker(doc):
    # Filter by kicker
    filter_kicker = {"Opinion": 1, "Letters to the Editor": 1, "The Post's View": 1}
    topic_name = ''
    for li in doc['contents']:
        if type(li).__name__ == 'dict':
            if 'type' in li and li['type'] == 'kicker':
                # skip filter kickers
                topic_name = li['content']
                if topic_name in filter_kicker.keys():
                    return False
    return topic_name


def process_washington_post(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        for line in tqdm(f):
            try:
                obj = json.loads(line)
                # if obj['id'] == "d1970396-0591-11e2-afff-d6c7f20a83bf":
                #     continue
                obj['kicker'] = filter_kicker(obj)
                if obj['kicker'] is False:
                    continue
                obj['body'] = extract_body([obj['contents']])

                # to lower case
                obj['title'] = str(obj['title']).lower()
                obj['body'] = str(obj['body']).lower()

                # stemming
                w_list = word_cut(obj['body'])
                for i in range(len(w_list)):
                    if w_list[i].isalpha():
                        w_list[i] = stemmer.stem(w_list[i])
                obj['body'] = ' '.join(w_list)
                w_list = word_cut(obj['title'])
                for i in range(len(w_list)):
                    if w_list[i].isalpha():
                        w_list[i] = stemmer.stem(w_list[i])
                obj['title'] = ' '.join(w_list)

                del obj['contents']
                if 'content' in obj:
                    date_blocks = [x for x in obj['content'] if ((x is not None) and ('type' in x) and (x['type'] == 'date'))]
                    if date_blocks:
                        for block in date_blocks:
                            obj['content'].remove(block)

                obj['title_body'] = (str(obj['title']) + ' ' + str(obj['body'])).lower()
                obj['title_author_date'] = (str(obj['title']) + ' ' + str(obj['author']) + ' ' + str(obj['published_date'])).lower()
                doc = json.dumps(obj)
                # insert data
                res = es.index(index=INDEX_NAME, id=obj['id'], body=doc)
            except Exception as e:
                if (obj is not None) and (obj['id'] is not None):
                    f1 = open("exception_ids.txt", "a")
                    f1.write("{}\n".format(obj['id']))
                    f1.close()
                    f2 = open("exceptions.txt", "a")
                    f2.write("id: {}, exception: {}\n".format(obj['id'],e))
                    f2.close()
                continue


# put all the news into elasticsearch
def init_es():
    # create index
    setting = {
        "index": {
            "mapping" : {
                "ignore_malformed" : "true"
            },
            "similarity": {
                "my_bm25": {
                    "type": "BM25",
                    "b": 0.75,
                    "k1": 1.2
                }
            }
        },
        "analysis" : {
            "analyzer" : {
                "synonym" : {
                    "tokenizer" : "whitespace",
                    "filter" : ["synonym"]
                }
            },
            "filter" : {
                "synonym" : {
                    "type" : "synonym",
                    "synonyms_path" : "synonyms.txt"
                }
            }
        }
    }
    mapping = {
        'properties': {
            'id': {
                'type': 'keyword'
            },
            'article_url': {
                'type': 'keyword'
            },
            'title': {
                'type': 'text',
                "similarity": "my_bm25",
                "analyzer": "whitespace"
            },
            'author': {
                'type': 'keyword'
            },
            'published_date': {
                'type': 'keyword'
            },
            'body': {
                'type': 'text',
                "similarity": "my_bm25",
                "analyzer": "whitespace"
            },
            'title_body': {
                'type': 'text',
                "similarity": "my_bm25",
                "analyzer": "whitespace"
            },
            'kicker': {
                'type': 'keyword'
            },
            'title_author_date': {
                'type': 'keyword'
            },
            # 'contents': {
            #     'type': 'keyword'
            # },
            'type': {
                'type': 'keyword'
            },
            'source': {
                'type': 'keyword'
            }
        }
    }
    create_index_body = {
        "settings": setting,
        "mappings": mapping
    }
    es.indices.delete(index=INDEX_NAME, ignore=[400, 404])
    es.indices.create(index=INDEX_NAME, body=create_index_body, ignore=400)
    # add all the file into elasticsearch
    process_washington_post(path_mp['DataPath'] + path_mp['WashingtonPost'])


init_es()
