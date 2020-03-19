import sys
sys.path.append("..")


import DataProcess.getCfg as cfg
import json
import re
from tqdm import tqdm
import random
import numpy as np


path_mp = cfg.get_path_conf('../path.cfg')


# extract body from give Washington Post json
# args 0: json contents
# retrun: body string
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


# split max_length string from body
# args 0: string
# return: string
def split_body(args=None):
	body, max_length = args
	max_length = int(max_length)
	w_list = cfg.word_cut(body)
	if len(w_list) <= max_length-2:
		return body
	head_len = int((max_length - 2) / 2)
	tail_len = int(max_length - 2 - head_len)
	return ' '.join(w_list[:head_len]) + ' '.join(w_list[-tail_len:])


def filter_doc(doc, date, similar_doc):
	doc_title = doc['title']
	doc_author = doc['author']
	doc_date = doc['published_date']
	# Filter by date
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


# generate samples for each document
# args 0: max_length for Bert
def gen_sample(args=None):
	max_length = args[0]
	max_length = int(max_length)
	# read all the doc, load as json, line count start from 1
	WashingtonPost = {}
	with open(path_mp['DataPath'] + path_mp['WashingtonPost'], 'r', encoding='utf-8') as f:
		for line in tqdm(f):
			obj = json.loads(line)
			doc_id = obj['id']
			WashingtonPost[doc_id] = obj
	print('WashingtonPost dataset loaded.')
	# read topics idx
	topics_mp = {}
	with open(cfg.OUTPUT + 'topics_index.txt', 'r', encoding='utf-8') as f:
		for line in tqdm(f):
			li = line[:-1].split(' ')
			topics_mp[li[0]] = set(li[1:])
	print('Topics idx loaded.')
	# read tfidf_mp
	tfidf_mp = {}
	with open(cfg.OUTPUT + 'tfidf_index.txt', 'r', encoding='utf-8') as f:
		for line in tqdm(f):
			li = line[:-1].split(' ')
			tfidf_mp[li[0]] = li[1:]
	tfidf_list = list(tfidf_mp.keys())
	print('TFIDF idx loaded.')
	# read words_mp
	words_index = {}
	with open(cfg.OUTPUT + 'words_index.txt', 'r', encoding='utf-8') as f:
		for line in tqdm(f):
			li = line[:-1].split(' ')
			words_index[li[0]] = set(li[1:])
	print('Words idx loaded.')
	# read test case
	test_case = []
	with open(path_mp['DataPath'] + path_mp['topics'], 'r', encoding='utf-8') as f:
		for line in f:
			doc_id = re.search(r'<docid>.*?</docid>', line)
			if doc_id is not None:
				doc_id = doc_id.group(0)[7:-8]
				test_case.append(doc_id)
	print('Test case loaded.')
	with open(cfg.OUTPUT + 'test_case.txt', 'w', encoding='utf-8') as out:
		for cur_id in tqdm(test_case):
			obj = WashingtonPost[cur_id]
			contents = obj['contents']
			title = obj['title']
			author = obj['author']
			date = obj['published_date']
			body = ""
			topic_name = ""
			for li in contents:
				if type(li).__name__ == 'dict':
					if 'type' in li and li['type'] == 'kicker' and topic_name != "":
						topic_name = li['content'].strip()
					if 'subtype' in li and li['subtype'] == 'paragraph':
						paragraph = li['content'].strip()
						# Replace <.*?> with ""
						paragraph = re.sub(r'<.*?>', '', paragraph)
						body += ' ' + paragraph
			# Recall By tf_idf
			body = body.strip()
			res_tfidf = set()
			for w in tfidf_mp[cur_id]:
				res_tfidf = res_tfidf | words_index[w]
			res_tfidf = list(res_tfidf)

			# Recall By topics
			res_topic = []
			if topic_name in res_topic:
				res_topic = list(topics_mp[topic_name])

			# Combie Recall results
			similar_doc = {} # Filter
			cur_key = ''
			if title is not None:
				cur_key += title
			if author is not None:
				cur_key += '#' + author
			if date is None:
				cur_key += '#' + str(date)
			similar_doc[cur_key] = 1
			res_combine = set()
			for li in res_tfidf:
				# Filter by kicker
				if li in tfidf_mp and filter_doc(WashingtonPost[li], date, similar_doc):
					res_combine.add(li)
			for li in res_topic:
				# Filter by kicker
				if li in tfidf_mp and filter_doc(WashingtonPost[li], date, similar_doc):
					res_combine.add(li)
			res_combine = list(res_combine)[:1000]

			# Generate test case
			sen1 = split_body([body, max_length])
			for doc_id in res_combine:
				doc_body = extract_body([WashingtonPost[doc_id]['contents']])
				sen2 = split_body([doc_body, max_length])
				out.write(str(0) + '\t' + sen1 + '\t' + sen2 + '\t' + cur_id + '\t' + doc_id + '\n')


if __name__ == "__main__":
	getattr(__import__('GenBertCls_testcase'), sys.argv[1])(sys.argv[2:])


