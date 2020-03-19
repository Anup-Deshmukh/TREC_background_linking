# Track_code
ICTNET@ TREC 2018 News Track

This is the code I tried on the News Track 2018 Task.

## Data Process and Observation [code here](./src/DataProcess)

* lower case
* stemmer
* remove stop words

## Successful Methods

* Elasticsearch BM25 (`Background Linking`) [code here](./src/elastic)
  * Build index : title + body
  * Query: title + body (Other query extension method: name entity, TFIDF, are no better than this)
  * [results here](./ICTNET_stem.trec_eval)

| Dataset | 2018 | 2019 |
|-----|-----|-----|
| ndcg@5 | 0.4541 | 0.5801 |

* Elasticsearch BM25  + Wiki Dump (`Entity ranking`) [code here](./src/entity)
  * Build index : Wiki page with enlink refer to exact one entity, extract 100 wiki page per entity
  * Query: news title + body
  * Ranking entities by wiki page bm25 score 
  * [results here](./ICTNET_estem.trec_eval)

| Dataset | 2018 | 2019 |
|-----|-----|-----|
| ndcg@5 | 0.7191 | 0.7315 |

##  Failed Methods

  * Bert (Background Linking only)
      * Reason: Too Slow and OOM
      * PipeLine: Like Regular Search Engine, recall + reranking
        * DataProcess [code here](./src/DataProcess)
        * Recall [code here](./src/Recall)
        * GenSample [code here](./src/GenSample)
        * Ranking [code here](./src/Ranking)
      * I also tried Spark, but seems worse than Elasticsearch
* Synonyms word vector in Elasticsearch [code here](./src/vector)
     * This didn't work either
* Unfinished Methods
  * Lucene: Since there is no time to try Lucene, I just list the example [code here](./src/lucene).

### [Paper Notes](https://github.com/lixiyi/Track_Report)