import sys
sys.path.append("..")


import DataProcess.getCfg as cfg
import json
import re
from tqdm import tqdm
import numpy as np


path_mp = cfg.get_path_conf('../path.cfg')


# create inverted list for topis
# No args
# output: (topic, [doc line numbers])
def topics_index(args = None):
	topics = {}
	with open(path_mp['DataPath'] + path_mp['WashingtonPost'], 'r', encoding='utf-8') as f:
		cnt = 1
		for line in tqdm(f):
			obj = json.loads(line)
			contents = obj['contents']
			for li in contents:
				if type(li).__name__ == 'dict':
					if 'type' in li and li['type'] == 'kicker':
						key = li['content']
						if key in topics:
							topics[key].append(cnt)
						else:
							topics[key] = []
							topics[key].append(cnt)
			cnt += 1
	with open(cfg.OUTPUT + 'topics_index.txt', 'w', encoding='utf-8') as f:
		f.write(json.dumps(topics))


# return documents list by topics
# args 1: topics
def recall_by_topics(args = None):
	key = args[0]
	with open(cfg.OUTPUT + 'topics_index.txt', 'r', encoding='utf-8') as f:
		mp = {}
		for line in f:
			mp = json.loads(line)
		return mp[key]


if __name__ == "__main__":
	getattr(__import__('Topics'), sys.argv[1])(sys.argv[2:])



