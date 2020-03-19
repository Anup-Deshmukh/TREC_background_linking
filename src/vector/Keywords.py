import sys
sys.path.append("..")


import DataProcess.getCfg as cfg
import os
import re
import numpy as np
from tqdm import tqdm


# get file path conf
path_mp = cfg.get_path_conf('../path.cfg')
MIN_FREQ = 5
MAX_IDF = 0.6


stop_words = {}
with open('../elastic/stopwords.txt', 'r', encoding='utf-8') as f:
	for w in f:
		w = w[:-1]
		stop_words[w] = 1
print('stop words loaded.')


idf = {}
N = 0
with open('/home/trec7/lianxiaoying/data/vector_corpus.txt', 'r', encoding='utf-8') as f:
	for line in tqdm(f):
		w_list = cfg.word_cut(line[:-1])
		tf = {}
		for w in w_list:
			w = w.strip()
			if w not in stop_words and len(w) > 2:
				if w in tf:
					tf[w] += 1
				else:
					tf[w] = 1
		for w in tf.keys():
			# appear in one doc more than MIN_FREQ
			if tf[w] >= MIN_FREQ:
				if w not in idf:
					idf[w] = 1
				else:
					idf[w] += 1
		N += 1
with open('keywords.txt', 'w', encoding='utf-8') as out:
	for w in idf.keys():
		if idf[w] * 1.0 / N < MAX_IDF:
			out.write(w + '\n')


