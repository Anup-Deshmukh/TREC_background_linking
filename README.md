
### IR-BERT @ TREC 2020 News Track (Background Linking)

This repo has the implementation of two methods
* Weighted Search Query + BM25 [code here](./src/IR-BERT/wBT+BM25.py)
* IR-BERT [code here](./src/IR-BERT/IR-BERT.py)

#### Data Process and Observation [code here](./src/IR-BERT/Preprocess.py)

* lower case all the text 
* stemming and lematization
* remove stop words

#### Best performing model: IR-BERT

![Model](https://github.com/Anup-Deshmukh/TREC_background_linking/blob/master/final.png)

* We propose IR-BERT, which combines the retrieval power of BM25 with the contextual understanding gained through a BERT based model.
* This model outperforms the TREC median as well as the highest scoring model of 2018 in terms of the nDCG@5 metric.

![Results](https://github.com/Anup-Deshmukh/TREC_background_linking/blob/master/res1.png)

* If you find this code helpful please cite our [arxiv paper](https://arxiv.org/pdf/2007.12603.pdf)

#### Recommended citation: Deshmukh, Anup Anand, and Udhav Sethi. "IR-BERT: Leveraging BERT for Semantic Search in Background Linking for News Articles." arXiv preprint arXiv:2007.12603 (2020).


