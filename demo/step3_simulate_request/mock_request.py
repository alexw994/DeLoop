# YOLOv5 🚀 by Ultralytics, AGPL-3.0 license
"""Perform test request."""

import pprint

import requests
import glob

DETECTION_URL = "http://localhost:6008/v1/object-detection"
for IMAGE in glob.glob('./datasets/coco128/images/train2017/*.jpg'):
    # Read image
    with open(IMAGE, "rb") as f:
        image_data = f.read()

    response = requests.post(DETECTION_URL, files={"image": image_data}).json()

    pprint.pprint(response)
