import sys
sys.path.append("..")


import DataProcess.getCfg as cfg
import os
import json
import re
from tqdm import tqdm
from elasticsearch import Elasticsearch

# get file path conf
path_mp = cfg.get_path_conf('../path.cfg')
es = Elasticsearch(port=7200)
INDEX_NAME = "news_stem"


def gen_train_corpus():
	dsl = {
		'query': {
			'match_all': {}
		}
	}
	page = es.search(index=INDEX_NAME, size=10000, scroll='2m', body=dsl)
	sid = page['_scroll_id']
	scroll_size = int(page['_shards']['total'])
	tot = 10000
	# Start scrolling
	with open('/home/trec7/lianxiaoying/data/vector_corpus.txt', 'w', encoding='utf-8') as out:
		while scroll_size > 0:
			print(tot)
			page = es.scroll(scroll_id=sid, scroll='2m')
			# Update the scroll ID
			sid = page['_scroll_id']
			# Get the number of results that we returned in the last scroll
			scroll_size = len(page['hits']['hits'])
			tot += scroll_size
			# generate corpus
			for doc in page['hits']['hits']:
				doc = doc['_source']['title_body']
				out.write(doc + '\n')


gen_train_corpus()



