import urllib.parse

from fastapi import APIRouter, Request
from typing import *
from PIL import Image
from io import BytesIO

import requests
from deloop.schema import DeRecordModel, ItemModel, StatusEnum, BBoxModel, Enum, BaseModel
from . import *
from .utils import es_get_record, url_joint
from .dataset import _get_unarchived_dataset


def get_image_dimensions(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

    # Get the total content length from the headers
    total_length = int(response.headers.get('Content-Length', 0))

    # Read the entire content or a reasonable portion (e.g., first 2048 bytes)
    chunk_size = min(total_length, 624)

    content = next(response.iter_content(chunk_size=chunk_size))

    # Extracting width and height using PIL
    image = Image.open(BytesIO(content))
    width, height = image.size

    return int(width), int(height)


def convert_ls_anno_to_items(annos):
    items = []
    for anno in annos:
        value = anno['value']
        original_width = anno['original_width']
        original_height = anno['original_height']
        items.append(ItemModel(
            name=value['rectanglelabels'][0],
            confidence=1,
            box=BBoxModel(x1=value['x'] / 100 * original_width,
                          y1=value['y'] / 100 * original_height,
                          x2=(value['x'] + value['width']) / 100 * original_width,
                          y2=(value['y'] + value['height']) / 100 * original_width)).model_dump())
    return items


def convert_record_to_ls_task(records):
    tasks = []
    for i in range(len(records)):
        width, height = get_image_dimensions(records[i].image_url)
        task = {
            "data": {
                "image": records[i].image_shared_url
            },
            "predictions": [
                {
                    "score": 1 - records[i].uncertainty,
                    "result": [
                        {
                            "original_width": width,
                            "original_height": height,
                            "image_rotation": 0,
                            "value": {
                                "x": records[i].bboxes[j].box.x1 / width * 100,
                                "y": records[i].bboxes[j].box.y1 / height * 100,
                                "width": (records[i].bboxes[j].box.x2 - records[i].bboxes[j].box.x1) / width * 100,
                                "height": (records[i].bboxes[j].box.y2 - records[i].bboxes[j].box.y1) / height * 100,
                                "rotation": 0,
                                "rectanglelabels": [
                                    records[i].bboxes[j].name
                                ]
                            },
                            "from_name": "tag",
                            "to_name": "img",
                            "type": "rectanglelabels",
                            "origin": "manual"
                        }
                        for j in range(len(records[i].bboxes))]
                }
            ],
            "annotations": [],
            "meta": {'record_id': records[i].record_id,
                     'project_name': records[i].project_name,
                     'image_name': records[i].image_name}
        }
        tasks.append(task)
    return tasks


router = APIRouter(prefix="/api/v1/de", tags=["ls"])


@router.put("/apply_ls_project")
def apply_ls_project(request: Request):
    # Each call will synchronize all deloop projects to Label Studio.
    datasets = _get_unarchived_dataset()
    ls_client.delete_all_projects()

    for dataset in datasets:
        for type in ['ORA', 'AUTO']:
            # create
            labels = dataset['labels']
            labels_element_xml = ''.join(['''<Label value=\"{}\" class_index=\"{}\"></Label>'''.format(i, labels[i])
                                          for i in labels.keys()])

            label_config = '''
            <View>
              <Image name="img" value="$image"></Image>
              <RectangleLabels name="tag" toName="img">
                {}
              </RectangleLabels>
            </View>
            '''.format(labels_element_xml)

            ls_project = ls_client.start_project(title=dataset['project_name'] + '_' + type,
                                                 label_config=label_config)

            server_ip = str(request.base_url.netloc).split(':')[0]
            port = int(DELOOP_HOST_PORT.split(':')[-1])

            # import data record
            ls_client.make_request('POST', url='/api/webhooks',
                                   data={"project": ls_project.params['id'],
                                         "url": url_joint('http://{}:{}'.format(server_ip, port),
                                                          "/api/v1/de/ls_webhook"),
                                         "send_payload": True,
                                         "send_for_all_actions": True,
                                         "headers": {},
                                         "is_active": True,
                                         "actions": []})

            results = es_get_record(project_name=dataset['project_name'],
                                    state='pending_oracle_annotation' if type == 'ORA' else 'auto_annotation_completed')
            records = [DeRecordModel.parse_obj(raw['_source']) for raw in results['hits']['hits']]
            tasks = convert_record_to_ls_task(records)

            if len(tasks):
                ls_project.import_tasks(tasks=tasks)
    return 'ok'


class _LSWebhookAction(Enum):
    ANNOTATION_UPDATED = 'ANNOTATION_UPDATED'
    ANNOTATION_CREATED = 'ANNOTATION_CREATED'


class _LSWebhookPostAPIInputData(BaseModel):
    action: _LSWebhookAction
    annotation: Dict
    task: Dict


@router.post("/ls_webhook")
def ls_webhook(data: _LSWebhookPostAPIInputData):
    task = data.task
    annotation = data.annotation
    action = data.action

    if action in ('ANNOTATION_UPDATED', 'ANNOTATION_CREATED'):
        # modify data in es
        bboxes = convert_ls_anno_to_items(annotation['result'])
        image_name = os.path.basename(task['data']['image'])
        _id = es_get_record(image_name=image_name)['hits']['hits'][0]['_id']

        es.update(index=record_index_name,
                  id=_id,
                  body={"doc": {"state": StatusEnum.HUMAN.value,
                                "bboxes": bboxes}})

    # TODO
    # elif data['action'] in ('TASKS_DELETED'):
    #     for task in data['tasks']:
    #         id = task['id']
    #         project = ls_client.get_project(data['project']['id'])
    #         task = project.get_task(id)
    #         image_name = os.path.basename(data['tasks'][0]['data']['image'])
    #         _id = es_get_record(image_name=image_name)['hits']['hits'][0]['_id']
    #         es.delete(index=record_index_name,
    #                   id=_id)

    return 'ok'


@router.get('/ls_auth')
def ls_auth():
    return ls_client.login_request_args
