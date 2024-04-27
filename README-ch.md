![](./deloop.png)

中文| [English](./README.md)

## 简介

deloop是一个连通后部署阶段的生产环境和开发环境的桥梁。它可以在每次模型部署后，高效地过滤和收集数据，并基于主动学习，构建对于下个版本模型训练最有效的数据集。
同时也可以作为MLOPS的其中一组件使用

## 启动

强烈建议使用docker-compose安装

### 安装docker-compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

```bash
sudo chmod +x /usr/local/bin/docker-compose
```

### clone本项目

```bash
cd ~ && sudo clone https://github.com/alexw994/deloop.git
```

### 启动

```bash
cd ~/deloop && sudo docker-compose up -d
```

### 主页

```
http://xxx.xxx.xxx.xxx:8000/deloop
```

### 客户端pip安装

```
cd ~/deloop/src && pip install . --inplace
```

## API文档

```
http://xxx.xxx.xxx.xxx:9601/redoc
```

## Demo

参考 [demo](./demo)

## 功能

- 在生产环境中，使用deloop client上传每次请求
- 使用minio和elasticsearch存储数据
- 基于主动学习，不确定度高的数据人工标注，不确定性低的自动标注（目前仅支持Objection Detection）
- 使用labelstudio标注
- 导出huggingface格式的数据集供训练

## 目标

- [ ] 支持文本数据
- [ ] 支持多模态
- [ ] 自动计算嵌入
- [ ] 基于图的最优数据集构建
- [ ] 引入更多主动学习方法

## 参考

- [label studio](https://github.com/heartexlabs/label-studio)
- [weave](https://github.com/qingwave/weave)