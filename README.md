![](./deloop.png)

English| [中文](./README-ch.md)

## Introduction

Deloop is a bridge between production and development environments, connected after deployment. It efficiently filters
and collects data after each model deployment and constructs datasets that are most effective for training the next
version of the model based on active learning. It can also be used as a component of MLOPS.

## Getting Started

It is strongly recommended to install using docker-compose.

### Installing docker-compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

```bash
sudo chmod +x /usr/local/bin/docker-compose
```

### Cloning this Project

```bash
cd ~ && sudo git clone https://github.com/alexw994/deloop.git
```

### Starting

```bash
cd ~/deloop && sudo docker-compose up -d
```

### Homepage

```
http://xxx.xxx.xxx.xxx:8000/deloop
```

### Client pip Installation

```
cd ~/deloop/src && pip install . --inplace
```

## API Documentation

```
http://xxx.xxx.xxx.xxx:9601/redoc
```

## Demo

Refer to [demo](./demo)

## Features

- In the production environment, upload each request using the deloop client.
- Store data using Minio and Elasticsearch.
- Manually annotate data with high uncertainty based on active learning, automatically annotate data with low
  uncertainty (currently only supports Object Detection).
- Use Label Studio for annotation.
- Export datasets in Hugging Face format for training.

## Goals

- [ ] Support text data.
- [ ] Support multimodal data.
- [ ] Automatic computation embedding.
- [ ] Optimal dataset construction based on graphs.
- [ ] Introduce more active learning methods.

## References

- [Label Studio](https://github.com/heartexlabs/label-studio)
- [Weave](https://github.com/qingwave/weave)