import os.path

from fastapi import FastAPI, File
from multiprocessing import Process
import io
from PIL import Image
from pydantic import TypeAdapter
import httpx
import sys
from pathlib import Path
import yaml
import uvicorn

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from deloop.schema import ItemModel, List

app = None
routes = {}


def convert_hf_dataset_to_yolo(save_dir, names, train, val=None, test=None):
    data = {
        'path': save_dir,
        'train': 'data/train.txt',
        'val': 'data/train.txt' if val is None else 'data/val.txt',
        'test': '' if test is None else 'data/test.txt',
        'names': {i: names[i] for i in range(len(names))}
    }

    for dataset, tag in [(train, 'train'), (val, 'val'), (test, 'test')]:
        if dataset is None:
            continue

        image_names = []
        for i in dataset:
            annos = []
            image = i['image']
            width = i['width']
            height = i['height']

            image_name = i['__meta__']['image_name']
            save_path = os.path.join(data['path'], 'data', image_name)
            if not os.path.exists(os.path.dirname(save_path)):
                os.makedirs(os.path.dirname(save_path))

            image.save(save_path)
            save_path = os.path.abspath(save_path)
            image_names.append(save_path)

            for b, c in zip(*(i['objects']['bbox'], i['objects']['category'])):
                # x1, y1, w, h
                x1, y1, w, h = b
                cx, cy, w, h = (x1 + w / 2) / width, (y1 + h / 2) / height, w / width, h / height
                annos.append(f"{c} {cx} {cy} {w} {h}")

            save_path = os.path.join(data['path'], 'data', image_name.split('.')[0] + '.txt')
            if not os.path.exists(os.path.dirname(save_path)):
                os.makedirs(os.path.dirname(save_path))

            with open(save_path, 'w') as f:
                f.write('\n'.join(annos))

        # write train.txt / test.txt / val.txt
        with open(os.path.join(data['path'], data[tag]), 'w') as f:
            f.write('\n'.join(image_names))

    with open(os.path.join(save_dir, 'data.yaml'), 'w') as f:
        yaml.safe_dump(data, f)

    return os.path.join(save_dir, 'data.yaml')


def create_server(local_server_host, local_server_port, local_server_endpoint):
    api = 'http://' + local_server_host + ':' + str(local_server_port),
    assert api not in routes, "Server already exists at " + api

    app = FastAPI()
    routes[api] = app

    def decorator(func):
        @app.post(local_server_endpoint, response_model=List[ItemModel])
        def wrapper(image: bytes = File(...)):
            im = Image.open(io.BytesIO(image))
            infer_result = func(im)

            # Validation Output (Output to the deloop server)
            # Return the result as a JSON response to the client
            return TypeAdapter(List[ItemModel]).validate_python(infer_result)

        p = Process(target=uvicorn.run, args=(app,),
                    kwargs={'host': local_server_host, 'port': local_server_port})
        p.daemon = True

        class TMP():
            def __init__(self, p):
                self.p = p
                ...

            def __call__(self):
                self.p.start()

        return TMP(p)

    return decorator
