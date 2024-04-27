import numpy as np
import requests
from PIL import Image
from io import BytesIO

default_thres = 20


def get_features(image: Image.Image):
    width = 8
    height = 8
    img = image.resize((width, height), resample=Image.BICUBIC)
    feature = np.array(img).astype(np.float32).flatten()
    return feature


def comepare(feature1, feature2):
    # psnr 0-inf
    # The larger the value, the more similar.
    mse = ((feature1 - feature2) ** 2).mean()
    psnr = 10 * np.log10(255 * 255 / mse)
    return psnr


if __name__ == '__main__':
    image1 = Image.open(BytesIO(requests.get(
        'http://10.39.88.175:9000/default/0007d172-6974-4f5b-892c-ad2435fbf121.jpg').content))
    image2 = Image.open(BytesIO(requests.get(
        'http://10.39.88.175:9000/default/00364062-a43b-4f08-b194-70925262b2c8.jpg').content))

    feature1 = get_features(image1)
    feature2 = get_features(image1)

    print(comepare(feature1, feature2))
