import sys
sys.path.append("..")


import DataProcess.getCfg as cfg
import json
import re
from tqdm import tqdm
import numpy as np
from stanfordcorenlp import StanfordCoreNLP


path_mp = cfg.get_path_conf('../path.cfg')


# create words inverted list
# No args
# outputs: words_index [length, doc line number]
# 		 : words_map (word, words_index line number)
def words_index(args = None):
	words = {}
	nlp = StanfordCoreNLP(cfg.STANFORDNLP)
	with open(path_mp['DataPath'] + path_mp['WashingtonPost'], 'r', encoding='utf-8') as f:
		filter_kicker = {"Opinion": 1, "Letters to the Editor": 1, "The Post's View": 1}
		cnt = 0
		for line in tqdm(f):
			obj = json.loads(line)
			contents = obj['contents']
			skip = False
			doc = ""
			for li in contents:
				if type(li).__name__ == 'dict':
					if 'type' in li and li['type'] == 'kicker':
						# skip filter kickers
						if li['content'] in filter_kicker.keys():
							skip = True
							break
					if 'subtype' in li and li['subtype'] == 'paragraph':
						paragraph = li['content'].strip()
						# Replace <.*?> with ""
						paragraph = re.sub(r'<.*?>', '', paragraph)
						doc += ' ' + paragraph
			cnt += 1
			if skip:
				continue
			# get inverted words for each doc
			doc = doc.strip()
			word_list = nlp.word_tokenize(doc)
			for w in word_list:
				if w not in words:
					words[w] = set()
				words[w].add(str(cnt))
	# output inverted list, first column is list length
	words_mp = {}
	with open(cfg.OUTPUT + 'words_index.txt', 'w', encoding='utf-8') as f:
		cnt = 1
		for key in sorted(words.keys()):
			words_mp[key] = cnt
			cnt += 1
			li = words[key]
			f.write(str(len(li)) + ' ' + ' '.join(li) + '\n')
	# output word to line map
	with open(cfg.OUTPUT + 'words_map.txt', 'w', encoding='utf-8') as f:
		f.write(json.dumps(words_mp))
	nlp.close()


# calculate tfidf for a string
# document args 1: s
# top words count args 2: num
# return: top doc line number list
def recall_by_tfidf(args = None):
	s, num, nlp = args
	num = int(num)
	# load inverted word to line map
	words_mp = {}
	with open(cfg.OUTPUT + 'words_map.txt', 'r', encoding='utf-8') as f:
		for line in f:
			words_mp = json.loads(line)
	word_list = nlp.word_tokenize(s)
	# calculate term frequency for each word in the str
	tf = {}
	for w in word_list:
		if w in tf:
			tf[w] += 1
		else:
			tf[w] = 1
	# calculate idf and tf-idf for each word
	w_list = sorted(tf)
	tfidf_mp = {}
	inv_list = {}		# words inverted list cache
	with open(cfg.OUTPUT + 'words_index.txt', 'r', encoding='utf-8') as f:
		cnt = 1			# line number
		now = 0			# current word index
		for line in f:
			# all the words for this document have calculated
			if now >= len(w_list):
				break
			w = w_list[now]
			# word not in vocabulary
			if w not in words_mp:
				continue
			# meet the right line
			if cnt == int(words_mp[w]):
				idf = np.log(cfg.DOCUMENT_COUNT * 1.0 / int(line.split(' ')[0]))
				tfidf_mp[w] = tf[w] * 1.0 * idf
				now += 1
				inv_list[w] = line.split(' ')[1:-1]
			cnt += 1
	# sort by tf-idf, combine top inverted file line number list
	tfidf_mp = sorted(tfidf_mp.items(), key=lambda d: d[1], reverse=True)
	res = set()
	for i in range(min(num, len(tfidf_mp))):
		w = tfidf_mp[i][0]
		res = res | set(inv_list[w])
	res = list(res)
	return res


# tf-idf result for each document
def tfidf_index(args = None):
	nlp = StanfordCoreNLP(cfg.STANFORDNLP)

	# read tfidf words_mp and words_idx
	words_mp = {}
	with open(cfg.OUTPUT + 'words_map.txt', 'r', encoding='utf-8') as f:
		for line in f:
			words_mp = json.loads(line)
	words_idx = []
	words_idx.append(' ')
	with open(cfg.OUTPUT + 'words_index.txt', 'r', encoding='utf-8') as f:
		for line in tqdm(f):
			words_idx.append(line)
	print('TF-IDF idx loaded.')

	with open(path_mp['DataPath'] + path_mp['WashingtonPost'], 'r', encoding='utf-8') as f:
		with open(cfg.OUTPUT + 'tfidf_index.txt', 'w', encoding='utf-8') as out:
			for line in tqdm(f):
				obj = json.loads(line)
				contents = obj['contents']
				body = ""
				for li in contents:
					if type(li).__name__ == 'dict':
						if 'subtype' in li and li['subtype'] == 'paragraph':
							paragraph = li['content'].strip()
							# Replace <.*?> with ""
							paragraph = re.sub(r'<.*?>', '', paragraph)
							body += ' ' + paragraph
				res_tfidf = cal_tfidf_fast([body, '20', nlp, words_mp, words_idx])
				out.write(' '.join(res_tfidf) + '\n')
	nlp.close()


# read words_mp and words_idx into memory first(idx start from 1)
def cal_tfidf_fast(args = None):
	s, num, nlp, words_mp, words_idx = args
	num = int(num)
	word_list = nlp.word_tokenize(s)
	# calculate term frequency for each word in the str
	tf = {}
	for w in word_list:
		if w in tf:
			tf[w] += 1
		else:
			tf[w] = 1
	# calculate idf and tf-idf for each word
	w_list = sorted(tf)
	tfidf_mp = {}
	inv_list = {}		# words inverted list cache
	for w in w_list:
		# word not in vocabulary
		if w not in words_mp:
			continue
		# meet the right line
		cnt = int(words_mp[w])
		line = words_idx[cnt]
		idf = np.log(cfg.DOCUMENT_COUNT * 1.0 / int(line.split(' ')[0]))
		tfidf_mp[w] = tf[w] * 1.0 * idf
		inv_list[w] = line.split(' ')[1:-1]
	# sort by tf-idf, combine top inverted file line number list
	tfidf_mp = sorted(tfidf_mp.items(), key=lambda d: d[1], reverse=True)
	res = set()
	for i in range(min(num, len(tfidf_mp))):
		w = tfidf_mp[i][0]
		res = res | set(inv_list[w])
	res = list(res)
	return res


if __name__ == "__main__":
	getattr(__import__('TFIDF'), sys.argv[1])(sys.argv[2:])

