#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import io
import sys
import yaml
import json
import shutil
import hashlib
import tempfile
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from pathlib import Path

# ============= 配置 =============
CONFIG_FILE = "config.yml"
UPLOAD_DIR = "uploads"
BUILD_DIR = "docker_build"
TEMPLATES_DIR = "templates"
INDEX_FILE = "index.html"

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# ============= 工具函数 =============
def get_safe_filename(filename):
    """生成安全的文件名"""
    name = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    return name[:255]

def generate_image_name(jar_path):
    """根据 JAR 文件名智能生成镜像名"""
    jar_name = os.path.basename(jar_path)
    if jar_name.endswith('.jar'):
        jar_name = jar_name[:-4]
    # 移除版本号等，保留主名
    parts = re.split(r'[-_.]', jar_name)
    if len(parts) > 1:
        # 取第一个有意义的部分
        base_name = parts[0].lower()
        if not base_name or len(base_name) < 2:
            base_name = "myapp"
        return f"{base_name}/{jar_name.lower()}"
    return f"myapp/{jar_name.lower()}"

# ============= HTTP 处理器 =============
class Jar2DockerHandler(BaseHTTPRequestHandler):
    server_version = "Jar2Docker/1.0"

    def _send_json(self, code, data):
        """发送 JSON 响应"""
        try:
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
        except Exception as e:
            print(f"❌ 发送 JSON 响应失败: {e}")

    def _send_html(self, content):
        """发送 HTML 响应"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            if isinstance(content, str):
                content = content.encode('utf-8')
            self.wfile.write(content)
        except Exception as e:
            print(f"❌ 发送 HTML 响应失败: {e}")

    def _send_file(self, filepath, content_type='application/octet-stream'):
        """发送文件"""
        try:
            if not os.path.exists(filepath):
                self.send_error(404, "File not found")
                return False

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(os.path.getsize(filepath)))
            self.end_headers()

            with open(filepath, 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
            return True
        except Exception as e:
            print(f"❌ 发送文件 {filepath} 失败: {e}")
            return False

    def load_config(self):
        """加载配置，不冲掉其他部分"""
        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "docker": {
                    "registry": "docker.io",
                    "registry_prefix": "",
                    "default_push": False,
                    "expose_port": 8080
                }
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            print(f"🆕 配置文件 {CONFIG_FILE} 不存在，已创建默认配置")
            return default_config

        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"⚠️ 读取配置失败，使用默认配置: {e}")
            config = {}

        if 'docker' not in config:
            config['docker'] = {
                "registry": "docker.io",
                "registry_prefix": "",
                "default_push": False,
                "expose_port": 8080
            }
            # 保存回去
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return config

    def do_GET(self):
        """处理 GET 请求"""
        path = self.path.split('?')[0]

        if path == '/get-config':
            self.handle_get_config()
        elif path == '/list-templates':
            self.handle_list_templates()
        elif path == '/':
            self.serve_index()
        elif path == '/index.html':
            self.serve_index()
        elif path.startswith('/static/') or path.startswith('/img.'):
            # 简单静态文件服务
            filepath = path.lstrip('/')
            if os.path.exists(filepath):
                content_type = 'image/png' if filepath.endswith('.png') else 'text/css'
                self._send_file(filepath, content_type)
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def serve_index(self):
        """返回 index.html"""
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            self._send_html(content)
        else:
            self.send_error(404, "index.html not found")

    def handle_get_config(self):
        """获取当前配置"""
        try:
            config = self.load_config()
            docker_config = config.get('docker', {})
            self._send_json(200, {"docker": docker_config})
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._send_json(500, {"error": f"获取配置失败: {str(e)}"})

    def handle_list_templates(self):
        """列出模板"""
        try:
            if not os.path.exists(TEMPLATES_DIR):
                templates = []
            else:
                templates = [
                    f.replace('.Dockerfile', '')
                    for f in os.listdir(TEMPLATES_DIR)
                    if f.endswith('.Dockerfile')
                ]
            self._send_json(200, {"templates": templates})
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._send_json(500, {"error": "获取模板列表失败"})

    def do_POST(self):
        """处理 POST 请求"""
        if self.path == '/upload':
            self.handle_upload()
        elif self.path == '/save-config':
            self.handle_save_config()
        elif self.path == '/suggest-image-name':  # ← 新增
            self.handle_suggest_image_name()  # ← 新增
        else:
            self.send_error(404)

    def handle_save_config(self):
        """保存全局配置，只更新 docker 部分"""
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)

            boundary = self.headers['Content-Type'].split("boundary=")[1].encode()
            parts = body.split(b'--' + boundary)
            form_data = {}

            for part in parts[1:-1]:
                if b'\r\n\r\n' in part:
                    header_end = part.find(b'\r\n\r\n')
                    headers = part[:header_end].decode('utf-8', errors='ignore')
                    data = part[header_end + 4:].rstrip(b'\r\n')

                    if 'name="' in headers:
                        try:
                            field_name = headers.split('name="')[1].split('"')[0]
                            form_data[field_name] = data.decode('utf-8', errors='ignore')
                        except:
                            continue

            new_docker_config = {
                "registry": form_data.get("registry", "docker.io").strip(),
                "registry_prefix": form_data.get("registry_prefix", "").strip().rstrip('/'),
                "default_push": (form_data.get("default_push") == "on"),
                "expose_port": int(form_data.get("expose_port", "8080")) if form_data.get("expose_port", "").isdigit() else 8080
            }

            full_config = {}
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        full_config = yaml.safe_load(f) or {}
                except:
                    pass

            if 'docker' not in full_config:
                full_config['docker'] = {}
            full_config['docker'].update(new_docker_config)

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(full_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            print(f"✅ 配置已更新: {full_config['docker']}")
            self._send_json(200, {
                "message": "Docker 配置保存成功！",
                "docker_config": full_config['docker']
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            clean_error_msg = re.sub(r'[\x00-\x1F\x7F]', ' ', error_msg).strip()
            self._send_json(500, {"error": f"保存配置失败: {clean_error_msg}"})

    def handle_suggest_image_name(self):
        """根据上传的 JAR 文件名，返回建议的镜像名"""
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)

            boundary = self.headers['Content-Type'].split("boundary=")[1].encode()
            parts = body.split(b'--' + boundary)

            jar_filename = None
            for part in parts[1:-1]:
                if b'\r\n\r\n' in part and b'name="jar_file"' in part and b'filename="' in part:
                    headers = part[:part.find(b'\r\n\r\n')].decode('utf-8', errors='ignore')
                    match = re.search(r'filename="(.+?)"', headers)
                    if match:
                        jar_filename = match.group(1)
                        break

            if not jar_filename:
                self._send_json(400, {"error": "未找到 JAR 文件"})
                return

            # 生成建议镜像名
            suggested_name = generate_image_name(jar_filename)  # 注意：这里传的是文件名，不是路径！

            self._send_json(200, {
                "suggested_imagename": suggested_name
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            self._send_json(500, {"error": f"生成镜像名失败: {str(e)}"})

    def handle_upload(self):
        """处理上传和构建"""
        try:
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self.send_error(400, "Content-Type must be multipart/form-data")
                return

            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)

            boundary = content_type.split("boundary=")[1].encode()
            parts = body.split(b'--' + boundary)

            jar_file = None
            custom_dockerfile = None
            imagename = "myapp/demo"
            tag = "latest"
            template_name = ""
            push_image = False

            for part in parts[1:-1]:
                if b'\r\n\r\n' in part:
                    header_end = part.find(b'\r\n\r\n')
                    headers = part[:header_end].decode('utf-8', errors='ignore')
                    data = part[header_end + 4:].rstrip(b'\r\n')

                    if 'name="jar_file"' in headers and b'filename="' in part:
                        filename = re.search(r'filename="(.+?)"', headers)
                        if filename:
                            original_name = filename.group(1)
                            safe_name = get_safe_filename(original_name)
                            jar_path = os.path.join(UPLOAD_DIR, safe_name)
                            with open(jar_path, 'wb') as f:
                                f.write(data)
                            jar_file = jar_path
                            # 自动生成镜像名
                            imagename = generate_image_name(jar_path)

                    elif 'name="custom_dockerfile"' in headers and b'filename="' in part:
                        filename = re.search(r'filename="(.+?)"', headers)
                        if filename:
                            safe_name = get_safe_filename(filename.group(1))
                            df_path = os.path.join(BUILD_DIR, "Dockerfile.custom")
                            with open(df_path, 'wb') as f:
                                f.write(data)
                            custom_dockerfile = df_path

                    elif 'name="template"' in headers:
                        template_name = data.decode('utf-8', errors='ignore').strip()

                    elif 'name="imagename"' in headers:
                        imagename = data.decode('utf-8', errors='ignore').strip() or imagename

                    elif 'name="tag"' in headers:
                        tag = data.decode('utf-8', errors='ignore').strip() or "latest"

                    elif 'name="push_image"' in headers:
                        push_image = True

            if not jar_file:
                self.send_error(400, "JAR file is required")
                return

            # 准备构建目录
            build_id = hashlib.md5(str(jar_file).encode()).hexdigest()[:8]
            build_path = os.path.join(BUILD_DIR, build_id)
            os.makedirs(build_path, exist_ok=True)

            # 复制 JAR
            jar_dest = os.path.join(build_path, os.path.basename(jar_file))
            shutil.copy2(jar_file, jar_dest)

            # 准备 Dockerfile
            dockerfile_path = os.path.join(build_path, "Dockerfile")
            config = self.load_config()
            expose_port = config['docker']['expose_port']

            if custom_dockerfile:
                shutil.copy2(custom_dockerfile, dockerfile_path)
            elif template_name:
                template_file = os.path.join(TEMPLATES_DIR, template_name + ".Dockerfile")
                if os.path.exists(template_file):
                    with open(template_file, 'r', encoding='utf-8') as src, open(dockerfile_path, 'w', encoding='utf-8') as dst:
                        content = src.read()
                        content = content.replace("${EXPOSE_PORT}", str(expose_port))
                        dst.write(content)
                else:
                    self.send_error(400, f"Template {template_name} not found")
                    return
            else:
                # 默认模板
                with open(dockerfile_path, 'w', encoding='utf-8') as f:
                    f.write(f"""FROM openjdk:11-jre-slim
WORKDIR /app
COPY . .
EXPOSE {expose_port}
ENTRYPOINT ["java", "-jar", "{os.path.basename(jar_file)}"]
""")

            # 构建镜像
            full_imagename = imagename
            prefix = config['docker']['registry_prefix'].strip()
            if prefix:
                full_imagename = f"{prefix}/{full_imagename}".lstrip('/')

            image_tag = f"{full_imagename}:{tag}"

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('X-Accel-Buffering', 'no')  # 禁用 nginx 缓冲
            self.end_headers()

            # 实时输出构建日志
            def build_and_stream():
                try:
                    cmd = ['docker', 'build', '-t', image_tag, build_path]
                    proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )

                    for line in proc.stdout:
                        try:
                            self.wfile.write(line.encode('utf-8'))
                            self.wfile.flush()
                        except:
                            break

                    proc.wait()

                    if proc.returncode == 0:
                        self.wfile.write(f"\n✅ 镜像构建成功: {image_tag}\n".encode('utf-8'))

                        # 推送镜像（如果勾选）
                        if push_image:
                            self.wfile.write(f"\n📤 正在推送镜像到仓库...\n".encode('utf-8'))
                            push_cmd = ['docker', 'push', image_tag]
                            push_proc = subprocess.Popen(
                                push_cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                bufsize=1
                            )
                            for line in push_proc.stdout:
                                try:
                                    self.wfile.write(line.encode('utf-8'))
                                    self.wfile.flush()
                                except:
                                    break
                            push_proc.wait()
                            if push_proc.returncode == 0:
                                self.wfile.write(f"\n✅ 镜像推送成功！\n".encode('utf-8'))
                            else:
                                self.wfile.write(f"\n❌ 镜像推送失败！\n".encode('utf-8'))
                    else:
                        self.wfile.write(f"\n❌ 镜像构建失败！\n".encode('utf-8'))

                except Exception as e:
                    self.wfile.write(f"\n❌ 构建异常: {str(e)}\n".encode('utf-8'))

            # 在线程中执行构建，避免阻塞
            thread = threading.Thread(target=build_and_stream)
            thread.daemon = True
            thread.start()
            thread.join(timeout=600)  # 最多等待10分钟

        except Exception as e:
            import traceback
            traceback.print_exc()
            if not self.wfile.closed:
                self.wfile.write(f"❌ 上传处理失败: {str(e)}\n".encode('utf-8'))

    def log_message(self, format, *args):
        """简化日志输出"""
        return

# ============= 启动服务器 =============
if __name__ == '__main__':
    port = 8000
    server = HTTPServer(('0.0.0.0', port), Jar2DockerHandler)
    print(f"🚀 Jar2Docker 服务已启动: http://localhost:{port}")
    print(f"📁 上传目录: {UPLOAD_DIR}")
    print(f"🏗️  构建目录: {BUILD_DIR}")
    print(f"📋 模板目录: {TEMPLATES_DIR}")
    print(f"⚙️  配置文件: {CONFIG_FILE}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        server.server_close()