from transformers import EfficientNetImageProcessor, EfficientNetModel
import torch
import os
from PIL import Image
import numpy as np

default_thres = 0.7

preprocessor = None
model = None
if os.environ.get('DELOOP_IMAGE_EMBEDDING'):
    preprocessor = EfficientNetImageProcessor.from_pretrained("google/efficientnet-b0")
    model = EfficientNetModel.from_pretrained("google/efficientnet-b0")


def get_features(image: Image.Image):
    inputs = preprocessor(image, return_tensors="pt")

    with torch.no_grad():
        last_hidden_state = model(**inputs).last_hidden_state

    last_hidden_state = last_hidden_state / np.expand_dims(np.linalg.norm(last_hidden_state, axis=1), 1)
    return last_hidden_state


def comepare(features1, features2):
    # Cosine similarity, ranges from 0 to 1
    # The larger the value, the more similar
    return np.dot(features1.flatten(), features2.flatten())
