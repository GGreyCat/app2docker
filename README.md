# App2Docker

🚀 一键将 Java/Node.js 应用打包成 Docker 镜像

## ✨ 新架构特性

- **Vue 3 + Vite** 现代化前端框架
- **组件化开发** 代码清晰易维护
- **响应式设计** 适配各种屏幕
- **专业编辑器** 内置代码编辑器
- **项目类型分类** 模板按类型组织

## 📁 项目结构

```
jar2docker/
├── backend/                # Python 后端
│   ├── app.py             # 主应用
│   ├── config.py          # 配置管理
│   ├── handlers.py        # 请求处理器
│   └── utils.py           # 工具函数
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── components/    # Vue 组件
│   │   │   ├── BuildPanel.vue         # 构建面板
│   │   │   ├── ExportPanel.vue        # 导出面板
│   │   │   ├── ComposePanel.vue       # Compose 面板
│   │   │   ├── TemplatePanel.vue      # 模板管理
│   │   │   ├── BuildLogModal.vue      # 构建日志
│   │   │   └── ConfigModal.vue        # 配置对话框
│   │   ├── App.vue        # 主应用
│   │   └── main.js        # 入口文件
│   ├── package.json
│   └── vite.config.js     # Vite 配置
├── data/                  # 数据目录
│   ├── templates/         # 用户模板
│   │   ├── jar/          # Java 模板
│   │   └── nodejs/       # Node.js 模板
│   ├── uploads/          # 上传文件
│   ├── docker_build/     # 构建目录
│   └── exports/          # 导出目录
├── templates/            # 内置模板
│   ├── jar/             # Java 模板
│   └── nodejs/          # Node.js 模板
├── requirements.txt      # Python 依赖
├── dev.sh               # 开发启动脚本
└── README.md
```

## 🚀 快速开始

### 开发模式

1. **安装依赖**

```bash
# Python 依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
cd ..
```

2. **启动服务**

需要两个终端：

```bash
# 终端 1 - 后端
python backend/app.py

# 终端 2 - 前端
cd frontend
npm run dev
```

3. **访问应用**

- 前端开发服务器: http://localhost:3000
- 后端 API 服务器: http://localhost:8000

### 生产模式

1. **构建前端**

```bash
cd frontend
npm run build
cd ..
```

2. **启动后端**

```bash
python backend/app.py
```

前端构建产物会输出到 `dist/` 目录，后端会自动服务这些静态文件。

## 🎯 功能特性

### 1. 构建镜像
- 上传 JAR 或 Node.js 应用
- 选择预设 Dockerfile 模板
- 一键构建并可选推送

### 2. 导出镜像
- 导出已构建的 Docker 镜像
- 支持 tar 和 tar.gz 压缩格式

### 3. Docker Compose
- 解析 docker-compose.yml 文件
- 批量导出镜像
- 支持文件上传和文本输入

### 4. 模板管理
- 项目类型分类（jar/nodejs）
- 内置模板 + 用户自定义
- 内联编辑器
- 内置模板覆盖机制

## 🔧 配置说明

配置文件位于 `data/config.yml`

```yaml
docker:
  registry: docker.io
  registry_prefix: your-namespace
  username: your-username
  password: your-password
  expose_port: 8080
  default_push: false
```

## 📝 模板系统

模板按项目类型组织在子目录中：

- `templates/jar/` - Java 应用模板（内置，只读）
- `templates/nodejs/` - Node.js 应用模板（内置，只读）
- `data/templates/jar/` - Java 应用模板（用户自定义）
- `data/templates/nodejs/` - Node.js 应用模板（用户自定义）

用户自定义模板优先级高于内置模板。

## 🐳 Docker 部署

```bash
docker build -t app2docker .
docker run -d -p 8000:8000 -v /var/run/docker.sock:/var/run/docker.sock app2docker
```

## 📄 License

MIT

