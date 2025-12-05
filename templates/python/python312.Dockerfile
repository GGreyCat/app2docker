# Python 3.12 Web 应用 Dockerfile
# 适用于 Flask、Django 等 Python Web 应用
# 使用阿里云镜像源加速下载

FROM alibaba-cloud-linux-3-registry.cn-hangzhou.cr.aliyuncs.com/alinux3/python:3.12.0

# 设置时区为上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（根据需要添加）
RUN yum install -y net-tools && \
    yum clean all && \
    rm -rf /var/cache/yum

# 复制 requirements.txt（如果存在）
COPY requirements.txt* ./

# 安装 Python 依赖
RUN if [ -f requirements.txt ]; then \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/; \
    fi

# 复制应用文件
COPY . .

# 暴露端口
EXPOSE {{EXPOSE_PORT:8000}}

# 启动应用
# 默认使用 gunicorn，如果使用其他方式请修改
# Flask: CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:{{EXPOSE_PORT:8000}}", "app:app"]
# Django: CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:{{EXPOSE_PORT:8000}}", "project.wsgi:application"]
CMD ["python", "app.py"]

