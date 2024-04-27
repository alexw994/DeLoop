from PIL import Image
import io
from fastapi import APIRouter
import urllib

from . import scheduler, DELOOP_HOST_PORT
from .utils import es_get_record
from deloop.al_backend.backend.base import BaseDetecionALBackend
from deloop.schema import DeRecordModel
from deloop.al_backend.query_method.foward_noise import state_calssify
import requests

router = APIRouter(prefix='/api/v1/de', tags=['aps'])


def add_schedule_func_http_request_job(*, project_name, time_interval):
    job_name = 'project:' + project_name

    for job in scheduler.get_jobs():
        if job.name == job_name:
            scheduler.remove_job(job.id)

    local_port = int(DELOOP_HOST_PORT.split(':')[1])
    local_url = f'http://localhost:{local_port}/api/v1/de/al/schedule'

    job = scheduler.add_job(func=requests.put,
                            trigger='interval',
                            name=job_name,
                            args=(local_url,),
                            kwargs={'json': {"project_name": project_name}},
                            minutes=time_interval)
    return job.id


def add_callback_func_http_request_job(*, project_name, record_id):
    job_name = 'record_id:' + record_id

    for job in scheduler.get_jobs():
        if job.name == job_name:
            scheduler.remove_job(job.id)

    local_port = int(DELOOP_HOST_PORT.split(':')[1])
    local_url = f'http://localhost:{local_port}/api/v1/de/al/callback'

    job = scheduler.add_job(func=requests.put,
                            trigger='date',
                            name=job_name,
                            args=(local_url,),
                            kwargs={'json': {"project_name": project_name, "record_id": record_id}})
    return job.id


def callback_func(es, storage, record_index_name, bucket_name, record_id,
                  al_backend: BaseDetecionALBackend):
    result = es_get_record(record_id=record_id)['hits']['hits'][0]
    record = DeRecordModel.parse_obj(result['_source'])

    image = storage.get_object(bucket_name, object_name=record.image_name)
    image = Image.open(io.BytesIO(image.data))
    items = record.bboxes

    state, uncertainty_score = state_calssify(image, al_backend, items)
    record.state = state.value
    record.uncertainty = uncertainty_score

    _id = result["_id"]

    es.update(index=record_index_name,
              id=_id,
              body={"doc": {"state": state.value,
                            "uncertainty": uncertainty_score}})


def schedule_func(es, storage, record_index_name, bucket_name, batch, al_backend: BaseDetecionALBackend):
    def count_records(project_name):
        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"project_name.keyword": project_name}},
                        {"match": {"state.keyword": "initialization"}}
                    ]
                }
            }
        }

        result = es.count(index=record_index_name, body=query_body)
        return result['count']

    # Call the AL interface, calculate the uncertainty score, and modify the original data
    query_body = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"project_name.keyword": al_backend.project_name}},
                    {"match": {"state.keyword": "initialization"}}
                ]
            }
        },
        "size": batch
    }
    # refresh index
    es.indices.refresh(index=record_index_name)

    results = es.search(index=record_index_name, body=query_body)
    updates = []

    for result in results['hits']['hits']:
        _id = result['_id']

        record = DeRecordModel.parse_obj(result['_source'])
        items = record.bboxes
        image_name = record.image_name

        image = storage.get_object(bucket_name, object_name=image_name)
        image = Image.open(io.BytesIO(image.data))

        state, uncertainty_score = state_calssify(image, al_backend, items)
        updates.append((_id, state, uncertainty_score))

    for _id, state, uncertainty_score in updates:
        es.update(index=record_index_name,
                  id=_id,
                  body={"doc": {"state": state.value,
                                "uncertainty": uncertainty_score}})


@router.get("/aps/jobs")
def aps_jobs():
    jobs = scheduler.get_jobs()
    return {'jobs_state': [{
        'version': 1,
        'id': j.id,
        'func': j.func_ref,
        'name': j.name,
        'next_run_time': j.next_run_time if hasattr(j, 'next_run_time') else None
    } for j in jobs],
        'state': ['STATE_STOPPED', 'STATE_RUNNING', 'STATE_PAUSED'][scheduler.state]}
