import os
from itertools import islice
import json
import re

# get conf file path
path_mp = {}
with open(os.getcwd()+'/../../path.cfg', 'r', encoding='utf-8') as f:
    for line in f:
        li = line[:-1].split('=')
        path_mp[li[0]] = li[1]

# check data format
with open(path_mp['DataPath'] + path_mp['WashingtonPost'], 'r', encoding='utf-8') as f:
    for line in islice(f, 30831, None):
        obj = json.loads(line)
        # for key in obj.keys():
        #     print(key, ':', obj[key])
        # print()
        contents = obj['contents']
        text = ""
        print(len(contents))
        cnt = 0
        for li in contents:
            print(cnt, li)
            cnt += 1
            if type(li).__name__ == 'dict' and li['type'] == 'sanitized_html':
                content = li['content']
                # remove html tags, lowercase
                content = re.sub(r'<.*?>', '', content)
                text += content.lower()
        obj['text'] = text
        del obj['contents']
        doc = json.dumps(obj)

