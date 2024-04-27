# YOLOv5 🚀 by Ultralytics, AGPL-3.0 license
"""Run a Flask REST API exposing one or more YOLOv5s models."""

import argparse
import io
import os.path
import json

from flask import Flask, request
from PIL import Image
from transformers import AutoModelForObjectDetection
import uuid
import os
import sys

app = Flask(__name__)
models = {}

DETECTION_URL = "/v1/object-detection"
model = AutoModelForObjectDetection.from_pretrained('./alexwww94/yolov8', trust_remote_code=True,
                                                    yolo_model_config={"model": 'yolov8n'})

global use_deloop
use_deloop = False


@app.route(DETECTION_URL, methods=["POST"])
def predict():
    if request.method != "POST":
        return

    if request.files.get("image"):
        im_file = request.files["image"]
        im_bytes = im_file.read()
        im = Image.open(io.BytesIO(im_bytes))

        if use_deloop:
            image_name = str(uuid.uuid4()) + '.jpg'
            deloop.upload_image(image_name, im)

        results = model(im, imgsz=640)  # reduce size=320 for faster inference
        results = [json.loads(i.tojson()) for i in results]
        if use_deloop:
            deloop.upload_record(image_name=image_name,
                                 bboxes=results[0])
        return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask API exposing YOLOv5 model")
    parser.add_argument("--port", default=6008, type=int, help="port number")
    parser.add_argument("--use_deloop", action='store_true', help="use deloop upload request")

    opt = parser.parse_args()

    if opt.use_deloop:
        from deloop import DeloopClient

        use_deloop = opt.use_deloop

        deloop = DeloopClient(host_port='http://10.39.88.175:9601',
                              project_name='example_project',
                              project_type='ObjectDetection',
                              infer_model='yolov8',
                              max_workers=4)

    app.run(host="0.0.0.0", port=opt.port)  # debug=True causes Restarting with stat
