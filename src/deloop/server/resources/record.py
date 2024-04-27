import time
import urllib
import uuid
from datetime import datetime

import httpx
from fastapi import Request, APIRouter, Response

from .utils import sql_read_only_trans, es_get_record, url_joint

from . import storage, bucket_name, minio, scheduler, record_index_name, es, aps, DELOOP_HOST_PORT
from deloop.schema import *

router = APIRouter(prefix='/api/v1/de', tags=['records'])


class _RecordPostAPIInputData(BaseModel):
    bboxes: List[ItemModel]
    project_name: str
    image_name: str


class _RecordPostAPIResponseData(BaseModel):
    record_id: str


@router.post('/records', response_model=_RecordPostAPIResponseData)
def record_post(data: _RecordPostAPIInputData, request: Request):
    '''
    All image addresses need to be forwarded through this service, rather than directly creating MinIO image url.
    '''
    server_ip = str(request.base_url.netloc).split(':')[0]
    port = int(DELOOP_HOST_PORT.split(':')[-1])
    image_file_name = data.image_name if data.image_name.endswith(
        '.jpg') else data.image_name + '.jpg'
    
    image_shared_url = url_joint('http://{}:{}'.format(server_ip, port),
                                 '/api/v1/de/minio_proxy',
                                 bucket_name,
                                 image_file_name)

    image_url = url_joint('{}://{}'.format(storage._base_url._url.scheme, storage._base_url._url.netloc),
                          bucket_name,
                          image_file_name)
    '''
    Generate a unique identifier for the record.
    Create a new record model from the data provided, setting the timestamp to the current date and time.
    Setting the initial state, and adding the unique identifier
    '''
    record_id = str(uuid.uuid4())
    record = DeRecordModel(**(data.model_dump()),
                           timestamp=datetime.now().strftime("%Y/%-m/%-d %H:%M:%S"),
                           state=StatusEnum.INIT.value,
                           record_id=record_id,
                           uncertainty=-1,
                           image_shared_url=image_shared_url,
                           image_url=image_url)

    # Check if the image has been successfully stored.
    count = 0
    while count < 5:
        try:
            storage.stat_object(bucket_name=bucket_name, object_name=record.image_name)
            break
        except minio.error.S3Error as e:
            time.sleep(0.5)
            count += 1
            continue

    projects = sql_read_only_trans(ProjectOrm, ProjectModel, name=record.project_name)
    if len(projects) != 0:
        project = projects[0]
        if project.has_al_backend:
            aps.add_callback_func_http_request_job(project_name=project.name, record_id=record_id)

    response = es.index(index=record_index_name, body=record.model_dump())
    return _RecordPostAPIResponseData(record_id=record_id)


@router.get('/minio_proxy/{bucket_name}/{file_name}')
def minio_proxy(bucket_name: str, file_name: str):
    image_shared_url = '{}://{}/{}/{}'.format(storage._base_url._url.scheme,
                                              storage._base_url._url.netloc,
                                              bucket_name,
                                              file_name)
    response = httpx.get(image_shared_url)

    return Response(response.read())


@router.delete('/records/{record_id}')
def record_delete(record_id: str):
    results = es_get_record(record_id=record_id)['hits']['hits']
    if len(results) != 0:
        id = results[0]['_id']
        es.delete(index=record_index_name, id=id)
        return Response('ok')
    else:
        return Response(f'{record_id} 不存在', status_code=404)


@router.get('/record_ids', response_model=List[str])
def record_getallid():
    results = es_get_record()
    results = [DeRecordModel.parse_obj(raw['_source']).record_id for raw in results['hits']['hits']]
    return results


@router.get('/records/{record_id}', response_model=DeRecordModel)
def record_get1(record_id: str):
    results = es_get_record(record_id=record_id)
    results = [DeRecordModel.parse_obj(raw['_source']).model_dump() for raw in results['hits']['hits']]
    if len(results) != 0:
        return results[0]
    else:
        return Response(f'{record_id} 不存在', status_code=404)


@router.get('/records', response_model=List[DeRecordModel])
def record_get2(project_name: Optional[str] = None,
                size: Optional[int] = None,
                record_id: Optional[str] = None):
    results = es_get_record(size=size, record_id=record_id, project_name=project_name)
    results = [DeRecordModel.parse_obj(raw['_source']).model_dump() for raw in results['hits']['hits']]
    return results
