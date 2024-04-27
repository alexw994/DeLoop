from transformers import PretrainedConfig


class YOLOv8Config(PretrainedConfig):
    model_type = 'yolov8'

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
