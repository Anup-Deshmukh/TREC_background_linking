import getCfg as cfg
import json
import re
from tqdm import tqdm
import numpy as np


path_mp = cfg.get_path_conf('../path.cfg')

with open(path_mp['DataPath'] + path_mp['WashingtonPost'], 'r', encoding='utf-8') as f:
	cnt = 0
	for line in tqdm(f):
		obj = json.loads(line)
		title = obj['title']
		author = obj['author']
		date = obj['published_date']
		cnt += 1
		try:
			date = int(date)
		except:
			print(cnt, date)

