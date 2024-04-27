import os
import urllib.parse

from fastapi import Request, APIRouter, Response, Header
from PIL import Image
import io
import socket
import requests
from pydantic import Field
from .utils import sql_read_only_trans
from . import scheduler, Session, aps
from deloop.schema import *
from deloop.al_backend.backend.base import BaseDetecionALBackend

router = APIRouter(prefix='/api/v1/de', tags=['al_backend'])


class _ALBackendPostAPIInputData(BaseModel):
    api: str
    headers: Union[None, str, dict] = Field(None)
    project_name: str

    #
    referer: Optional[str] = Field(None)


def check_connection(ip_address, port=None):
    port = int(port) if port else 80
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Create a socket and attempt to connect to the IP address and port
        sock.settimeout(2)  # Set the connection timeout to 2 seconds
        sock.connect((ip_address, port))
        return True
    except Exception as e:
        return False
    finally:
        sock.close()


@router.post('/al_backend')
def al_backend_post(data: _ALBackendPostAPIInputData, request: Request):
    api = data.api
    headers = data.headers
    project_name = data.project_name

    # test api ip is avaliable
    if not check_connection(*urllib.parse.urlparse(api).netloc.split(':')):
        return Response('Api ip and port is not avaliable', status_code=400)

    with Session.begin() as sqlsession:
        project = sqlsession.query(ProjectOrm).filter_by(name=project_name).all()[0]
        project.al_backend_config = {'api': api, 'headers': headers}
        project.has_al_backend = True
        sqlsession.commit()

    # After adding the backend, start the scheduled job
    project = sql_read_only_trans(ProjectOrm, ProjectModel, name=project_name)[0]

    aps.add_schedule_func_http_request_job(project_name=project.name, time_interval=project.time_interval)

    return 'ok'


class __ALBackendHealthPostAPIInputData(BaseModel):
    project_name: str
    image_url: str


@router.post('/al_backend/health')
def al_backend_health(data: __ALBackendHealthPostAPIInputData):
    project_name = data.project_name
    image_url = data.image_url

    image = Image.open(io.BytesIO(requests.get(image_url).content))

    projects = sql_read_only_trans(ProjectOrm, ProjectModel, name=project_name)
    if len(projects) == 0:
        return Response('project not found', status_code=404)
    else:
        project = projects[0]
        al_backend_config = project.al_backend_config
        al_backend = BaseDetecionALBackend(project_name=project.name, config=al_backend_config)
        al_backend.infer(image)
        return Response('ok', status_code=200)
