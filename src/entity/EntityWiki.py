import sys
sys.path.append("..")


import DataProcess.getCfg as cfg
import os
import json
import re
from tqdm import tqdm
from elasticsearch import Elasticsearch
from nltk.stem.porter import *
from trec_car.read_data import *

# get file path conf
path_mp = cfg.get_path_conf('../path.cfg')
es = Elasticsearch(port=7200)
stemmer = PorterStemmer()
SEARCH_NAME = "news_wiki_meta"
INDEX_NAME = "news_wiki_entity_stem"


def process_wiki(filepath):
    # load case
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
        if len(li) != 0:
            case_mp[topic_id] = li
            li = []
    # find entity wiki page
    for topic_id in case_mp:
        for entity in case_mp[topic_id][1:]:
            dsl = {
                "size": 100,
                'query': {
                    'match': {
                        'inlink': entity['link']
                    }
                }
            }
            res = es.search(index=SEARCH_NAME, body=dsl)
            print(entity['id'], len(res['hits']['hits']))
            for ri in res['hits']['hits']:
                obj = ri['_source']
                obj['inlink'] = entity['link']
                # stemming
                w_list = cfg.word_cut(obj['body'])
                for i in range(len(w_list)):
                    if w_list[i].isalpha():
                        w_list[i] = stemmer.stem(w_list[i])
                obj['body'] = ' '.join(w_list)
                doc = json.dumps(obj)
                # insert data
                res = es.index(index=INDEX_NAME, body=doc)


# put all the news into elasticsearch
def init_es():
    # create index
    setting = {
        "index": {
            "similarity": {
                "my_bm25": {
                    "type": "BM25",
                    "b": 0.95,
                    "k1": 2.1
                }
            }
        }
    }
    mapping = {
        'properties': {
            'page_name': {
                'type': 'text',
                "similarity": "my_bm25"
            },
            'body': {
                'type': 'text',
                "similarity": "my_bm25",
            },
            'inlink': {
                'type': 'text',
                "similarity": "my_bm25",
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
    process_wiki(cfg.WIKIDUMP)


init_es()
