# 静态网站 Dockerfile (Nginx 简化版)
# 适用于简单的静态网站部署

# 使用阿里云 Nginx 镜像
FROM registry.cn-shanghai.aliyuncs.com/numen/nginx:latest

# 设置时区为上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# 复制静态文件到 nginx 默认目录
COPY . /usr/share/nginx/html/


# 打印目录查看
RUN ls -la /usr/share/nginx/html/

# 暴露端口
EXPOSE {{EXPOSE_PORT:80}}

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]

