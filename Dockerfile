# 使用官方的 Python 运行时作为基础镜像
FROM python:3.11-slim

# 定义 TINI_VERSION 环境变量
ENV TINI_VERSION=v0.19.0

# 安装 wget 和 tini
RUN apt-get update && apt-get install -y wget ca-certificates \
  && cd /tmp \
  && wget -q -O tini https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini \
  && chmod +x tini \
  && mv tini /usr/local/bin/tini \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# 设置容器内的工作目录
WORKDIR /usr/src/app

# 将 requirements.txt 文件复制到容器中
COPY requirements.txt ./

# 安装 requirements.txt 中列出的所有依赖包
RUN pip install --no-cache-dir -r requirements.txt

# 将当前目录的内容复制到容器中的 /usr/src/app 目录
COPY . .
RUN rm -rf /app/test


# 当容器启动时运行 signal_trading.py
CMD ["/sbin/tini", "--"]