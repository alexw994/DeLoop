from transformers import CLIPProcessor, CLIPModel
import torch
import os
from PIL import Image
import numpy as np

default_thres = 0.7

preprocessor = None
model = None
if os.environ.get('DELOOP_IMAGE_EMBEDDING'):
    preprocessor = CLIPProcessor.from_pretrained("laion/CLIP-ViT-H-14-laion2B-s32B-b79K")
    model = CLIPModel.from_pretrained("laion/CLIP-ViT-H-14-laion2B-s32B-b79K")


def get_features(image: Image.Image):
    inputs = preprocessor(images=image, return_tensors="pt")

    with torch.no_grad():
        image_features = model.get_image_features(**inputs)

    image_features = image_features / np.expand_dims(np.linalg.norm(image_features, axis=1), 1)
    return image_features


def comepare(features1, features2):
    # The larger the value, the more similar.
    return np.dot(features1.flatten(), features2.flatten())
