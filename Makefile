# 定义变量
IMAGE_NAME = signal_trading
TAG = latest


build:
	pyinstaller signal_trading.spec

clean:
	rm -rf build dist

# 打包 Docker 镜像
docker:
	docker build -t $(IMAGE_NAME):$(TAG) .

