import os.path
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).parents[1] / 'src'
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from fastapi.testclient import TestClient
from deloop.client import DeloopClient
from deloop.server.app import app
from PIL import Image

for route in app.routes:
    if '/api/v1/de' in route.path:
        print(f"{route.path}")

test_client = TestClient(app)

test_al_backend_url = '/test_al_backend'
test_al_backend_host = '127.0.0.1'
test_al_backend_port = 6107


def mock_post(url, data):
    url = url.replace(str(test_client.base_url), '')
    return test_client.post(url, json=data)


def mock_get(url, data=None):
    url = url.replace(str(test_client.base_url), '')
    return test_client.get(url)


from unittest import mock


def test_deloop_client():
    with mock.patch('deloop.client.client._post', mock_post):
        with mock.patch('deloop.client.client._get', mock_get):
            project_name = str(uuid.uuid4())

            client = DeloopClient(host_port=str(test_client.base_url),
                                  infer_model='TestResNet')

            client.set_project_name(project_name)
            assert client.remote_project_exits(project_name)

            image = Image.open(os.path.dirname(__file__) + '/' + 'bus.jpg')
            image_name = str(uuid.uuid4()) + '.jpg'
            client.upload_image(image_name, image, project_name)

            bboxes = [
                {
                    "name": "example_name",
                    "class": 42,
                    "confidence": 0.87,
                    "box": {
                        "x1": 10.5,
                        "y1": 20.3,
                        "x2": 30.8,
                        "y2": 40.2
                    }
                }
            ]
            client.upload_record(image_name, bboxes, project_name)

            @client.add_al_backend(test_al_backend_host,
                                   test_al_backend_port,
                                   test_al_backend_url,
                                   project_name=project_name)
            def infer(image):
                return [
                    {
                        "name": "example_name",
                        "class": 42,
                        "confidence": 0.87,
                        "box": {
                            "x1": 10.5,
                            "y1": 20.3,
                            "x2": 30.8,
                            "y2": 40.2
                        }
                    }
                ]

            infer()
