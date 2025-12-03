# App2Docker 新功能说明

## 新增功能

### 1. 支持多种文件格式上传
- ✅ JAR 文件（`.jar`）
- ✅ ZIP 压缩包（`.zip`）
- ✅ TAR 压缩包（`.tar`）
- ✅ TAR.GZ 压缩包（`.tar.gz`, `.tgz`）

### 2. 支持 Node.js 项目
- ✅ Node.js 20 版本
- ✅ 自动识别 package.json
- ✅ 自动安装依赖（npm install）
- ✅ 支持 npm start 启动

### 3. 项目类型选择
用户可以在前端选择项目类型：
- **Java 应用（JAR）**：支持 JAR 文件或包含 JAR 的压缩包
- **Node.js 应用**：支持包含 Node.js 项目的压缩包

### 4. 智能模板匹配
- 选择 Java 项目时，自动过滤显示 Java 相关模板（dragonwell8, dragonwell17 等）
- 选择 Node.js 项目时，自动显示 Node.js 模板（node20）

## 使用方法

### 上传 Java 应用（JAR）
1. 选择项目类型：**Java 应用（JAR）**
2. 上传 JAR 文件或包含 JAR 的压缩包
3. 选择合适的 Java 模板（如 dragonwell17）
4. 填写镜像名称和标签
5. 点击"开始构建"

### 上传 Node.js 应用
1. 选择项目类型：**Node.js 应用**
2. 将 Node.js 项目打包成 ZIP 或 TAR 格式
   ```bash
   # 示例：打包 Node.js 项目
   zip -r myapp.zip myapp/
   # 或
   tar -czf myapp.tar.gz myapp/
   ```
3. 上传压缩包
4. 系统会自动选择 node20 模板
5. 填写镜像名称和标签
6. 点击"开始构建"

## 技术实现

### 后端改进
- 添加了 `zipfile` 和 `tarfile` 模块支持
- 实现了自动解压功能（`extract_archive`）
- 支持项目类型参数（`project_type`）
- 改进了 `generate_image_name` 函数，支持多种文件扩展名

### 前端改进
- 添加项目类型选择器
- 动态更新文件上传接受的格式
- 智能过滤模板列表
- 改进用户提示信息

### Node.js Dockerfile 模板
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE {{EXPOSE_PORT}}
CMD ["npm", "start"]
```

## 注意事项

1. **Node.js 项目结构要求**：
   - 必须包含 `package.json` 文件
   - 建议在 package.json 中定义 `start` 脚本
   - 确保项目根目录下有主入口文件

2. **压缩包要求**：
   - 压缩包内应包含完整的项目结构
   - 避免在压缩包外层添加多余的文件夹

3. **端口配置**：
   - 可以在"Docker 配置"中设置默认暴露端口
   - Node.js 应用需要监听配置的端口

## 示例项目结构

### Node.js 项目示例
```
myapp/
├── package.json
├── package-lock.json
├── index.js
├── src/
│   └── ...
└── node_modules/ (可选，会自动安装)
```

### package.json 示例
```json
{
  "name": "myapp",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.18.0"
  }
}
```

