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
# 包含 templates/ 目录（内置模板）和所有代码文件
# data/ 目录通过 .dockerignore 排除，使用 Docker 卷映射
COPY . .

# 说明：
# - templates/ 目录包含内置模板，打包在镜像中（只读）
# - data/ 目录在运行时通过卷映射提供，包含用户数据和自定义模板
# 
# 运行容器时映射 data 目录：
# docker run -v $(pwd)/data:/app/data -v /var/run/docker.sock:/var/run/docker.sock \
#            -p 8000:8000 jar2docker

# 暴露服务端口（默认 8000）
EXPOSE 8000

# 容器启动时运行主程序
CMD ["python", "jar2docker.py"]



