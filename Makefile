# 定义变量
IMAGE_NAME = signal_trading
TAG = latest


# 打包 Docker 镜像
docker:
	docker build -t $(IMAGE_NAME):$(TAG) .
