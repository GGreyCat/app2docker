# backend/routes.py
"""FastAPI 路由定义"""
import os
from typing import Optional
from fastapi import (
    APIRouter,
    File,
    UploadFile,
    Form,
    Query,
    HTTPException,
    Request,
    Response,
    Body,
)
from fastapi.responses import (
    JSONResponse,
    PlainTextResponse,
    FileResponse,
    StreamingResponse,
)
from pydantic import BaseModel

from backend.handlers import (
    BuildManager,
    load_config,
    save_config,
    generate_image_name,
    get_all_templates,
    BUILTIN_TEMPLATES_DIR,
    USER_TEMPLATES_DIR,
    EXPORT_DIR,
    natural_sort_key,
    client,
    DOCKER_AVAILABLE,
)
from backend.utils import get_safe_filename
from backend.auth import authenticate, verify_token
from datetime import datetime
import json

router = APIRouter()


# === Pydantic 模型 ===
class LoginRequest(BaseModel):
    username: str
    password: str


class TemplateRequest(BaseModel):
    name: str
    content: str
    project_type: str = "jar"
    original_name: str = None  # 用于更新时的原始名称
    old_project_type: str = None  # 用于项目类型变更


class ParseComposeRequest(BaseModel):
    content: str


class DeleteTemplateRequest(BaseModel):
    name: str
    project_type: str = "jar"


# === 认证相关 ===
@router.post("/login")
async def login(request: LoginRequest):
    """用户登录"""
    result = authenticate(request.username, request.password)
    if result.get("success"):
        return JSONResponse(result)
    raise HTTPException(status_code=401, detail=result.get("error", "用户名或密码错误"))


@router.post("/logout")
async def logout():
    """用户登出"""
    return JSONResponse({"success": True, "message": "已登出"})


# === 配置相关 ===
@router.get("/get-config")
async def get_config():
    """获取配置"""
    try:
        config = load_config()
        docker_config = config.get("docker", {})
        return JSONResponse({"docker": docker_config})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/save-config")
async def save_config_route(
    registry: str = Form("docker.io"),
    registry_prefix: str = Form(""),
    default_push: str = Form("false"),  # 改为 str 类型，前端发送的是字符串
    username: str = Form(""),
    password: str = Form(""),
    expose_port: str = Form("8080"),  # 改为 str 类型以便更好地处理
):
    """保存 Docker 配置"""
    try:
        # 转换布尔值
        default_push_bool = default_push.lower() in ("true", "1", "on", "yes")

        # 转换端口号
        try:
            expose_port_int = int(expose_port)
        except (ValueError, TypeError):
            expose_port_int = 8080

        config = load_config()
        new_docker_config = {
            "registry": registry.strip(),
            "registry_prefix": registry_prefix.strip().rstrip("/"),
            "default_push": default_push_bool,
            "username": username.strip(),
            "password": password.strip(),
            "expose_port": expose_port_int,
        }

        if "docker" not in config:
            config["docker"] = {}
        config["docker"].update(new_docker_config)

        save_config(config)

        print(
            f"✅ 配置已保存: {json.dumps(config['docker'], ensure_ascii=False, indent=2)}"
        )
        return JSONResponse(
            {
                "message": "Docker 配置保存成功！",
                "docker": config["docker"],  # 改为 docker 以与 get-config 保持一致
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


# === 构建相关 ===
@router.post("/upload")
async def upload_file(
    app_file: UploadFile = File(...),
    imagename: str = Form(...),
    tag: str = Form("latest"),
    template: str = Form(...),
    project_type: str = Form("jar"),
    push: str = Form("off"),
):
    """上传文件并开始构建"""
    try:
        if not app_file or not app_file.filename:
            raise HTTPException(status_code=400, detail="未上传文件")

        # 读取文件内容
        file_data = await app_file.read()

        # 调用构建管理器
        manager = BuildManager()
        build_id = manager.start_build(
            file_data=file_data,
            image_name=imagename,
            tag=tag,
            should_push=(push == "on"),
            selected_template=template,
            original_filename=app_file.filename,
            project_type=project_type,
        )

        return JSONResponse(
            {
                "build_id": build_id,
                "message": "构建任务已启动，请通过日志查看进度",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")


@router.get("/get-logs")
async def get_logs(build_id: str = Query(...)):
    """获取构建日志"""
    try:
        manager = BuildManager()
        logs = manager.get_logs(build_id)
        log_text = "".join(logs) if isinstance(logs, list) else str(logs)
        return PlainTextResponse(log_text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")


# === 镜像相关 ===
@router.post("/suggest-image-name")
async def suggest_image_name(jar_file: UploadFile = File(...)):
    """根据文件名建议镜像名称"""
    try:
        app_filename = jar_file.filename
        if not app_filename:
            raise HTTPException(status_code=400, detail="未找到文件")

        config = load_config()
        docker_config = config.get("docker", {})
        base_name = docker_config.get("registry_prefix", "")
        suggested_name = generate_image_name(base_name, app_filename)

        return JSONResponse({"suggested_imagename": suggested_name})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成镜像名失败: {str(e)}")


@router.get("/export-image")
async def export_image(
    image: str = Query(..., description="镜像名称"),
    tag: str = Query("latest", description="镜像标签"),
    compress: str = Query("none", description="压缩格式: none, gzip"),
):
    """导出镜像"""
    try:
        import shutil
        import gzip

        if not DOCKER_AVAILABLE:
            raise HTTPException(
                status_code=503, detail="Docker 服务不可用，无法导出镜像"
            )

        image_name = image.strip()
        tag_name = tag.strip()

        if not image_name:
            raise HTTPException(status_code=400, detail="缺少 image 参数")

        # 如果镜像名包含标签，分离出来
        if ":" in image_name and not tag:
            image_name, inferred_tag = image_name.rsplit(":", 1)
            if inferred_tag:
                tag_name = inferred_tag

        full_tag = f"{image_name}:{tag_name}"
        compress_enabled = compress.lower() in ("gzip", "gz", "tgz", "1", "true", "yes")

        # 获取认证信息
        config = load_config()
        docker_cfg = config.get("docker", {})
        username = docker_cfg.get("username")
        password = docker_cfg.get("password")
        auth_config = None
        if username and password:
            auth_config = {"username": username, "password": password}

        # 尝试拉取镜像
        try:
            pull_kwargs = {
                "repository": image_name,
                "tag": tag_name,
                "stream": True,
                "decode": True,
            }
            if auth_config:
                pull_kwargs["auth_config"] = auth_config

            pull_stream = client.api.pull(**pull_kwargs)
            for chunk in pull_stream:
                if "error" in chunk:
                    raise RuntimeError(chunk["error"])

            # 确认镜像存在
            client.images.get(full_tag)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"无法获取镜像: {str(e)}")

        # 创建导出目录
        os.makedirs(EXPORT_DIR, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        safe_base = get_safe_filename(image_name.replace("/", "_") or "image")
        tar_filename = f"{safe_base}-{tag_name}-{timestamp}.tar"
        tar_path = os.path.join(EXPORT_DIR, tar_filename)

        # 导出镜像
        image_stream = client.api.get_image(full_tag)
        with open(tar_path, "wb") as f:
            for chunk in image_stream:
                f.write(chunk)

        final_path = tar_path
        download_name = tar_filename
        content_type = "application/x-tar"

        # 如果需要压缩
        if compress_enabled:
            final_path = f"{tar_path}.gz"
            download_name = os.path.basename(final_path)
            content_type = "application/gzip"
            with open(tar_path, "rb") as src, gzip.open(final_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            os.remove(tar_path)

        # 返回文件并在发送后删除
        return FileResponse(
            final_path,
            media_type=content_type,
            filename=download_name,
            background=lambda: (
                os.remove(final_path) if os.path.exists(final_path) else None
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"导出镜像失败: {str(e)}")


# === Compose 相关 ===
@router.post("/parse-compose")
async def parse_compose(request: ParseComposeRequest):
    """解析 Docker Compose 文件"""
    try:
        import yaml

        compose_doc = yaml.safe_load(request.content)

        # 提取镜像列表
        images = []
        if isinstance(compose_doc, dict):
            services = compose_doc.get("services", {})
            for service_name, service_config in services.items():
                if isinstance(service_config, dict):
                    image = service_config.get("image", "")
                    if image:
                        images.append({"service": service_name, "image": image})

        return JSONResponse({"images": images})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析 Compose 文件失败: {str(e)}")


# === 模板相关 ===
@router.get("/list-templates")
async def list_templates():
    """列出所有可用模板"""
    try:
        templates = get_all_templates()
        details = []

        for name, info in templates.items():
            try:
                stat = os.stat(info["path"])
                details.append(
                    {
                        "name": name,
                        "filename": os.path.basename(info["path"]),
                        "size": stat.st_size,
                        "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": info["type"],
                        "project_type": info.get("project_type", "jar"),
                        "editable": info["type"] == "user",
                    }
                )
            except OSError:
                continue

        details.sort(key=lambda item: natural_sort_key(item["name"]))
        return JSONResponse(details)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.get("/templates")
async def get_template(name: Optional[str] = Query(None)):
    """获取模板详情或列表"""
    try:
        if name:
            # 获取单个模板内容
            templates = get_all_templates()
            if name not in templates:
                raise HTTPException(status_code=404, detail="模板不存在")

            template_path = templates[name]["path"]
            if not os.path.exists(template_path):
                raise HTTPException(status_code=404, detail="模板文件不存在")

            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()

            return JSONResponse(
                {
                    "name": name,
                    "content": content,
                    "type": templates[name]["type"],
                    "project_type": templates[name].get("project_type", "jar"),
                }
            )
        else:
            # 返回模板列表（前端兼容格式）
            templates = get_all_templates()
            details = []

            for name, info in templates.items():
                try:
                    stat = os.stat(info["path"])
                    details.append(
                        {
                            "name": name,
                            "filename": os.path.basename(info["path"]),
                            "size": stat.st_size,
                            "updated_at": datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                            "type": info["type"],
                            "project_type": info.get("project_type", "jar"),
                            "editable": info["type"] == "user",
                        }
                    )
                except OSError:
                    continue

            details.sort(key=lambda item: natural_sort_key(item["name"]))

            # 返回前端期望的格式
            return JSONResponse(
                {
                    "items": details,
                    "total": len(details),
                    "builtin": sum(1 for d in details if d["type"] == "builtin"),
                    "user": sum(1 for d in details if d["type"] == "user"),
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")


@router.post("/templates")
async def create_template(request: TemplateRequest):
    """创建新模板"""
    try:
        name = request.name
        content = request.content
        project_type = request.project_type

        # 验证模板名称
        if not name or ".." in name or "/" in name:
            raise HTTPException(status_code=400, detail="非法模板名称")

        # 确定保存路径
        template_dir = os.path.join(USER_TEMPLATES_DIR, project_type)
        os.makedirs(template_dir, exist_ok=True)

        template_path = os.path.join(template_dir, f"{name}.Dockerfile")

        if os.path.exists(template_path):
            raise HTTPException(status_code=400, detail="模板已存在")

        # 保存模板
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(content)

        return JSONResponse({"message": "模板创建成功", "name": name})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")


@router.put("/templates")
async def update_template(request: TemplateRequest):
    """更新模板"""
    try:
        name = request.name
        content = request.content
        original_name = request.original_name or name  # 支持重命名

        templates = get_all_templates()

        # 如果是重命名，检查原始模板是否存在
        if original_name not in templates:
            raise HTTPException(status_code=404, detail="模板不存在")

        template_info = templates[original_name]

        if template_info["type"] == "builtin":
            raise HTTPException(status_code=403, detail="不能修改内置模板")

        old_path = template_info["path"]

        # 如果项目类型改变或名称改变，需要移动/重命名文件
        if (
            request.old_project_type
            and request.old_project_type != request.project_type
        ):
            # 项目类型改变，需要移动文件
            new_dir = os.path.join(USER_TEMPLATES_DIR, request.project_type)
            os.makedirs(new_dir, exist_ok=True)
            new_path = os.path.join(new_dir, f"{name}.Dockerfile")

            # 保存到新位置
            with open(new_path, "w", encoding="utf-8") as f:
                f.write(content)

            # 删除旧文件
            if os.path.exists(old_path):
                os.remove(old_path)
        elif original_name != name:
            # 仅重命名
            new_path = os.path.join(os.path.dirname(old_path), f"{name}.Dockerfile")
            with open(new_path, "w", encoding="utf-8") as f:
                f.write(content)
            if os.path.exists(old_path) and old_path != new_path:
                os.remove(old_path)
        else:
            # 仅更新内容
            with open(old_path, "w", encoding="utf-8") as f:
                f.write(content)

        return JSONResponse({"message": "模板更新成功", "name": name})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新模板失败: {str(e)}")


@router.delete("/templates")
async def delete_template(request: DeleteTemplateRequest):
    """删除模板"""
    try:
        name = request.name
        templates = get_all_templates()

        if name not in templates:
            raise HTTPException(status_code=404, detail="模板不存在")

        template_info = templates[name]

        if template_info["type"] == "builtin":
            raise HTTPException(status_code=403, detail="不能删除内置模板")

        template_path = template_info["path"]

        # 删除文件
        if os.path.exists(template_path):
            os.remove(template_path)

        return JSONResponse({"message": "模板删除成功", "name": name})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除模板失败: {str(e)}")
