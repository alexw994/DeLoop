import os.path
import sys
import tempfile
from pathlib import Path
import socket

import datasets

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from deloop import image_util
from concurrent.futures import ThreadPoolExecutor
from .tools import create_server
import httpx
import zipfile


def _post(url, data):
    headers = {
        'Content-Type': 'application/json'
    }

    response = httpx.request('post', url, json=data, headers=headers)
    return response


def _get(url, data=None):
    response = httpx.request('get', url)
    return response


def default_callback(task):
    print(task.result())


def get_ip_address():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an external IP address (e.g., public DNS server)
        sock.connect(('8.8.8.8', 80))
        # Get the current socket address
        ip_address = sock.getsockname()[0]
    finally:
        # Close the socket
        sock.close()
    return ip_address


class DeloopClient():
    def __init__(self, host_port, project_name=None, infer_model=None, project_type='ObjectDetection',
                 al_backend_config=None, max_workers=4):
        self.host_port = host_port
        self.tpool = ThreadPoolExecutor(max_workers=max_workers)
        self.tlist = []
        self.project_name = project_name
        self.infer_model = infer_model
        self.project_type = project_type
        self.al_backend_config = al_backend_config

        if project_name and not self.remote_project_exits(project_name):
            self.create_project(project_name,
                                infer_model=self.infer_model,
                                type=self.project_type,
                                al_backend_config=self.al_backend_config)

    def set_project_name(self, project_name):
        self.project_name = project_name
        if not self.remote_project_exits(project_name):
            self.create_project(project_name,
                                infer_model=self.infer_model,
                                type=self.project_type,
                                al_backend_config=self.al_backend_config)

    def upload_image(self, image_name, image, project_name=None):
        project_name = project_name or self.project_name
        assert project_name

        if project_name and not self.remote_project_exits(project_name):
            self.create_project(project_name,
                                infer_model=self.infer_model,
                                type=self.project_type,
                                al_backend_config=self.al_backend_config)

        image_base64 = image_util.image_to_base64(image)
        data = {'project_name': project_name,
                'image_name': image_name,
                'image_base64': image_base64}

        self.make_async_request(_post, self.host_port + '/api/v1/de/images', data)

    def upload_record(self, image_name, bboxes, project_name=None):
        project_name = project_name or self.project_name
        assert project_name

        if project_name and not self.remote_project_exits(project_name):
            self.create_project(project_name,
                                infer_model=self.infer_model,
                                type=self.project_type,
                                al_backend_config=self.al_backend_config)

        data = {'bboxes': bboxes,
                'project_name': project_name,
                'image_name': image_name}
        self.make_async_request(_post, self.host_port + '/api/v1/de/records', data)

    def remote_project_exits(self, project_name):
        response = self.make_request(_get, self.host_port + '/api/v1/de/projects')
        assert response.status_code == 200

        print(response.json())
        project_names = [i['name'] for i in response.json()]
        return project_name in project_names

    def create_project(self, project_name,
                       infer_model,
                       type,
                       trigger_type=None,
                       method=None,
                       time_interval=None,
                       al_backend_config=None):
        response = self.make_request(_get, self.host_port + '/api/v1/de/projects')
        assert response.status_code == 200

        print(response.json())
        if project_name not in [i['name'] for i in response.json()]:
            data = {'name': project_name,
                    'infer_model': infer_model,
                    'type': type,
                    'trigger_type': trigger_type,
                    'method': method,
                    'has_al_backend': True if al_backend_config else False,
                    'time_interval': time_interval,
                    'al_backend_config': al_backend_config}

            response = self.make_request(_post, self.host_port + '/api/v1/de/projects', data)
            assert response.status_code == 200

            assert response.status_code == 200
        else:
            return 'project already exists'

    def make_async_request(self, function, url, data, callback=None):
        task = self.tpool.submit(function, url, data)
        if callback is None:
            callback = default_callback
        task.add_done_callback(callback)

    def make_request(self, function, url, data=None):
        response = function(url, data)
        return response

    def add_al_backend(self, local_server_host,
                       local_server_port, local_server_endpoint,
                       local_server_headers=None, project_name=None, manual_server_address=None):

        """
        封装一个方法，创建一个local_server，并注册到deloop的服务端，使得deloop的服务端能通过http调用client注册的这个方法
        :param local_server_host:
        :param local_server_port:
        :param local_server_endpoint:
        :param local_server_headers:
        :return:
        """
        if local_server_headers is None:
            local_server_headers = {}

        project_name = project_name or self.project_name
        assert project_name

        server_ip = local_server_host
        if manual_server_address:
            server_ip = manual_server_address
        else:
            try:
                server_ip = get_ip_address()
            except:
                pass

        api = 'http://' + server_ip + ':' + str(local_server_port) + local_server_endpoint

        data = {'project_name': project_name,
                'api': api,
                'headers': local_server_headers}
        # upload al_backend
        response = self.make_request(_post, self.host_port + '/api/v1/de/al_backend', data)
        assert response.status_code == 200

        # return a decorator
        return create_server(local_server_host, local_server_port, local_server_endpoint)

    def archived_datasets(self):
        response = self.make_request(_get, self.host_port + '/api/v1/de/datasets?archived=1')
        return response.json()

    def download_dataset(self, dataset_name, format, save_dir):
        assert format in ['hf', 'raw']
        save_dir = os.path.join(save_dir, format)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        response = self.make_request(_post, self.host_port + '/api/v1/de/datasets/download',
                                     {'archived_dataset_name': dataset_name, 'format': format})
        dataset_download_url = response.json()
        assert isinstance(dataset_download_url, str)

        response = self.make_request(_get, dataset_download_url)
        # download
        with tempfile.TemporaryFile() as tmpf:
            tmpf.write(response.read())

            with zipfile.ZipFile(tmpf) as zf:
                zf.extractall(save_dir)

        if format == 'hf':
            dataset = datasets.load_dataset(save_dir)
            return dataset
        else:
            return save_dir
