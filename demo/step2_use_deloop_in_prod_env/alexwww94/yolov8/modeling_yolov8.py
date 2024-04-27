from transformers import PreTrainedModel
from .configuration_yolov8 import YOLOv8Config
from ultralytics import YOLO


class YOLOv8ForObjectDetection(PreTrainedModel):
    config_class = YOLOv8Config

    def __init__(self, config, *args, **kwargs):
        super().__init__(config)
        yolo_model_config = kwargs['yolo_model_config']
        yolo_model_config['verbose'] = True
        self.yolo_model = YOLO(**yolo_model_config)

    def forward(self, *args, **kwargs):
        return self.yolo_model(*args, **kwargs)

    def eval(self):
        self.yolo_model.model.eval()
