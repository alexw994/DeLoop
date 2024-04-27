import os.path
import sys
import time
import uuid
from pathlib import Path
import pytest

ROOT = Path(__file__).parents[1] / 'src'
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from fastapi.testclient import TestClient
from deloop.server.app import app
from deloop.image_util import image_to_base64
from deloop.server.resources.record import record_get2

import fake_al_backend
from PIL import Image

for route in app.routes:
    if '/api/v1/de' in route.path:
        print(f"{route.path}")

test_client = TestClient(app)
fake_al_backend.create()
al_backend_host = fake_al_backend.test_al_backend_host
al_backend_port = fake_al_backend.test_al_backend_port
al_backend_url = fake_al_backend.test_al_backend_url


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


@pytest.mark.parametrize(
    "project_name,image_name,post_project_data,post_image_data,post_record_data", [random_test_data()]
)
def test_image_records(project_name, image_name, post_project_data, post_image_data, post_record_data):
    # insert
    response = test_client.post("/api/v1/de/images", json=post_image_data)
    assert response.status_code == 200

    response = test_client.post("/api/v1/de/records", json=post_record_data)
    assert response.status_code == 200
    record_id = response.json()['record_id']

    # select ids
    response = test_client.get("/api/v1/de/record_ids")
    assert response.status_code == 200

    # select
    for _project_name, _size, _record_id in [(project_name, 3, record_id),
                                             (None, 5, record_id),
                                             (project_name, None, record_id),
                                             (project_name, 7, None),
                                             (None, None, record_id),
                                             (project_name, None, None),
                                             (None, 10, None),
                                             (None, None, None)]:
        params = {"project_name": _project_name, "size": _size, "record_id": _record_id}
        params = {k: v for k, v in params.items() if v is not None}
        response = test_client.get("/api/v1/de/records",
                                   params=params)
        assert response.status_code == 200

        if _record_id is not None:
            assert _record_id in [i['record_id'] for i in response.json()]

        record_get2(_project_name, _size, _record_id)

    # delete
    response = test_client.delete(f"/api/v1/de/records/{record_id}")
    assert response.status_code == 200

    # delete 404
    response = test_client.delete(f"/api/v1/de/records/{record_id}")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "project_name,image_name,post_project_data,post_image_data,post_record_data", [random_test_data()]
)
def test_project(project_name, image_name, post_project_data, post_image_data, post_record_data):
    # insert
    response = test_client.post("/api/v1/de/projects", json=post_project_data)
    print(response.content)
    assert response.status_code == 200

    # select
    response = test_client.get("/api/v1/de/projects")
    print(response.content)
    assert response.status_code == 200

    response = test_client.get(f"/api/v1/de/projects/{project_name}")
    print(response.content)
    assert response.status_code == 200

    # delect
    response = test_client.delete(f"/api/v1/de/projects/{project_name}")
    assert response.status_code == 200
    response = test_client.get("/api/v1/de/projects")
    assert project_name not in [i['name'] for i in response.json()]

    # select 404
    response = test_client.get(f"/api/v1/de/projects/{project_name}")
    print(response.content)
    assert response.status_code == 404


@pytest.mark.parametrize(
    "project_name,image_name,post_project_data,post_image_data,post_record_data", [random_test_data()]
)
def test_al_backend_health(project_name, image_name, post_project_data, post_image_data, post_record_data):
    image_url = 'https://app.heartex.ai/static/samples/sample.jpg'

    post_project_data['has_al_backend'] = True
    post_project_data['al_backend_config'] = {
        "headers": "{}",
        "api": f"http://{al_backend_host}:{al_backend_port}{al_backend_url}"
    }

    response = test_client.post("/api/v1/de/projects", json=post_project_data)
    assert response.status_code == 200

    response = test_client.post('/api/v1/de/al_backend/health',
                                json={'project_name': project_name, 'image_url': image_url})
    assert response.status_code == 200


@pytest.mark.parametrize(
    "project_name,image_name,post_project_data,post_image_data,post_record_data", [random_test_data()]
)
def test_put_project_al_schedule_call(project_name, image_name, post_project_data, post_image_data, post_record_data):
    post_project_data['has_al_backend'] = True
    post_project_data['al_backend_config'] = {
        "headers": "{}",
        "api": f"http://{al_backend_host}:{al_backend_port}{al_backend_url}"
    }

    response = test_client.post("/api/v1/de/projects", json=post_project_data)
    assert response.status_code == 200

    # insert
    response = test_client.post("/api/v1/de/images", json=post_image_data)
    print(response.content)
    assert response.status_code == 200

    response = test_client.post("/api/v1/de/records", json=post_record_data)
    assert response.status_code == 200
    record_id = response.json()['record_id']

    # test project al schedule
    response = test_client.put("/api/v1/de/al/schedule", json={'project_name': project_name})
    print(response.content)
    assert response.status_code == 200

    response = test_client.get(f'/api/v1/de/records/{record_id}')
    print(response.json())
    assert response.status_code == 200
    assert response.json()['state'] != 'initialization'


@pytest.mark.parametrize(
    "project_name,image_name,post_project_data,post_image_data,post_record_data", [random_test_data()]
)
def test_put_project_al_callback_call(project_name, image_name, post_project_data, post_image_data, post_record_data):
    post_project_data['has_al_backend'] = True
    post_project_data['al_backend_config'] = {
        "headers": "{}",
        "api": f"http://{al_backend_host}:{al_backend_port}{al_backend_url}"
    }

    response = test_client.post("/api/v1/de/projects", json=post_project_data)
    assert response.status_code == 200

    # insert
    response = test_client.post("/api/v1/de/images", json=post_image_data)
    print(response.content)
    assert response.status_code == 200

    response = test_client.post("/api/v1/de/records", json=post_record_data)
    assert response.status_code == 200
    record_id = response.json()['record_id']

    # test project al callback
    response = test_client.put("/api/v1/de/al/callback", json={'project_name': project_name, "record_id": record_id})
    print(response.content)
    assert response.status_code == 200

    response = test_client.get(f'/api/v1/de/records/{record_id}')
    print(response.json())
    assert response.status_code == 200
    assert response.json()['state'] != 'initialization'


@pytest.mark.parametrize(
    "project_name,image_name,post_project_data,post_image_data,post_record_data", [random_test_data()]
)
def test_post_al_backend(project_name, image_name, post_project_data, post_image_data, post_record_data):
    response = test_client.post("/api/v1/de/projects", json=post_project_data)
    assert response.status_code == 200

    al_backend_config = {
        "headers": "{}",
        "api": f"http://{al_backend_host}:{al_backend_port}{al_backend_url}",
        "project_name": project_name
    }
    response = test_client.post('/api/v1/de/al_backend',
                                json=al_backend_config)
    print(response.content)
    assert response.status_code == 200

    response = test_client.get(f"/api/v1/de/projects/{project_name}")
    assert response.status_code == 200
    assert response.json()['has_al_backend'] == True


@pytest.mark.parametrize(
    "project_name,image_name,post_project_data,post_image_data,post_record_data", [random_test_data()]
)
def test_dataset(project_name, image_name, post_project_data, post_image_data, post_record_data):
    # create project
    response = test_client.post("/api/v1/de/projects", json=post_project_data)
    print(response.content)
    assert response.status_code == 200

    # insert image and record
    response = test_client.post("/api/v1/de/images", json=post_image_data)
    print(response.content)
    assert response.status_code == 200

    response = test_client.post("/api/v1/de/records", json=post_record_data)
    assert response.status_code == 200

    # select dataset, project_name
    response = test_client.get('/api/v1/de/datasets', params={'project_name': project_name})
    assert response.status_code == 200

    # select dataset, archived=False
    response = test_client.get('/api/v1/de/datasets', params={'project_name': project_name, "archived": False})
    assert response.status_code == 200

    # select
    response = test_client.get('/api/v1/de/datasets')
    assert response.status_code == 200

    # archive
    response = test_client.post('/api/v1/de/datasets/archive', json={'project_name': project_name})
    assert response.status_code == 200

    # select archived dataset
    params = {"project_name": project_name, "archived": True}
    response = test_client.get('/api/v1/de/datasets', params=params)
    assert len(response.json()) > 0

    # upload archived dataset to hf
    archived_dataset_name = response.json()[0]['name']
    response = test_client.post('/api/v1/de/datasets/uploadhf', json={'archived_dataset_name': archived_dataset_name})
    print(response.content)
    assert response.status_code == 200

    # download archived dataset
    response = test_client.post('/api/v1/de/datasets/download', json={'archived_dataset_name': archived_dataset_name})
    print(response.content)
    assert response.status_code == 200

    # delect archived dataset
    response = test_client.delete(f'/api/v1/de/datasets/{archived_dataset_name}')
    assert response.status_code == 200


@pytest.mark.parametrize(
    "project_name,image_name,post_project_data,post_image_data,post_record_data", [random_test_data()]
)
def test_apply_ls_project(project_name, image_name, post_project_data, post_image_data, post_record_data):
    # create project
    response = test_client.post("/api/v1/de/projects", json=post_project_data)
    print(response.content)
    assert response.status_code == 200

    # insert image and record
    response = test_client.post("/api/v1/de/images", json=post_image_data)
    print(response.content)
    assert response.status_code == 200

    response = test_client.post("/api/v1/de/records", json=post_record_data)
    assert response.status_code == 200

    # apply_ls_project
    response = test_client.put("/api/v1/de/apply_ls_project")
    assert response.status_code == 200


# TODO
def test_ls_webhook_delete():
    ...


# TODO
def test_ls_webhook_submit():
    ...
