import os
from pathlib import Path
import minio

ROOT = Path(__file__).parents[3]
import sys

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

DELOOP_HOST_PORT = os.environ.get('DELOOP_HOST_PORT', '0.0.0.0:9601')
DELOOP_DATA_DIR = os.environ.get('DELOOP_DATA', os.path.join(ROOT, 'deloop', 'data'))

if not os.path.exists(DELOOP_DATA_DIR):
    os.makedirs(DELOOP_DATA_DIR)

MINIO_HOST_PORT = os.environ.get('MINIO_HOST_PORT', 'minio:9000')

MINIO_BUCKET_NAME = os.environ.get('MINIO_BUCKET_NAME', 'default')
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'ROOTNAME')
MINIO_SECURE = os.environ.get('MINIO_SECURE', 'CHANGEME123')

ES_PROTOCOL_HOST_PORT = os.environ.get('ES_PROTOCOL_HOST_PORT', 'http://elasticsearch:9200')
ES_RECORD_INDEX_NAME = os.environ.get('ES_RECORD_INDEX_NAME', 'record')

LABELTSTUDIO_HOST_PORT = os.environ.get('LABELTSTUDIO_HOST_PORT', 'http://labelstudio:8080')


def init_storage():
    storage = minio.Minio(MINIO_HOST_PORT,
                          access_key=MINIO_ACCESS_KEY,
                          secret_key=MINIO_SECURE,
                          secure=False)

    # Make the bucket if it doesn't exist.
    found = storage.bucket_exists(MINIO_BUCKET_NAME)
    if not found:
        storage.make_bucket(MINIO_BUCKET_NAME)
        print("Created bucket", MINIO_BUCKET_NAME)
        policy_template = '''{{
          "Statement": [
           {{
            "Action": [
             "s3:GetBucketLocation",
             "s3:ListBucket",
             "s3:ListBucketMultipartUploads"
            ],
            "Effect": "Allow",
            "Principal": {{
             "AWS": "*"
            }},
            "Resource": "arn:aws:s3:::{MINIO_BUCKENT_NAME}",
            "Sid": ""
           }},
           {{
            "Action": [
             "s3:AbortMultipartUpload",
             "s3:DeleteObject",
             "s3:GetObject",
             "s3:ListMultipartUploadParts",
             "s3:PutObject"
            ],
            "Effect": "Allow",
            "Principal": {{
             "AWS": "*"
            }},
            "Resource": "arn:aws:s3:::{MINIO_BUCKENT_NAME}/*",
            "Sid": ""
           }}
          ],
          "Version": "2012-10-17"
         }}'''

        policy = policy_template.format(MINIO_BUCKENT_NAME=MINIO_BUCKET_NAME)

        storage.set_bucket_policy(bucket_name=MINIO_BUCKET_NAME, policy=policy)
    else:
        print("Bucket", MINIO_BUCKET_NAME, "already exists")
    return storage


def init_es():
    ''' ES '''
    from elasticsearch import Elasticsearch

    es = Elasticsearch(ES_PROTOCOL_HOST_PORT)
    if not es.indices.exists(index=ES_RECORD_INDEX_NAME):
        es.indices.create(index=ES_RECORD_INDEX_NAME)
    return es


def init_sql():
    '''SQLAlchemy'''
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from deloop.schema import Base

    sqlengine = create_engine(url='sqlite:///' + os.path.join(DELOOP_DATA_DIR, 'system.sqlite3'), echo=True)
    Session = sessionmaker(bind=sqlengine)

    Base.metadata.create_all(sqlengine)
    return Session


def init_aps():
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    from apscheduler.schedulers.background import BackgroundScheduler

    jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///' + os.path.join(DELOOP_DATA_DIR, 'jobs.sqlite3'))}
    scheduler = BackgroundScheduler(jobstores=jobstores)
    scheduler.start()
    return scheduler


def ls():
    from label_studio_sdk.client import ClientCredentials, Client

    class LSClient(Client):
        def __init__(self, *args, **kwargs):
            self.credentials = kwargs.get('credentials')
            super().__init__(*args, **kwargs)

        def get_api_key(self, credentials: ClientCredentials):
            login_url = self.get_url("/user/login")
            # Retrieve and set the CSRF token first
            self.session.get(login_url)
            csrf_token = self.session.cookies.get('csrftoken', None)
            login_data = dict(**credentials.dict(), csrfmiddlewaretoken=csrf_token)
            self.session.post(
                login_url,
                data=login_data,
                headers=dict(Referer=self.url),
                cookies=self.session.cookies,
            ).raise_for_status()
            api_key = (
                self.session.get(self.get_url("/api/current-user/token"))
                .json()
                .get("token")
            )
            return api_key

        @property
        def login_request_args(self):
            csrf_token = self.session.cookies.get('csrftoken', None)
            cookie = {'csrftoken': csrf_token,
                      'sessionid': self.session.cookies.get('sessionid', None)}

            return {'url': self.get_url("/user/login"),
                    'data': dict(email=self.credentials.email, password=self.credentials.password,
                                 csrfmiddlewaretoken=csrf_token),
                    'headers': {},
                    'cookie': cookie}

    email = 'admin@foo.com'
    password = 'foo123'

    credentials = ClientCredentials(email=email, password=password)
    ls_client = LSClient(url=LABELTSTUDIO_HOST_PORT, credentials=credentials)
    return ls_client


bucket_name = MINIO_BUCKET_NAME
record_index_name = ES_RECORD_INDEX_NAME

storage = init_storage()
es = init_es()
Session = init_sql()
scheduler = init_aps()
ls_client = ls()
