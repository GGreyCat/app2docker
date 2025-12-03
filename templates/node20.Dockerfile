# Node.js 20 应用 Dockerfile
FROM node:20-alpine

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json（如果存在）
COPY package*.json ./

# 安装依赖
RUN npm install --production

# 复制应用文件
COPY . .

# 暴露端口
EXPOSE {{EXPOSE_PORT}}

# 启动应用（优先使用 npm start）
CMD ["npm", "start"]
