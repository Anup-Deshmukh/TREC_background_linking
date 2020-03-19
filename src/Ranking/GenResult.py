import sys
sys.path.append("..")

import DataProcess.getCfg as cfg
import json
import re
from tqdm import tqdm

path_mp = cfg.get_path_conf('../path.cfg')


topic_mp = {}
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
			topic_mp[li[1]] = li[0]
			li = []


label = ['0', '2', '4', '8', '16']

predict = []
with open('/home/trec7/lianxiaoying/predict/test_results.tsv', 'r', encoding='utf-8') as f:
	for line in f:
		li = line[:-1].split('\t')
		max_num = 0
		max_idx = 0
		for i in range(len(li)):
			x = float(li[i])
			if x > max_num:
				max_num = x
				max_idx = i
		predict.append(label[max_idx])

with open('/home/trec7/lianxiaoying/Track_code/src/outputs/test_case.txt', 'r', encoding='utf-8') as f:
	reader = f.readlines()

cnt = 0
with open('/home/trec7/lianxiaoying/trec_eval.9.0/test/bresult.test', 'w', encoding='utf-8') as f:
	for index, line in enumerate(reader):
		split_line = line[:-1].strip().split('\t')
		if split_line[0] == '0' and len(split_line) == 5:
			out = []
			out.append(topic_mp[split_line[3]])
			out.append('Q0')
			out.append(split_line[4])
			out.append(str(0))
			out.append(predict[cnt])
			out.append('ICTNET')
			f.write("\t".join(out) + "\n")
			cnt += 1


