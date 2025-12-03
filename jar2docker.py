# main.py
from http.server import HTTPServer
from handlers import Jar2DockerHandler
from utils import ensure_dirs

if __name__ == '__main__':
    ensure_dirs()
    port = 8000
    server = HTTPServer(('0.0.0.0', port), Jar2DockerHandler)

    print(f"🚀 Jar2Docker 服务已启动: http://localhost:{port}")
    print("📁 上传目录: data/uploads/")
    print("🏗️  构建目录: data/docker_build/")
    print("📋 内置模板: templates/ (只读)")
    print("📝 用户模板: data/templates/ (可读写)")
    print("⚙️  配置文件: data/config.yml")
    print("📦 导出目录: data/exports/")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        server.server_close()