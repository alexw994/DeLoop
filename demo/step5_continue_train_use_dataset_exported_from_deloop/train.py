import io
import os
from transformers import AutoModelForObjectDetection
import datasets
from deloop import DeloopClient
from deloop.client.tools import convert_hf_dataset_to_yolo
import yaml

project_name = 'example_project'

client = DeloopClient(host_port='http://10.39.88.175:9601',
                      project_name=project_name,
                      project_type='ObjectDetection',
                      infer_model='yolov8',
                      max_workers=4)

dataset_name = 'dataset_from_example_project_v1'

save_dir = os.path.join(os.path.dirname(__file__), dataset_name)
dataset = client.download_dataset(dataset_name, format='hf', save_dir=save_dir)

dataset = dataset['train']
names = dataset.features['objects'].feature['category'].names

splited_dataset = dataset.train_test_split(test_size=0.2)
train_dataset = splited_dataset['train']
test_dataset = splited_dataset['test']

model = AutoModelForObjectDetection.from_pretrained('./alexwww94/yolov8', trust_remote_code=True,
                                                    yolo_model_config={"model": 'yolov8n'})

data = convert_hf_dataset_to_yolo(save_dir=save_dir, names=names, train=train_dataset, val=test_dataset)

'''
Convert huggingface dataset to yolo format
example: https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/datasets/coco128.yaml
'''
import os

os.environ['WANDB_MODE'] = 'offline'
model.yolo_model.train(data=data)
