#!/usr/bin/env python3

import subprocess
import tempfile
import argparse
import os

argparser = argparse.ArgumentParser(
    description='Evaluate a background linking run',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

argparser.add_argument('--treceval',
                       help='Path to trec_eval executable',
                       default='/Users/soboroff/trec/trec30/news/scripts/trec_eval.macos')
argparser.add_argument('--qrels',
                       help='Qrels file',
                       default='/Users/soboroff/trec/trec30/news/eval/qrels.background')
argparser.add_argument('runfile', help='Path to run to evaluate')

args = argparser.parse_args()

using_tempfile = False
actual_filename = args.runfile
if args.runfile.endswith('.gz'):
    decompressed = tempfile.NamedTemporaryFile(delete=False)
    result = subprocess.run(['gzip', '-dc', args.runfile],
                            stdout=decompressed)
    if result.returncode != 0:
        raise OSError(result.returncode, result.stderr)
    decompressed.close()
    using_tempfile = True
    actual_filename = decompressed.name

result = subprocess.run([args.treceval,
                         '-M 100',
                         '-q',
                         '-mall_trec',
                         # '-mndcg.1=2,2=4,3=8,4=16',
                         # '-l16',
                         args.qrels,
                         actual_filename])
if result.returncode != 0:
    raise OSError(result.returncode, result.stderr)

if using_tempfile:
    os.unlink(decompressed.name)