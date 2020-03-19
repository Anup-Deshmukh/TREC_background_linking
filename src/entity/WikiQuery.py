import sys
sys.path.append("..")


import DataProcess.getCfg as cfg
import os
import jieba
import re
import numpy as np
from tqdm import tqdm
from elasticsearch import Elasticsearch
from stanfordcorenlp import StanfordCoreNLP
import json
from nltk.stem.porter import *


# get file path conf
path_mp = cfg.get_path_conf('../path.cfg')
es = Elasticsearch(port=7200)
nlp = StanfordCoreNLP('http://localhost', port=7100)
stemmer = PorterStemmer()
INDEX_NAME = "news_alpha"
WIKI_INDEX = "news_wiki_para"


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


def process(obj):
    obj['body'] = extract_body([obj['contents']])

    # to lower case
    obj['title'] = str(obj['title']).lower()
    obj['body'] = str(obj['body']).lower()

    # stemming
    # w_list = cfg.word_cut(obj['body'])
    # for i in range(len(w_list)):
    #     if w_list[i].isalpha():
    #         w_list[i] = stemmer.stem(w_list[i])
    # obj['body'] = ' '.join(w_list)
    # w_list = cfg.word_cut(obj['title'])
    # for i in range(len(w_list)):
    #     if w_list[i].isalpha():
    #         w_list[i] = stemmer.stem(w_list[i])
    # obj['title'] = ' '.join(w_list)

    del obj['contents']
    obj['title_body'] = (str(obj['title']) + ' ' + str(obj['body'])).lower()
    obj['title_author_date'] = (str(obj['title']) + ' ' + str(obj['author']) + ' ' + str(obj['published_date'])).lower()
    return obj


def test_entity_ranking():
    # stop words
    # stop_words = {}
    # with open('../elastic/stopwords.txt', 'r', encoding='utf-8') as f:
    #     for w in f:
    #         w = w[:-1]
    #         stop_words[w] = 1
    # print('stop words loaded.')
    # test case: topic_id, list:[docid, entity_id]
    case_mp = {}
    with open(path_mp['DataPath'] + path_mp['entities'], 'r', encoding='utf-8') as f:
        li = []
        mp = {}
        topic_id = ''
        for line in f:
            topic_id_tmp = re.search(r'<num>.*?</num>', line)
            if topic_id_tmp is not None:
                if len(li) > 0:
                    case_mp[topic_id] = li
                    li = []
                topic_id = topic_id_tmp
                topic_id = topic_id.group(0)[5+9:-7]
            doc_id = re.search(r'<docid>.*?</docid>', line)
            if doc_id is not None:
                doc_id = doc_id.group(0)[7:-8]
                li.append(doc_id)
            entity_id = re.search(r'<id>.*?</id>', line)
            if entity_id is not None:
                entity_id = entity_id.group(0)[5:-6]
                mp['id'] = entity_id
            mention = re.search(r'<mention>.*?</mention>', line)
            if mention is not None:
                mention = mention.group(0)[9:-10]
                mp['mention'] = mention.lower()
            link = re.search(r'<link>.*?</link>', line)
            if link is not None:
                link = link.group(0)[6:-7]
                mp['link'] = link.lower()
                li.append(mp)
                mp = {}
    print('test case loaded.')
    with open('/home/trec7/lianxiaoying/trec_eval.9.0/test/eresult.test', 'w', encoding='utf-8') as f:
        for topic_id in case_mp.keys():
            li = case_mp[topic_id]
            doc_id = li[0]
            out_doc_id = {'97b489e2-0a38-11e5-9e39-0db921c47b93':1}
            doc = ''
            if doc_id not in out_doc_id:
                dsl = {
                    'query': {
                        'match': {
                            'id': doc_id
                        }
                    }
                }
                res = es.search(index=INDEX_NAME, body=dsl)
                # print(res)
                doc = res['hits']['hits'][0]['_source']
            else:
                with open(doc_id + '.txt', 'r', encoding='utf-8') as rin:
                    for line in rin:
                        doc = json.loads(line)
                doc = process(doc)
            # tmp1 = cfg.word_cut(doc['title_body'])
            # tmp = []
            # for w in tmp1:
            #     if w not in stop_words:
            #         tmp.append(w)
            # qr = ' '.join(tmp)
            qr = doc['title_body']
            cnt = 1
            for entity in li[1:]:
                dsl = {
                    "size": 100,
                    "timeout": "1m",
                    "query": {
                        'bool': {
                            'must': {
                                'match': {
                                    'body': {
                                        'query': qr,
                                        'boost': 1
                                    }
                                }
                            },
                            'must': {
                                'match': {
                                    'body': {
                                        'query': entity['mention'],
                                        'boost': 1
                                    }
                                }
                            }
                        }
                    }
                }
                res = es.search(index=WIKI_INDEX, body=dsl, request_timeout=30)
                res = res['hits']['hits']

                print(entity['id'], len(res))
                out = []
                out.append(topic_id)
                out.append('Q0')
                out.append(entity['id'])
                out.append(str(cnt))
                if len(res) > 0:
                    score = res[0]['_score']
                    out.append(str(score))
                else:
                    out.append(str(0))
                out.append('ICTNET')
                ans = "\t".join(out) + "\n"
                f.write(ans)
                cnt += 1


test_entity_ranking()
