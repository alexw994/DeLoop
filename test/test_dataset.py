import os.path
import sys
import time
import uuid
from pathlib import Path
import pytest

ROOT = Path(__file__).parents[1] / 'src'
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from deloop.image_util import image_to_base64

from PIL import Image


def random_test_data():
    image = Image.open(os.path.dirname(__file__) + '/' + 'bus.jpg')
    image_base64 = image_to_base64(image)

    project_name = str(uuid.uuid4())
    image_name = str(uuid.uuid4()) + '.jpg'

    post_image_data = {'image_base64': image_base64,
                       'image_name': image_name}

    post_record_data = {
        "bboxes": [
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
        ],
        "project_name": project_name,
        "image_name": image_name
    }

    post_project_data = {
        "name": project_name,
        "infer_model": "ResNet50",
        "type": "ObjectDetection",
        "has_al_backend": False,
        "batch": 1,
        "describle": "A project for image recognition using ResNet50 model",
        "method": "FN",
        "time_interval": 1
    }

    return project_name, image_name, post_project_data, post_image_data, post_record_data


from deloop.server.app import app
from deloop.server.resources.dataset import save_raw
from deloop.server.resources.dataset import save_parquet
from deloop.server.resources.record import es_get_record, es, record_index_name
from fastapi.testclient import TestClient

for route in app.routes:
    if '/api/v1/de' in route.path:
        print(f"{route.path}")

test_client = TestClient(app)


@pytest.mark.parametrize(
    "project_name,image_name,post_project_data,post_image_data,post_record_data", [random_test_data()]
)
def test_dataset_save(project_name, image_name, post_project_data, post_image_data, post_record_data):
    # insert
    response = test_client.post("/api/v1/de/images", json=post_image_data)
    assert response.status_code == 200

    response = test_client.post("/api/v1/de/records", json=post_record_data)
    assert response.status_code == 200

    # hack
    record_id = response.json()['record_id']
    result = es_get_record(record_id=record_id)
    _id = result['hits']['hits'][0]['_id']
    es.update(index=record_index_name,
              id=_id,
              body={"doc": {"state": 'auto_annotation_completed',
                            "uncertainty": 0.2}})
    es.indices.refresh(index=record_index_name)

    # archive
    response = test_client.post('/api/v1/de/datasets/archive', json={'project_name': project_name})
    assert response.status_code == 200

    params = {"project_name": project_name, "archived": True}
    response = test_client.get('/api/v1/de/datasets', params=params)
    assert len(response.json()) > 0

    archived_dataset_name = response.json()[0]
    save_raw(archived_dataset_name['name'])
    save_parquet(archived_dataset_name['name'])
