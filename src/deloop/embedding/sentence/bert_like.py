from sentence_transformers import SentenceTransformer
import os
import numpy as np

preprocessor = None
model = None
if os.environ.get('DELOOP_SENTENCE_EMBEDDING'):
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def get_feature(sentence):
    sentences = [sentence] if isinstance(str) else sentence
    embeddings = model.encode(sentences, normalize_embeddings=True)
    return embeddings


def comepare(features1, features2):
    # Cosine similarity, ranges from 0 to 1
    # The larger the value, the more similar
    return np.dot(features1.flatten(), features2.flatten())
