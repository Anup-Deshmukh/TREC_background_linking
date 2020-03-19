#!/usr/bin/python3

import random
import argparse


def gen_result(infile, outfile):
	with open(infile, 'r', encoding='utf-8') as f:
		with open(outfile, 'w', encoding='utf-8') as f1:
			for line in f:
				li = line.split(' ')
				print(li[0])
				res = []
				res.append(li[0])
				res.append('Q0')
				res.append(li[2])
				res.append(str(random.randint(1,10)))
				res.append(str(random.random()))
				res.append('ICTNET')
				ans = "\t".join(res) + "\n"
				f1.write(ans)
		

parser = argparse.ArgumentParser(description="generate random results")
parser.add_argument('--infile', '-i', help='input file')
parser.add_argument('--outfile', '-o', help='output file')
args = parser.parse_args()
gen_result(args.infile, args.outfile)

