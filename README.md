
## IR-BERT @ TREC 2020 News Track (Background Linking)

This repo has the implementation of two methods
* Weighted Search Query + BM25 [code here](./src/IR-BERT/WBT%2BBM25.py)
* IR-BERT [code here](./src/IR-BERT/IR-BERT.py)

#### Steps for running the code on your machine
* ./src/path.cfg 
	* Ignore the following variables: 
		* topics19
		* entities
		* entities19
		* eqrels
	* All the background linking related files (The dataset, topics and qrels) go in the path given by "DataPath" variable
* Result files are created by both main scripts of two models, IR-BERT and Weighted BM25 
* These result files in turn can be directly evaluted by using the background linking eval script


#### Steps to run IR-BERT

* Set appropriate paths in src/path.cfg
* Run merge.py in wapo/WashingtonPost/data. You will need the files listed in "filenames" in this directory alongside the merge script.
* Start elasticsearch server. command: "elasticsearch". (In case of port mismatch check "http.port" in elasticsearch.yml)
* Run Preprocess.py
* Run IR-BERT.py

#### Data Processing [code here](./src/IR-BERT/Preprocess.py)

* lower case all the text 
* stemming and lematization
* remove stop words by using "stopwords.txt" as a dictionary of words
* filter the articles based on their kicker field

#### Best performing model: IR-BERT

<img src="https://github.com/Anup-Deshmukh/TREC_background_linking/blob/master/final.png" alt="drawing" height="170" width="350"/>

* We propose IR-BERT, which combines the retrieval power of BM25 with the contextual understanding gained through a BERT based model. It has following components
	* Elasticsearch BM25
	* RAKE for keyword extraction
	* Setence BERT for semantic similarity
* Our model outperforms the TREC median as well as the highest scoring model of 2018 in terms of the nDCG@5 metric.

<img src="https://github.com/Anup-Deshmukh/TREC_background_linking/blob/master/res1.png" alt="drawing" height="150" width="220"/>

#### If you find this code helpful do cite our [arxiv paper](https://arxiv.org/pdf/2007.12603.pdf)

#### Recommended citation: Deshmukh, Anup Anand, and Udhav Sethi. "IR-BERT: Leveraging BERT for Semantic Search in Background Linking for News Articles." arXiv preprint arXiv:2007.12603 (2020).


