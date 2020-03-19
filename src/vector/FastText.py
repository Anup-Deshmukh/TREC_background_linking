import sys
sys.path.append("..")


import DataProcess.getCfg as cfg
import os
import jieba
import re
import numpy as np
from tqdm import tqdm
from elasticsearch import Elasticsearch
import fasttext


# get file path conf
path_mp = cfg.get_path_conf('../path.cfg')
es = Elasticsearch(port=7200)
INDEX_NAME = "news_stem"
LAMBDA = 0.5


def cos_sim(vector_a, vector_b):
	vector_a = np.mat(vector_a)
	vector_b = np.mat(vector_b)
	num = float(vector_a * vector_b.T)
	denom = np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
	cos = num / denom
	sim = 0.5 + 0.5 * cos
	return sim


def rerank():
	case_mp = {}
	with open(path_mp['DataPath'] + path_mp['topics'], 'r', encoding='utf-8') as f:
		li = []
		for line in f:
			topic_id = re.search(r'<num>.*?</num>', line)
			if topic_id is not None:
				topic_id = topic_id.group(0)[5+9:-7]
				li.append(topic_id)
			doc_id = re.search(r'<docid>.*?</docid>', line)
			if doc_id is not None:
				doc_id = doc_id.group(0)[7:-8]
				li.append(doc_id)
			if len(li) == 2:
				case_mp[li[1]] = li[0]
				li = []
	print('test case loaded.')
	res_in = {}
	sc_map = {}
	with open('/home/trec7/lianxiaoying/trec_eval.9.0/test/elastic_bresult.test', 'r', encoding='utf-8') as f:
		for line in f:
			li = line[:-1].split('\t')
			topic_id = li[0]
			doc_id = li[2]
			if topic_id not in res_in:
				res_in[topic_id] = []
			res_in[topic_id].append(doc_id)
			sc = float(li[4])
			if topic_id not in sc_map:
				sc_map[topic_id] = {}
			sc_map[topic_id][doc_id] = sc
	print('result input loaded.')
	model = fasttext.load_model("/home/trec7/lianxiaoying/data/fasttext/wiki-news-300d-1M.vec")
	print('model loaded.')

	with open('/home/trec7/lianxiaoying/trec_eval.9.0/test/vec_bresult.test', 'w', encoding='utf-8') as f1:
		for obj_id in case_mp:
			topic_id = case_mp[obj_id]
			print(topic_id)
			dsl = {
				'query': {
					'match': {
						'id': obj_id
					}
				}
			}
			res = es.search(index=INDEX_NAME, body=dsl)
			obj_sen = res['hits']['hits'][0]['_source']['title_body']
			obj_vec = model.get_sentence_vector(obj_sen)
			# calculate max and min sc for this topic_id
			max_sc = 0
			min_sc = 1000000
			for doc_id in sc_map[topic_id].keys():
				sc = sc_map[topic_id][doc_id]
				max_sc = max(max_sc, sc)
				min_sc = min(min_sc, sc)
			cnt = 0
			for doc_id in res_in[topic_id]:
				dsl = {
					'query': {
						'match': {
							'id': doc_id
						}
					}
				}
				ri = es.search(index=INDEX_NAME, body=dsl)
				doc_sen = ri['hits']['hits'][0]['_source']['title_body']
				doc_vec = model.get_sentence_vector(doc_sen)
				sc = (1-LAMBDA) * (sc_map[topic_id][doc_id] - min_sc) / (max_sc - min_sc)\
					+ LAMBDA * cos_sim(obj_vec, doc_vec)

				out = []
				out.append(topic_id)
				out.append('Q0')
				out.append(ri['hits']['hits'][0]['_source']['id'])
				out.append(str(cnt))
				out.append(str(sc))
				out.append('ICTNET')
				ans = "\t".join(out) + "\n"
				f1.write(ans)
				cnt += 1


rerank()

