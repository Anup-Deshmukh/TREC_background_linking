# Generate samples for Ranking
## Bert Classification
* Form: Label   sentence1   sentence2
* Sentence length: head + tail = 510
* Label: 0, 2, 4, 8, 16
    * Different topics: 0
    * Only same Topics: 2
    * Only same Key words or Entities: 4
	* Same Topics and key words or Entities: 8
    * Same Document: 16
* Filter
    * Date larger than current date
    * Same rep_key: title + '#' + author + '#' + 'date'
* Generate 5 example for each document: 0, 2, 4, 6, 8
    * Random choose a document by index for each level
