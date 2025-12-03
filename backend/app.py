# backend/app.py
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import HTTPServer
from backend.handlers import Jar2DockerHandler
from backend.utils import ensure_dirs

if __name__ == "__main__":
    ensure_dirs()
    port = 8000
    server = HTTPServer(("0.0.0.0", port), Jar2DockerHandler)

    print("=" * 60)
    print("🚀 App2Docker 服务已启动")
    print("=" * 60)
    print(f"📍 后端 API: http://localhost:{port}")
    print(f"📍 前端开发: http://localhost:3000 (需单独启动)")
    print("")
    print("📁 目录结构:")
    print("  ├── 上传: data/uploads/")
    print("  ├── 构建: data/docker_build/")
    print("  ├── 导出: data/exports/")
    print("  ├── 内置模板: templates/jar, templates/nodejs (只读)")
    print("  └── 用户模板: data/templates/jar, data/templates/nodejs (可读写)")
    print("")
    print("⚙️  配置文件: data/config.yml")
    print("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        server.server_close()
