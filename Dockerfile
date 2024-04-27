FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime
RUN apt update && apt install -y libgl1-mesa-glx libglib2.0-0

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt -i http://10.39.88.175:3141/root/custom/+simple/ --trusted-host 10.39.88.175
COPY src/deloop /deloop

WORKDIR /deloop
CMD ["python", "server/app.py"]
