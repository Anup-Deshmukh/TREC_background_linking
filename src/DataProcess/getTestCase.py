import getCfg as cfg
import json
import re
from tqdm import tqdm


path_mp = cfg.get_path_conf('../path.cfg')

# path_mp['DataPath'] + path_mp['topics']
with open('D:/Download/Projects/TREC2019/WashingtonPost.v2/data/newsir18-topics.txt', 'r', encoding='utf-8') as f:
	cnt = 1
	for line in f:
		doc_id = re.search(r'<docid>.*?</docid>', line)
		if doc_id is not None:
			doc_id = doc_id.group(0)[7:-8]
			print(cnt, doc_id)
			cnt += 1

