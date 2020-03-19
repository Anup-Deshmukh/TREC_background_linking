import sys
sys.path.append("..")


import DataProcess.getCfg as cfg
import json
import re
from tqdm import tqdm
import random
import numpy as np
from pyspark import SparkContext, SparkConf
from stanfordcorenlp import StanfordCoreNLP


path_mp = cfg.get_path_conf('../path.cfg')
#nlp = StanfordCoreNLP('http://localhost', port=7000)


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


def filter_doc(doc, date, similar_doc):
	# Filter by kicker
	filter_kicker = {"Opinion": 1, "Letters to the Editor": 1, "The Post's View": 1}
	for li in doc['contents']:
		if type(li).__name__ == 'dict':
			if 'type' in li and li['type'] == 'kicker':
				# skip filter kickers
				topic_name = li['content']
				if topic_name in filter_kicker.keys():
					return False
	# Filter by date
	doc_title = doc['title']
	doc_author = doc['author']
	doc_date = doc['published_date']
	if doc_date is not None and date is not None and int(doc_date) > int(date):
		return False
	# Filter by date + title + author
	rep_key = ''
	if doc_title is not None:
		rep_key += doc_title
	if doc_author is not None:
		rep_key += '#' + doc_author
	if doc_date is not None:
		rep_key += '#' + str(doc_date)
	if rep_key in similar_doc:
		return False
	similar_doc[rep_key] = 1
	return True


def calc_doc_length(line):
	obj = json.loads(line)
	body = extract_body([obj['contents']])
	w_list = cfg.word_cut(body)
	return len(w_list)


def return_doc(line):
	obj = json.loads(line)
	doc_id = obj['id']
	return (doc_id, obj)


def calc_score(line, words_df, query, avgdl, flag=False):
	k1 = 1.5
	b = 0.75
	obj = line
	if not flag:
		obj = json.loads(line)
	body = extract_body([obj['contents']])
	doc_id = obj['id']
	w_list = cfg.word_cut(body)
	# calc tf for the doc
	tf = {}
	for w in w_list:
		if w in tf:
			tf[w] += 1
		else:
			tf[w] = 1
	# calc bm25 for the doc
	score = 0.0
	for w in query:
		tfi = 0
		if w in tf:
			tfi = tf[w]
		dfi = 1e-7
		if w in words_df.value:
			dfi = words_df.value[w]
		dl = len(w_list)
		N = cfg.DOCUMENT_COUNT
		score += np.log(N / dfi) * ((k1 + 1) * tfi) / (k1 * ((1 - b) + b * dl / avgdl) + tfi)
	return (score, doc_id)


# words_df: document frequency for each word
# WashingtonPost: corpus
def bm25(sc, query, words_df, avgdl):
	res = sc.textFile(path_mp['DataPath'] + path_mp['WashingtonPost']) \
		.map(lambda line: calc_score(line, words_df, query, avgdl))\
		.sortByKey(False).collect()
	return res[:1000]


def gen_res(args = None):
	SparkContext.getOrCreate().stop()
	conf = SparkConf().setMaster("local[*]").setAppName("bm25") \
		.set("spark.executor.memory", "10g") \
		.set("spark.driver.maxResultSize", "10g") \
		.set("spark.cores.max", 10) \
		.set("spark.executor.cores", 10) \
		.set("spark.default.parallelism", 20)
	sc = SparkContext(conf=conf)
	# stop words
	stop_words = {}
	with open('../elastic/stopwords.txt', 'r', encoding='utf-8') as f:
		for w in f:
			w = w[:-1]
			stop_words[w] = 1
	print('stop words loaded.')
	# words df
	words_df = sc.textFile(cfg.OUTPUT + 'words_index.txt') \
		.filter(lambda line: line != '') \
		.map(lambda line: (str(line.split(' ')[0]).lower(), len(line.split(' ')[1:]))) \
		.collectAsMap()
	words_df = sc.broadcast(words_df)
	print('words_df loaded.')
	# avgdl
	avgdl = sc.textFile(path_mp['DataPath'] + path_mp['WashingtonPost']) \
		.map(lambda line: calc_doc_length(line)).sum()
	avgdl = avgdl * 1.0 / 595037
	print('avgdl loaded.')
	# WashingtonPost
	WashingtonPost = sc.textFile(path_mp['DataPath'] + path_mp['WashingtonPost']) \
		.map(lambda line: return_doc(line)).collectAsMap()
	print('WashingtonPost loaded.')
	# test case
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
	# filter and generate result
	with open('/home/trec7/lianxiaoying/trec_eval.9.0/test/bresult.test', 'w', encoding='utf-8') as f:
		for cur_id in case_mp.keys():
			topic_id = case_mp[cur_id]
			print('now is processing:', topic_id)
			obj = WashingtonPost[cur_id]
			body = extract_body([obj['contents']])
			# query (modify)
			tmp1 = cfg.word_cut(str(obj['title'] + ' ' + body).lower())
			tmp = []
			for w in tmp1:
				if w not in stop_words:
					tmp.append(w)
			query = tmp
			if len(tmp) > 768:
				query = tmp[:512] + tmp[-256:]
			res = bm25(sc, query, words_df, avgdl)
			# filter
			title = obj['title']
			author = obj['author']
			date = obj['published_date']
			similar_doc = {}
			cur_key = ''
			if title is not None:
				cur_key += title
			if author is not None:
				cur_key += '#' + author
			if date is None:
				cur_key += '#' + str(date)
			similar_doc[cur_key] = 1
			for score, doc_id in res:
				doc = WashingtonPost[doc_id]
				if filter_doc(doc, date, similar_doc):
					out = []
					out.append(topic_id)
					out.append('Q0')
					out.append(doc_id)
					out.append(str(0))
					out.append(str(score))
					out.append('ICTNET')
					f.write("\t".join(out) + "\n")


if __name__ == "__main__":
	getattr(__import__('bm25'), sys.argv[1])(sys.argv[2:])

