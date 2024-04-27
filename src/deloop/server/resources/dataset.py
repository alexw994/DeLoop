import math

import datasets
from fastapi import APIRouter, Request
from datasets import Dataset
from datasets import features
from io import BytesIO
import tempfile
import zipfile
import glob
import os
from PIL import Image
import io
import httpx

from . import es, storage, record_index_name, bucket_name, minio, DELOOP_HOST_PORT, scheduler
from .utils import es_get_record, url_joint
from deloop.schema import *
import huggingface_hub
import urllib

router = APIRouter(prefix='/api/v1/de', tags=['dataset'])


@router.delete('/datasets/{archived_dataset_name}')
def dataset_delete(archived_dataset_name: str):
    # delete index in es
    es.indices.delete(index=archived_dataset_name)

    # delete .zip file in minio if it existed
    try:
        storage.stat_object(bucket_name=bucket_name, object_name=archived_dataset_name + '_hf' + '.zip')
        # dont raise a error so this file is existed
        storage.remove_object(bucket_name=bucket_name, object_name=archived_dataset_name + '_hf' + '.zip')
    except:
        pass

    try:
        storage.stat_object(bucket_name=bucket_name, object_name=archived_dataset_name + '_raw' + '.zip')
        # dont raise a error so this file is existed
        storage.remove_object(bucket_name=bucket_name, object_name=archived_dataset_name + '_raw' + '.zip')
    except:
        pass

    return 'ok'


class _DownloadDatasetFormat(Enum):
    raw = 'raw'
    hf = 'hf'


class _DownloadDatasetPostAPIInputData(BaseModel):
    archived_dataset_name: str
    format: Optional[_DownloadDatasetFormat] = _DownloadDatasetFormat.hf


@router.post('/datasets/download')
def download_dataset(data: _DownloadDatasetPostAPIInputData, request: Request):
    archived_dataset_name = data.archived_dataset_name
    format = data.format

    server_ip = str(request.base_url.netloc).split(':')[0]
    port = int(DELOOP_HOST_PORT.split(':')[-1])

    if format == _DownloadDatasetFormat.raw.value:
        dataset_shared_url = url_joint('http://{}:{}'.format(server_ip, port),
                                       '/api/v1/de/minio_proxy',
                                       bucket_name, archived_dataset_name + '_raw' + '.zip')
        return dataset_shared_url

    elif format == _DownloadDatasetFormat.hf.value:
        dataset_shared_url = url_joint('http://{}:{}'.format(server_ip, port),
                                       '/api/v1/de/minio_proxy',
                                       bucket_name, archived_dataset_name + '_hf' + '.zip')
        return dataset_shared_url


def save_parquet(archived_dataset_name):
    try:
        storage.stat_object(bucket_name=bucket_name, object_name=archived_dataset_name + '.parquet')
        return 'already existed'
    except minio.error.S3Error as e:
        # dont existed
        all_indices = es.indices.get_alias().keys()
        dataset_index_names = [i for i in all_indices if i.startswith('dataset_from_')]
        assert archived_dataset_name in dataset_index_names, 'index not exist'

        # upload to minio
        results = es_get_record(index=archived_dataset_name)
        results = [DeRecordModel.parse_obj(raw['_source']) for raw in results['hits']['hits']]

        data = []
        image_id = 1
        object_id = int(10 ** (math.log10(len(results)) + 2) + 1)
        for i in results:
            image = Image.open(io.BytesIO(httpx.get(i.image_url).content))
            objects = {'id': [],
                       'area': [],
                       'bbox': [],
                       'category': []}

            for b in i.bboxes:
                box = b.box
                x1 = box.x1
                y1 = box.y1
                w = box.x2 - box.x1
                h = box.y2 - box.y1
                objects['id'].append(object_id)
                objects['area'].append(int(w * h))
                objects['bbox'].append([round(x1, 0), round(y1, 0), round(w, 0), round(h, 0)])
                objects['category'].append(b.class_field)

                object_id += 1

            j = {'image_id': image_id,
                 'image': image,
                 'width': image.width,
                 'height': image.height,
                 'objects': objects,
                 '__meta__': {'image_name': i.image_name,
                              'record_id': i.record_id}}
            image_id += 1
            data.append(j)

        labels = _get_archived_dataset_info(archived_dataset_name)['labels']
        num_classes = max([v for k, v in labels.items()]) + 1
        id2label = {v: k for k, v in labels.items()}
        names = [id2label[i] if i in id2label else f'missing_{i}' for i in range(num_classes)]

        hf_dataset_example = Dataset.from_list(data[0:1])
        features_example = hf_dataset_example.features
        features_example['objects'] = features.Sequence(features_example['objects'])
        features_example['objects'].feature['id'] = features.Value(dtype='int64')
        features_example['objects'].feature['area'] = features.Value(dtype='int64')
        features_example['objects'].feature['category'] = features.ClassLabel(names=names)
        features_example['objects'].feature['bbox'] = features.Sequence(features.Value(dtype='float64'))

        hf_dataset = Dataset.from_list(data,
                                       features=features_example)

        with tempfile.TemporaryDirectory() as tmpdir:
            hf_dataset.to_parquet(os.path.join(tmpdir, archived_dataset_name + '.parquet'))

            with tempfile.TemporaryFile() as tmpf:
                _zip_directory(tmpdir, tmpf)
                tmpf.seek(0)
                bytes_io = BytesIO(tmpf.read())
                # save
                bytes_io.seek(0)
                storage.put_object(bucket_name, archived_dataset_name + '_hf' + '.zip', bytes_io,
                                   len(bytes_io.getbuffer()))

        return 'ok'


def save_raw(archived_dataset_name):
    try:
        storage.stat_object(bucket_name=bucket_name, object_name=archived_dataset_name + '.zip')
        return 'already existed'

    except minio.error.S3Error as e:
        # dont existed
        all_indices = es.indices.get_alias().keys()
        dataset_index_names = [i for i in all_indices if i.startswith('dataset_from_')]
        assert archived_dataset_name in dataset_index_names, 'index not exist'

        # upload to minio
        results = es_get_record(index=archived_dataset_name)
        results = [DeRecordModel.parse_obj(raw['_source']) for raw in results['hits']['hits']]

        labels = _get_archived_dataset_info(archived_dataset_name)['labels']
        num_classes = max([v for k, v in labels.items()]) + 1
        id2label = {v: k for k, v in labels.items()}
        names = [id2label[i] if i in id2label else f'missing_{i}' for i in range(num_classes)]

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, 'labels.txt'), 'w') as f:
                for i in range(num_classes):
                    f.write(f'{i} {names[i]}\n')

            os.makedirs(os.path.join(tmpdir, 'anno'))
            for i in results:
                i = i.model_dump()
                image_url = i.pop('image_url')
                image_name = i.pop('image_name')
                record_id = i.pop('record_id')
                image = Image.open(io.BytesIO(httpx.get(image_url).content))
                image.save(os.path.join(tmpdir, image_name))
                json_file_path = os.path.join(tmpdir, 'anno', record_id + '.json')
                with open(json_file_path, 'w') as f:
                    json.dump(i, f)

            with tempfile.TemporaryFile() as tmpf:
                _zip_directory(tmpdir, tmpf)
                tmpf.seek(0)
                bytes_io = BytesIO(tmpf.read())
                # save
                bytes_io.seek(0)
                storage.put_object(bucket_name, archived_dataset_name + '_raw' + '.zip', bytes_io,
                                   len(bytes_io.getbuffer()))

        return 'ok'


class _UploadHFDatasetPostAPIInputData(BaseModel):
    archived_dataset_name: str
    space: str
    hf_token: str


@router.post('/datasets/uploadhf')
def upload_dataset_to_hf(data: _UploadHFDatasetPostAPIInputData):
    archived_dataset_name = data.archived_dataset_name

    dataset_url = url_joint('{}://{}'.format(storage._base_url._url.scheme, storage._base_url._url.netloc),
                            bucket_name,
                            archived_dataset_name + '_hf' + '.zip')

    response = httpx.get(dataset_url)
    # download
    with tempfile.TemporaryFile() as tmpf:
        tmpf.write(response.read())

        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(tmpf) as zf:
                zf.extractall(tmpdir)
            hf_dataset = datasets.load_dataset(tmpdir)

            # upload to hf
            huggingface_hub.login(token=data.hf_token)
            hf_dataset.push_to_hub(f'{data.space}/{archived_dataset_name}', private=True)

    return 'ok'


class _ArchiveDatasetPostAPIInputData(BaseModel):
    project_name: str


@router.post('/datasets/archive')
def dataset_archive(data: _ArchiveDatasetPostAPIInputData):
    project_name = data.project_name

    all_indices = es.indices.get_alias().keys()
    dataset_index_names = [i for i in all_indices if i.startswith('dataset_from_{}'.format(project_name))]
    max_version = None
    if len(dataset_index_names) == 0:
        # first version
        index_name = 'dataset_from_{}_v1'.format(project_name)
    else:
        # new version
        max_version = max(map(int, [i.split('_v')[-1] for i in dataset_index_names]))
        index_name = 'dataset_from_{}_v{}'.format(project_name, max_version + 1)

    archived_dataset_name = index_name

    # save dataset in this new index
    filter_query = {
        "bool": {
            "must": [
                {
                    "match": {"project_name.keyword": "example_project"}},
                {
                    "bool": {
                        "should": [
                            {"match": {"state.keyword": "human_annotation_completed"}},
                            {"match": {"state.keyword": "auto_annotation_completed"}}
                        ]
                    }
                }
            ]
        }
    }
    # query record numbers
    curr_results = es.search(index=record_index_name,
                             body={'query': filter_query, 'version': True, 'size': 10000})
    count = curr_results['hits']['total']['value']
    if count == 0:
        return "No record to archive"

    curr_results = curr_results['hits']['hits']

    if max_version is not None:

        '''To confirm whether there are changes in the dataset before and after modification. 
        If there are no changes, creation will not be allowed'''

        last_index_name = 'dataset_from_{}_v{}'.format(project_name, max_version)
        last_results = es_get_record(index=last_index_name)['hits']['hits']

        if len(last_results) == len(curr_results):
            last_results = sorted(last_results, key=lambda k: k['_source']['record_id'])
            curr_results = sorted(curr_results, key=lambda k: k['_source']['record_id'])

            flag = True
            for l, c in list(zip(last_results, curr_results)):
                if l['_source'] != c['_source']:
                    flag = False
                    break
            if flag == True:
                return 'The latest index is consistent with the pending merge index. Creation was unsuccessful'

    response = es.reindex(
        body={
            "source": {
                "index": record_index_name,
                "query": filter_query
            },
            "dest": {
                "index": index_name,
            }
        },
        refresh=True
    )
    '''
    Deprecated: When copying a record to a new index, the version number should still be preserved
    for i in es_get_record(index=index_name)['hits']['hits']:
        _id = i['_id']
        body = i['_source']
        query = {
            "query": {
                "term": {
                    "_id": _id
                }
            },
            "version": True
        }
        _old_version = es.search(index=record_index_name, body=query)['hits']['hits'][0]['_version']
        r = requests.put(ES_PROTOCOL_HOST_PORT + '/{}/_doc/{}/?version={}&version_type=external'.format(index_name, 
                                                                                                        _id,
                                                                                                        _old_version),
                         json=body)
    '''

    '''
    Add a task for saving and uploading data asynchronously.
    '''

    job_name = 'save_dataset_zip:' + archived_dataset_name
    job = scheduler.add_job(save_raw,
                            trigger='date',
                            name=job_name,
                            args=(archived_dataset_name,))

    job_name = 'save_dataset_parquet:' + archived_dataset_name
    job = scheduler.add_job(save_parquet,
                            trigger='date',
                            name=job_name,
                            args=(archived_dataset_name,))
    return 'ok'


class _DatasetInfoGetAPIResponseData(BaseModel):
    project_name: str
    name: str
    count: int
    ...


@router.get('/datasets')
def dataset_info(project_name: Optional[str] = None,
                 archived: Optional[bool] = None,
                 version: Optional[str] = None):
    if project_name is None and archived is None:
        return _get_archived_dataset() + _get_unarchived_dataset()
    else:
        if archived is not None:
            if archived:
                return _get_archived_dataset(project_name=project_name, version=version)
            else:
                return _get_unarchived_dataset(project_name=project_name)
        else:
            return _get_archived_dataset(project_name=project_name, version=version) \
                   + _get_unarchived_dataset(project_name=project_name)


def _get_archived_dataset_info(archived_dataset_name: str):
    index_name = archived_dataset_name
    project_name = '_'.join(index_name.split('_')[2:-1])

    query_body = {
        "size": 0,
        "aggs": {
            "unique_states": {
                "terms": {
                    "field": "state.keyword",
                    "size": 10000
                }
            }
        }
    }
    results = es.search(index=index_name, body=query_body)
    doc_count = results['hits']['total']['value']
    agg = {'project_name': project_name,
           'name': index_name,
           'count': doc_count,
           **{i.value: 0 for i in StatusEnum}}
    for bucket in results['aggregations']['unique_states']['buckets']:
        agg[bucket['key']] = bucket['doc_count']

    # labels
    results = es_get_record(project_name=agg['project_name'])['hits']['hits']

    labels = {}
    [[labels.update({j['name']: j['class']}) for j in i['_source']['bboxes']] for i in results]
    agg['labels'] = labels

    return agg


def _get_archived_dataset(project_name=None, version=None):
    # 已归档dataset的record
    all_indices = es.indices.get_alias().keys()
    dataset_index_names = [i for i in all_indices if i.startswith('dataset_from_')]
    agg_results = []

    for index_name in dataset_index_names:
        project_name_from_index_name = '_'.join(index_name.split('_')[2:-1])

        if project_name is not None and project_name_from_index_name != project_name:
            continue

        agg = _get_archived_dataset_info(archived_dataset_name=index_name)
        agg_results.append(agg)
    return agg_results


def _get_unarchived_dataset(project_name=None):
    query_body = {
        "size": 0,
        "aggs": {
            "unique_project": {
                "terms": {
                    "field": "project_name.keyword",
                    "size": 10000
                },
                "aggs": {
                    "unique_states": {
                        "terms": {
                            "field": "state.keyword",
                            "size": 10000
                        }
                    }
                }
            }
        }
    }
    results = es.search(index=record_index_name, body=query_body)

    agg_results = []
    for bucket in results['aggregations']['unique_project']['buckets']:
        agg = {'project_name': bucket['key'],
               'name': bucket['key'],
               'count': bucket['doc_count'], **{i.value: 0 for i in StatusEnum}}

        for sub_bucket in bucket['unique_states']['buckets']:
            agg[sub_bucket['key']] = sub_bucket['doc_count']

        if project_name is not None:
            if agg['project_name'] != project_name:
                continue

        # labels
        results = es_get_record(project_name=agg['project_name'])['hits']['hits']

        labels = {}
        try:
            [[labels.update({j['name']: j['class']}) for j in i['_source']['bboxes']] for i in results]
        except:
            print(1)
        agg['labels'] = labels

        agg_results.append(agg)
    return agg_results


def _zip_directory(directory_path, zip_file_path):
    try:
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as f:
            for file in glob.glob(os.path.join(directory_path, '**', "*"), recursive=True):
                arcname = os.path.relpath(file, directory_path)
                f.write(file, arcname=arcname)
    except Exception as e:
        print(f"compress failure：{e}")
