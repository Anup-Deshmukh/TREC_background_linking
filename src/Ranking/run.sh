#!/bin/bash

cp /home/trec7/lianxiaoying/Track_code/src/Ranking/run_classifier.py /home/trec7/lianxiaoying/bert

export BERT_BASE_DIR=/home/trec7/lianxiaoying/model/uncased_L-12_H-768_A-12
export DATA_DIR=/home/trec7/lianxiaoying/Track_code/src/outputs


CUDA_VISIBLE_DEVICES=3 python /home/trec7/lianxiaoying/bert/run_classifier.py \
  --task_name=bertcls \
  --do_train=true \
  --do_eval=true \
  --do_predict=true \
  --data_dir=$DATA_DIR \
  --vocab_file=$BERT_BASE_DIR/vocab.txt \
  --bert_config_file=$BERT_BASE_DIR/bert_config.json \
  --init_checkpoint=$BERT_BASE_DIR/bert_model.ckpt \
  --max_seq_length=128 \
  --train_batch_size=16 \
  --eval_batch_size=16 \
  --predict_batch_size=16 \
  --learning_rate=2e-5 \
  --num_train_epochs=1.0 \
  --output_dir=/home/trec7/lianxiaoying/trained_model