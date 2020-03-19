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
INDEX_NAME = "news_wiki_entity19_stem"

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
try:
	es.indices.close(index=INDEX_NAME)
except:
	print('Index already closed.')
es.indices.put_settings(index=INDEX_NAME, body=setting)
es.indices.open(index=INDEX_NAME)

