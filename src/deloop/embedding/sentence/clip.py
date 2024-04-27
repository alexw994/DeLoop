from transformers import CLIPModel, CLIPTokenizer
import torch
import os
import numpy as np

default_thres = 0.7

preprocessor = None
model = None
if os.environ.get('DELOOP_SENTENCE_EMBEDDING'):
    model = CLIPModel.from_pretrained("laion/CLIP-ViT-H-14-laion2B-s32B-b79K")
    tokenizer = CLIPTokenizer.from_pretrained("laion/CLIP-ViT-H-14-laion2B-s32B-b79K")


def get_feature(sentence):
    sentences = [sentence] if isinstance(str) else sentence

    inputs = tokenizer(sentences, padding=True, return_tensors="pt")

    with torch.no_grad():
        text_features = model.get_text_features(**inputs)

    text_features = text_features / np.expand_dims(np.linalg.norm(text_features, axis=1), 1)
    return text_features


def comepare(features1, features2):
    # Cosine similarity, ranges from 0 to 1
    # The larger the value, the more similar
    return np.dot(features1.flatten(), features2.flatten())
