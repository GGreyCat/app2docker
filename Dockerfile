# 使用阿里云的 Python 3.11 轻量级镜像作为基础
FROM alibaba-cloud-linux-3-registry.cn-hangzhou.cr.aliyuncs.com/alinux3/python:3.11.1

# 设置工作目录
WORKDIR /app

# 安装系统依赖（如果需要 curl 或其他工具，可在此添加）
# RUN apt-get update && apt-get install -y \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
# 可选：为 pip 配置阿里云镜像源以加速下载
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件到容器
COPY . .

# 暴露服务端口（默认 8000）
EXPOSE 8000

# 容器启动时运行主程序
CMD ["python", "jar2docker.py"]



