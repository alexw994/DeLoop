import json
from deloop import DeloopClient
from transformers import AutoModelForObjectDetection
import socket

model = AutoModelForObjectDetection.from_pretrained('../step2_use_deloop_in_prod_env/alexwww94/yolov8',
                                                    trust_remote_code=True,
                                                    yolo_model_config={"model": 'yolov8n'})

project_name = 'example_project'
client = DeloopClient(host_port='http://10.39.88.175:9601',
                      project_name=project_name,
                      project_type='ObjectDetection',
                      infer_model='yolov8',
                      max_workers=4)

al_backend_host = '0.0.0.0'
al_backend_port = 6007
al_backend_url = '/al_backend/infer'


@client.add_al_backend(al_backend_host,
                       al_backend_port,
                       al_backend_url,
                       project_name=project_name,
                       manual_server_address='10.39.88.175')
def al_backend_infer(image):
    results = model(image, imgsz=640)  # reduce size=320 for faster inference
    results = [json.loads(i.tojson()) for i in results][0]
    return results


if __name__ == '__main__':
    al_backend_infer()
