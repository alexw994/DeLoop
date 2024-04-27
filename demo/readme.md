## demo

### Start Deloop Service

Start deloop as described on the homepage

### Use Deloop in Product Environment

```
pip install deloop
```

```python
from deloop.client import DeloopClient

deloop = DeloopClient(host_port='http://localhost:9601',
                      project_name='example_project',
                      project_type='ObjectDetection',
                      infer_model='yolov8',
                      max_workers=4)
```

Upload the image before each analysis, and upload the detection results after the analysis, similar to the reference
code in the demo.

Deloop will send data using multithreading, so there's no need to worry about affecting production. However, since this
project is in an unstable stage, it's important to capture exceptions as much as possible.

### Simulate Request

Here, requests sent by users to the production environment are simulated.

### Explore in Deloop

The backend service is used to calculate the uncertainty of each image (by analyzing the impact of different levels of
noise on the analysis results) to determine whether the image should be manually annotated.

Deloop provides a quick way to bind an active learning backend. Follow the example code to build your own backend
service.

After all this, deloop can continuously collect request data from the production environment.

You can find the entrance to Oracle labeling on the homepage, which embeds Label Studio. Here, you can annotate and
export datasets on the datasets page.

### Continue train use dataset exported from deloop

Support exporting datasets in HuggingFace format. You can use `alexwww94/yolov8` to convert this format for training.