from sentence_transformers import SentenceTransformer
from rake_nltk import Rake

model = SentenceTransformer('roberta-large-nli-stsb-mean-tokens')

sentences = ['This framework generates embeddings for each input sentence',
    'Sentences are passed as a list of string.', 
    'The quick brown fox jumps over the lazy dog.']


sentence_embeddings = model.encode(sentences)

for sentence, embedding in zip(sentences, sentence_embeddings):
    print("Sentence:", sentence)
    print("Embedding shape:", embedding.shape)
    print("")
