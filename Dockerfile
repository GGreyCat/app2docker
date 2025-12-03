# 多阶段构建：前端 + 后端

# ============ 阶段 1: 构建前端 ============
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci

# 复制前端源代码
COPY frontend/ ./

# 构建生产版本
RUN npm run build

# ============ 阶段 2: Python 后端 ============
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 从第一阶段复制构建好的前端文件
COPY --from=frontend-builder /frontend/dist ./dist

# 复制内置模板
COPY templates/ ./templates/

# 说明：
# - templates/ 目录包含内置模板（按项目类型分类）
# - data/ 目录在运行时通过卷映射提供
# - favicon.ico 已包含在前端构建产物（dist/）中
# 
# 运行容器：
# docker run -d \
#   -v $(pwd)/data:/app/data \
#   -v /var/run/docker.sock:/var/run/docker.sock \
#   -p 8000:8000 \
#   app2docker

# 暴露服务端口
EXPOSE 8000

# 启动后端服务（后端会服务前端构建文件）
CMD ["python", "backend/app.py"]
