#!/usr/bin/env python3

import os
import jieba
import re
import numpy as np
from elasticsearch import Elasticsearch
import xmlhandler as xh
from sklearn.feature_extraction.text import TfidfVectorizer

INDEX_NAME = "news_try1"
result_file = "../../wapo/WashingtonPost/data/result_files/titbody80.test"

path_mp = {}
with open(os.getcwd()+'/../path.cfg', 'r', encoding='utf-8') as f:
	for line in f:
		li = line[:-1].split('=')
		path_mp[li[0]] = li[1]

es = Elasticsearch()

topics = xh.get_topics(path_mp['DataPath'] + path_mp['topics'])
# get stop words list
stwlist = [line.strip() for line in open('stopwords.txt', encoding='utf-8').readlines()]
# doc length 595037
D = 595037
min_words = 80
num_results = 100
alpha_title = 0.7

def test_backgound_linking():
	add_score = 0.
	topic_cnt = 0.
	with open(result_file, 'w', encoding='utf-8') as f1:
		num = 1
		for mp in topics:
			# print(mp['num'].split(':')[1].strip())
			print("query docid", mp['docid'])
			num += 1
			# search by docid of the topic to get the query
			dsl = {
				'query': {
					'match': {
						'id': mp['docid']
					}
				}
			}

			# check if the docid of the topic is present in the indexed dataset
			res = es.search(index=INDEX_NAME, body=dsl)
			doc = res['hits']['hits'][0]['_source']
			dt = doc['published_date']
			docid = doc['id']
			print("found docid: ", docid)
			
			# remove stop words
			text = re.sub('[’!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~]+', '', doc['body'])
			words = "#".join(jieba.cut(text)).split('#')


			# initialize tf-idf
			q = {}
			tf = {}
			for w in words:
				if w != "" and w != ' ' and w not in stwlist:
					if w in tf:
						tf[w] += 1.0
					else:
						tf[w] = 1.0
					# calc idf of word w (how many docs it is present in)
					dsl = {
						"size": 0,
						'query': {
							'match_phrase': {
								'title_body': w
							},
						},
						"aggs": {
							"idf": {
								"terms": {
									"field": "source.keyword"
								}
							}
						}

					}
					res = es.search(index=INDEX_NAME, body=dsl)
					res = res['aggregations']['idf']['buckets']
					idf = 0.0
					for dc in res:
						idf += dc['doc_count']
					if idf > 0.0:
						q[w] = np.log(D / idf) # formula for idf
					else:
						q[w] = 0.0
			for w in q.keys():
				q[w] *= tf[w] # q now contains the tf * idf for each word
			q = sorted(q.items(), key=lambda x: x[1], reverse=True)
			query = ""
			sz = min(min_words, len(q))
			cnt = 0
			for w in q:
				if cnt >= sz:
					break
				query += ' ' + w[0]
				cnt += 1
			# query the doc
			dsl = {
				"size": num_results,
				"query": {
					'bool': {
						'must': {
							'match': {
								'title_body':{
									'query': query,
									'boost': 1
								}
							}
						},
						'should': [
							{
								'match': {
									'title_body': {
										'query': doc['title'],
										"boost": 2.34
									}
								}
							},
						],
						"must_not": {"match": {"id": docid}},
						'filter': {
							"range": {"published_date": {"lt": dt}}
						}
					},
				}
			}
			# res is the set of retrieved documents
			res = es.search(index=INDEX_NAME, body=dsl)
			res = res['hits']['hits']
			#print(res[0])
			# calculate diversity of retrieved documents 
			diversity_score = calc_diversity(res, num_results, alpha_title)
			add_score += diversity_score
			topic_cnt += 1
			# output result.test file
			print('Number of hits:', len(res))
			print('Writing to file: ', result_file)
			cnt = 1
			for ri in res:
				out = []
				out.append(mp['num'].split(':')[1].strip())
				out.append('Q0')
				out.append(ri['_source']['id'])
				out.append(str(cnt))
				out.append(str(ri['_score']))
				out.append('titbody80')
				ans = "\t".join(out) + "\n"
				f1.write(ans)
				cnt += 1				
	print(topic_cnt)
	print('diversity of all retrieved docuements for all topics: ', add_score/topic_cnt)
	return

def calc_diversity(res, num, alpha):
	t_corpus = []
	b_corpus = []
	norm_fact = (num*(num - 1))/2.0
	for i in range(len(res)):
		t_corpus.append(str(res[i]['_source']['title']))
		b_corpus.append(str(res[i]['_source']['body']))
		
	t_vect = TfidfVectorizer(min_df=1, stop_words="english")
	t_tfidf = t_vect.fit_transform(t_corpus)
	t_pairwise_similarity = t_tfidf * t_tfidf.T
	t_arr = np.array(t_pairwise_similarity.toarray())
	t_score = (t_arr.sum() - np.trace(t_arr))/2.0
	t_score = 1 - t_score/norm_fact 
	  
	b_vect = TfidfVectorizer(min_df=1, stop_words="english")
	b_tfidf = b_vect.fit_transform(b_corpus)
	b_pairwise_similarity = b_tfidf * b_tfidf.T
	b_arr = np.array(b_pairwise_similarity.toarray())
	b_score = (b_arr.sum() - np.trace(b_arr))/2.0
	b_score = 1 - b_score/norm_fact  
	
	div_score = (1 - alpha)*t_score + alpha*b_score
	#print(div_score)
	return div_score

test_backgound_linking()
