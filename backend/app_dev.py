#!/usr/bin/env python3
# backend/app_dev.py - 开发模式启动脚本（支持热重载）
import os
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class ServerRestartHandler(FileSystemEventHandler):
    """文件变化处理器"""

    def __init__(self, restart_callback):
        self.restart_callback = restart_callback
        self.last_restart = 0
        self.debounce_seconds = 1  # 防抖延迟

    def on_modified(self, event):
        # 只监控 Python 文件
        if event.src_path.endswith(".py"):
            current_time = time.time()
            # 防抖：避免频繁重启
            if current_time - self.last_restart > self.debounce_seconds:
                print(f"\n🔄 检测到文件变化: {event.src_path}")
                print("⏳ 正在重启服务器...\n")
                self.last_restart = current_time
                self.restart_callback()


class DevServer:
    """开发服务器（支持热重载）"""

    def __init__(self):
        self.process = None
        self.observer = None
        self.backend_dir = os.path.join(project_root, "backend")

    def start_server(self):
        """启动服务器进程"""
        if self.process:
            self.stop_server()

        # 使用 uvicorn 启动 FastAPI 服务器
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.app:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--reload",
            ],
            cwd=project_root,
            env={**os.environ, "PYTHONPATH": project_root},
        )

    def stop_server(self):
        """停止服务器进程"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def restart_server(self):
        """重启服务器"""
        self.start_server()

    def start_watching(self):
        """启动文件监控"""
        event_handler = ServerRestartHandler(self.restart_server)
        self.observer = Observer()

        # 监控 backend 目录
        self.observer.schedule(event_handler, self.backend_dir, recursive=True)

        # 也监控项目根目录的配置文件
        root_handler = ServerRestartHandler(self.restart_server)
        # 注意：只监控 .py 文件，不监控 data 目录
        for root, dirs, files in os.walk(project_root):
            # 跳过不需要监控的目录
            dirs[:] = [
                d
                for d in dirs
                if d
                not in [
                    "data",
                    "frontend",
                    "node_modules",
                    "__pycache__",
                    ".git",
                    "dist",
                    "docker_build",
                    "exports",
                    "uploads",
                ]
            ]

        self.observer.start()
        print("👁️  文件监控已激活（监控 backend/ 目录）")

    def run(self):
        """运行开发服务器"""
        print("\n" + "=" * 60)
        print("🔥 开发模式（支持热重载）")
        print("=" * 60)
        print("📝 修改任何 .py 文件都会自动重启服务器")
        print("=" * 60 + "\n")

        try:
            self.start_watching()
            self.start_server()

            print("\n" + "=" * 60)
            print("✅ 服务器已启动 + 文件监控已激活")
            print("=" * 60 + "\n")

            # 保持运行
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("👋 正在关闭服务器...")
            print("=" * 60)
            self.stop_server()
            if self.observer:
                self.observer.stop()
                self.observer.join()
            print("\n✅ 服务器已完全停止\n")


if __name__ == "__main__":
    dev_server = DevServer()
    dev_server.run()
