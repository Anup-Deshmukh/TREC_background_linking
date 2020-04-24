#!/usr/bin/env python3

import os
import jieba
import re
import numpy as np
from elasticsearch import Elasticsearch
import xmlhandler as xh
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from rake_nltk import Rake
import math
#import nltk
#from nltk.corpus import stopwords
#nltk.download('stopwords')
#from nltk.tokenize import word_tokenize

INDEX_NAME = "news_try1"
result_file = "../../wapo/WashingtonPost/data/result_files/IND_UW_A8.test"

path_mp = {}
with open(os.getcwd()+'/../path.cfg', 'r', encoding='utf-8') as f:
	for line in f:
		li = line[:-1].split('=')
		path_mp[li[0]] = li[1]

# init bert finetuned model
model = SentenceTransformer('bert-base-nli-mean-tokens')

# accessing BM 25 index
es = Elasticsearch()
topics = xh.get_topics(path_mp['DataPath'] + path_mp['topics'])
# get stop words list
stwlist = [line.strip() for line in open('stopwords.txt', encoding='utf-8').readlines()]

# init parameters
D = 571963
min_words = 80
minw_bert = 100
num_res_bm25 = 100
num_res_bert = 100
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
				"size": num_res_bm25,
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
			res_bm25 = es.search(index=INDEX_NAME, body=dsl)
			res_bm25 = res_bm25['hits']['hits']
			
			# refine bm25 results with bert
			#res_bert_bm = filter_bert(res_bm25, query, minw_bert, num_res_bm25, num_res_bert)

			# calculate diversity of retrieved documents 
			diversity_score = calc_diversity(res_bm25, num_res_bm25, alpha_title)
			add_score += diversity_score
			topic_cnt += 1
			
			# output result.test file
			print('Number of hits:', len(res_bm25))
			print('Writing to file: ', result_file)
			cnt = 1
			for ri in res_bm25:
				out = []
				out.append(mp['num'].split(':')[1].strip())
				out.append('Q0')
				out.append(ri['_source']['id'])
				out.append(str(cnt))
				out.append(str(ri['_score']))
				out.append('IND_UW_A8')
				ans = "\t".join(out) + "\n"
				f1.write(ans)
				cnt += 1				
	#print(topic_cnt)
	print('diversity of all retrieved docuements for all topics: ', add_score/topic_cnt)
	return


def extract_key(text, w, r):
	
	r.extract_keywords_from_text(text) 
	a = r.get_ranked_phrases()
	t = ""
	cut = min(w, len(a))
	count = 0
	for phrase in a:
		if count >= cut:
			break
		t = t + ' ' + phrase
		count += 1
	return t	

def scoring_bert(e1, e2):
	
	cosine = np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2))
	score = 1./(1 + math.exp(-100*(cosine - 0.95)))
	#print(score)
	return score

def filter_bert(res, query, w, num, num_bert):
	
	r = Rake()
	text_corpus = []
	score_arr = []
	query = str(query)
	query_corpus = []
	query_corpus.append(query)
	res_new = []

	for i in range(len(res)):
		
		text = str(res[i]['_source']['title_body'])
		# remove stop words
		#text_tokens = word_tokenize(text)
		#tokens_without_sw = [word for word in text_tokens if not word in stopwords.words()]
		#text = (" ").join(tokens_without_sw)
		key_text = extract_key(text, w, r)
		text_corpus.append(key_text)

	text_emb = np.array(model.encode(text_corpus))
	query_emb = np.array(model.encode(query_corpus))
	query_emb = query_emb[0]

	#print("text emb size: ", text_emb.shape)
	#print("query emb size: ", query_emb.shape)

	#for t, emb in zip(text_corpus, text_emb):
	for emb in text_emb:	
		score = scoring_bert(query_emb, emb)
		score_arr.append(score)

	score_arr = np.array(score_arr)
	max_ind = score_arr.argsort()[-num_bert:][::-1]
	for i in max_ind:
		res_new.append(res[i])

	return res_new

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
