import sys
sys.path.append("..")


import DataProcess.getCfg as cfg
import json
import re
from tqdm import tqdm
import random
import numpy as np
from pyspark import SparkContext, SparkConf
import bm25
from stanfordcorenlp import StanfordCoreNLP


path_mp = cfg.get_path_conf('../path.cfg')
nlp = StanfordCoreNLP('http://localhost', port=7000)


def get_mapping(args=None):
	SparkContext.getOrCreate().stop()
	conf = SparkConf().setMaster("local[*]").setAppName("bm25") \
		.set("spark.executor.memory", "10g") \
		.set("spark.driver.maxResultSize", "10g") \
		.set("spark.cores.max", 10) \
		.set("spark.executor.cores", 10) \
		.set("spark.default.parallelism", 20)
	sc = SparkContext(conf=conf)
	# words df
	words_df = sc.textFile(cfg.OUTPUT + 'words_index.txt') \
		.filter(lambda line: line != '') \
		.map(lambda line: (line.split(' ')[0], len(line.split(' ')[1:]))) \
		.collectAsMap()
	words_df = sc.broadcast(words_df)
	print('words_df loaded.')
	# avgdl
	avgdl = sc.textFile(path_mp['DataPath'] + path_mp['WashingtonPost']) \
		.map(lambda line: bm25.calc_doc_length(line)).sum()
	avgdl = avgdl * 1.0 / 595037
	print('avgdl loaded.')
	# WashingtonPost
	WashingtonPost = sc.textFile(path_mp['DataPath'] + path_mp['WashingtonPost']) \
		.map(lambda line: bm25.return_doc(line)).collectAsMap()
	print('WashingtonPost loaded.')
	# test case: doc_id, topic_id
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
	# answer: topic_id, (doc_id, rel)
	ans_mp = {}
	with open(path_mp['DataPath'] + path_mp['bqrels'], 'r', encoding='utf-8') as f:
		for line in f:
			li = line[:-1].split(' ')
			topic_id = li[0]
			doc_id = li[2]
			if topic_id not in ans_mp:
				ans_mp[topic_id] = []
			ans_mp[topic_id].append([doc_id, li[3]])
	print('bqrel loaded.')
	# generate relevance map
	rel_mp = {}
	for cur_id in case_mp.keys():
		obj = WashingtonPost[cur_id]
		topic_id = case_mp[cur_id]
		body = bm25.extract_body([obj['contents']])
		# query (modify)
		tmp = nlp.ner(obj['title'] + ' ' + body)
		query = []
		for w, nn in tmp:
			if nn != 'O':
				query.append(w)
		rel_mp[topic_id] = []
		for doc_id, rel in ans_mp[topic_id]:
			score = bm25.calc_score(WashingtonPost[doc_id], words_df, query, avgdl, True)
			rel_mp[topic_id].append([score, rel])
	with open(cfg.OUTPUT + 'rel_mp.txt', 'w', encoding='utf-8') as f:
		f.write(json.dumps(rel_mp))


# modify bm25 score in col4 to rel
def transform(args=None):
	score2rel = {
		321: { 0: 58.72430022331213, 2: 57.806902160130576, 4: 52.42887915317125, 8: 57.74074158269595},
		336: { 0: 41.43326593391888, 2: 27.185608260012476, 4: 50.175585642250574, 8: 150.17558564225058},
		341: { 0: 196.809155381055, 2: 235.93497363971383, 4: 337.0338518528704, 8: 326.3167258535053},
		347: { 0: 61.131059550066944, 2: 22.365119967344796, 4: 70.23342739428186, 8: 53.66974906538185},
		350: { 0: 42.363541188083616, 2: 28.974780943825614, 4: 128.9747809438256, 8: 228.9747809438256},
		362: { 0: 53.57301621718483, 2: 86.09751445959351, 4: 134.8830366830545, 8: 132.8467762715161},
		363: { 0: 200.9079189769455, 2: 165.25576162503592, 4: 186.4617485420089, 8: 218.65479306718942},
		367: { 0: 103.79541698553251, 2: 203.7954169855325, 4: 303.7954169855325, 8: 403.7954169855325},
		375: { 0: 152.27557899060835, 2: 237.79469747911173, 4: 112.6560126155415, 8: 362.8226977450113},
		378: { 0: 432.6029393473918, 2: 571.9040526280181, 4: 593.6095532325874, 8: 689.6837909059575},
		393: { 0: 323.2818006770586, 2: 135.4852865362941, 4: 427.91371548958534, 8: 452.90955885344454},
		397: { 0: 81.79056507884778, 2: 150.41680746532845, 4: 200.31938029066316, 8: 207.53578384807767},
		400: { 0: 313.7599912921198, 2: 435.6144292516918, 4: 312.3079722896437, 8: 275.87492813240726},
		408: { 0: 94.97544672331911, 2: 141.86706198013798, 4: 149.73214999936997, 8: 143.3714643735981},
		414: { 0: 959.4636253646839, 2: 1139.0043408749552, 4: 1116.7193050056164, 8: 1337.4526479971005},
		422: { 0: 77.09443211983637, 2: 126.62725632846761, 4: 142.46487849053196, 8: 242.46487849053196},
		426: { 0: 32.736241768252455, 2: 28.716751527399467, 4: 33.52177016985936, 8: 35.47489265511767},
		427: { 0: 13.92547646521178, 2: 17.649533833222666, 4: 117.64953383322266, 8: 19.07694844150749},
		433: { 0: 32.7655611253469, 2: 80.4839208702713, 4: 180.4839208702713, 8: 280.4839208702713},
		439: { 0: 26.62032646198832, 2: 51.032832302922564, 4: 67.98481261929192, 8: 92.55389917083852},
		442: { 0: 48.30587491911558, 2: 385.5817010664017, 4: 368.78251657400597, 8: 307.839542815939},
		445: { 0: 43.678735598011194, 2: 44.17230591671435, 4: 9.845207222426046, 8: 136.45140625472175},
		626: { 0: 93.62755278014345, 2: 155.6799006539045, 4: 255.6799006539045, 8: 355.6799006539045},
		646: { 0: 102.02190444521304, 2: 97.11747798430899, 4: 96.20543199477098, 8: 133.19403515518084},
		690: { 0: 166.7070999258524, 2: 202.76010385782527, 4: 222.64157973118336, 8: 206.0213208974926},
		801: { 0: 144.84739857977843, 2: 159.53571468731468, 4: 148.8026113685882, 8: 248.8026113685882},
		802: { 0: 538.3024335476871, 2: 523.877217056287, 4: 515.0974254350103, 8: 418.19529134839655},
		803: { 0: 182.83832287975537, 2: 195.36152001289702, 4: 206.18810329959683, 8: 306.18810329959683},
		804: { 0: 276.75680900954865, 2: 303.06371545991703, 4: 344.9771600351888, 8: 444.9771600351888},
		805: { 0: 125.97287376853438, 2: 118.96782455908634, 4: 163.85288961333077, 8: 194.31504300953233},
		806: { 0: 10.789025140488453, 2: 4.473457396001118, 4: 7.480731225333054, 8: 107.48073122533306},
		807: { 0: 581.4618128128214, 2: 664.4219751513514, 4: 764.4219751513514, 8: 864.4219751513514},
		808: { 0: 336.5468711807911, 2: 442.158020903444, 4: 445.90124589359624, 8: 34.122528597992165},
		809: { 0: 161.43678874644095, 2: 379.7676482933797, 4: 269.9380241650345, 8: 369.9380241650345},
		810: { 0: 61.64603617942636, 2: 78.36515941470918, 4: 96.28323696310517, 8: 65.75863418526386},
		811: { 0: 101.415589248826, 2: 94.91624054824744, 4: 84.7946269109678, 8: 285.92559049615295},
		812: { 0: 83.69590584308445, 2: 57.429063301771116, 4: 89.94096711316989, 8: 64.51852369618118},
		813: { 0: 29.934968207599532, 2: 15.219113624808006, 4: 18.631854439373488, 8: 33.18974187998908},
		814: { 0: 102.10859181240667, 2: 98.29728259653756, 4: 108.278662711536, 8: 98.88422452248157},
		815: { 0: 907.5453285828931, 2: 1072.0283909951272, 4: 987.5988425139852, 8: 1087.5988425139853},
		816: { 0: 55.713808642054545, 2: 53.4495625358998, 4: 66.68100240373332, 8: 68.84235169654785},
		817: { 0: 110.57844988799829, 2: 87.81629993088524, 4: 187.81629993088524, 8: 287.81629993088524},
		818: { 0: 34.70651818533792, 2: 32.25579148216741, 4: 63.6643826672487, 8: 44.43606917873597},
		819: { 0: 51.67123560801849, 2: 41.04743205430557, 4: 31.489606709360643, 8: 8.065028979120006},
		820: { 0: 156.41195658041454, 2: 178.57308555811528, 4: 171.95232868362882, 8: 271.9523286836288},
		821: { 0: 30.574427209284142, 2: 25.15839923712893, 4: 25.26372308163213, 8: 13.478462491955824},
		822: { 0: 240.52537276289323, 2: 290.4659941381753, 4: 323.82835348421105, 8: 317.17701280341794},
		823: { 0: 58.58014991269853, 2: 81.206832550841, 4: 61.72876272427533, 8: 35.833283740623386},
		824: { 0: 448.72863010675036, 2: 549.0479888048068, 4: 515.2541190496644, 8: 615.2541190496644},
		825: { 0: 708.8622441163649, 2: 1026.833151315723, 4: 1447.2217555840325, 8: 1560.285264769665}
	}
	with open('/home/trec7/lianxiaoying/trec_eval.9.0/test/bresult.test', 'r', encoding='utf-8') as f:
		with open('/home/trec7/lianxiaoying/trec_eval.9.0/test/bresult.test1', 'w', encoding='utf-8') as out:
			for line in f:
				li = line[:].split('\t')
				topic_id = li[0]
				score = float(li[4])
				rel = 16
				if score <= score2rel[int(topic_id)][0]:
					rel = 0
				elif score <= score2rel[int(topic_id)][2]:
					rel = 2
				elif score <= score2rel[int(topic_id)][4]:
					rel = 4
				elif score <= score2rel[int(topic_id)][8]:
					rel = 8
				li[4] = str(rel)
				out.write('\t'.join(li))


def clip_rel(args=None):
	# 0:2:4:8:16 = 16:8:4:2:1
	up = [1, 3, 7, 15, 31]
	dw = 31
	relevance = [16, 8, 4, 2, 0]
	topic_num = {}
	with open('/home/trec7/lianxiaoying/trec_eval.9.0/test/bresult.test', 'r', encoding='utf-8') as f:
		for line in f:
			li = line[:].split('\t')
			topic_id = li[0]
			if topic_id in topic_num:
				topic_num[topic_id] += 1
			else:
				topic_num[topic_id] = 1
	with open('/home/trec7/lianxiaoying/trec_eval.9.0/test/bresult.test', 'r', encoding='utf-8') as f:
		with open('/home/trec7/lianxiaoying/trec_eval.9.0/test/bresult.test1', 'w', encoding='utf-8') as out:
			cnt = 0
			now = 0
			topic_id = ''
			for line in f:
				li = line[:].split('\t')
				if li[0] != topic_id:
					now = 0
					cnt = 0
				topic_id = li[0]
				rel = relevance[now]
				tot = topic_num[topic_id] * up[now]/dw
				if cnt < tot:
					cnt += 1
				else:
					now = now + 1
				li[4] = str(rel)
				out.write('\t'.join(li))


if __name__ == "__main__":
	getattr(__import__('Score2Rel'), sys.argv[1])(sys.argv[2:])

