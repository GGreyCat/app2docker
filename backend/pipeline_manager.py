# backend/pipeline_manager.py
"""流水线管理器 - 用于管理预配置的 Git 构建流水线（基于数据库）"""
import json
import uuid
import hmac
import hashlib
import threading
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from backend.database import get_db_session, init_db
from backend.models import Pipeline, PipelineTaskHistory

# 确保数据库已初始化
try:
    init_db()
except:
    pass


class PipelineManager:
    """流水线管理器（基于数据库）"""

    def __init__(self):
        self.lock = threading.RLock()

    def _to_dict(self, pipeline: Pipeline) -> Dict:
        """将数据库模型转换为字典"""
        if not pipeline:
            return None
        
        return {
            "pipeline_id": pipeline.pipeline_id,
            "name": pipeline.name,
            "description": pipeline.description,
            "enabled": pipeline.enabled,
            "git_url": pipeline.git_url,
            "branch": pipeline.branch,
            "sub_path": pipeline.sub_path,
            "project_type": pipeline.project_type,
            "template": pipeline.template,
            "image_name": pipeline.image_name,
            "tag": pipeline.tag,
            "push": pipeline.push,
            "push_registry": pipeline.push_registry,
            "template_params": pipeline.template_params or {},
            "use_project_dockerfile": pipeline.use_project_dockerfile,
            "dockerfile_name": pipeline.dockerfile_name,
            "webhook_token": pipeline.webhook_token,
            "webhook_secret": pipeline.webhook_secret,
            "webhook_branch_filter": pipeline.webhook_branch_filter,
            "webhook_use_push_branch": pipeline.webhook_use_push_branch,
            "branch_tag_mapping": pipeline.branch_tag_mapping or {},
            "source_id": pipeline.source_id,
            "selected_services": pipeline.selected_services or [],
            "service_push_config": pipeline.service_push_config or {},
            "service_template_params": pipeline.service_template_params or {},
            "push_mode": pipeline.push_mode,
            "resource_package_configs": pipeline.resource_package_configs or [],
            "cron_expression": pipeline.cron_expression,
            "next_run_time": pipeline.next_run_time.isoformat() if pipeline.next_run_time else None,
            "current_task_id": pipeline.current_task_id,
            "task_queue": pipeline.task_queue or [],
            "created_at": pipeline.created_at.isoformat() if pipeline.created_at else None,
            "updated_at": pipeline.updated_at.isoformat() if pipeline.updated_at else None,
            "last_triggered_at": pipeline.last_triggered_at.isoformat() if pipeline.last_triggered_at else None,
            "trigger_count": pipeline.trigger_count,
        }

    def create_pipeline(
        self,
        name: str,
        git_url: str,
        branch: str = None,
        project_type: str = "jar",
        template: str = None,
        image_name: str = None,
        tag: str = "latest",
        push: bool = False,
        push_registry: str = None,
        template_params: dict = None,
        sub_path: str = None,
        use_project_dockerfile: bool = True,
        dockerfile_name: str = "Dockerfile",
        webhook_secret: str = None,
        webhook_token: str = None,
        enabled: bool = True,
        description: str = "",
        cron_expression: str = None,
        webhook_branch_filter: bool = False,
        webhook_use_push_branch: bool = True,
        branch_tag_mapping: dict = None,
        source_id: str = None,
        selected_services: list = None,
        service_push_config: dict = None,
        service_template_params: dict = None,
        push_mode: str = "multi",
        resource_package_configs: list = None,
    ) -> str:
        """创建流水线配置"""
        pipeline_id = str(uuid.uuid4())

        # 生成 Webhook Token
        if not webhook_token:
            webhook_token = str(uuid.uuid4())
        
        # 检查 token 是否已被使用
        db = get_db_session()
        try:
            existing = db.query(Pipeline).filter(Pipeline.webhook_token == webhook_token).first()
            if existing:
                raise ValueError(f"Webhook Token '{webhook_token}' 已被其他流水线使用")
            
            # 如果没有提供 webhook_secret，生成一个
            if not webhook_secret:
                webhook_secret = str(uuid.uuid4())

            pipeline = Pipeline(
                pipeline_id=pipeline_id,
                name=name,
                description=description,
                enabled=enabled,
                git_url=git_url,
                branch=branch,
                sub_path=sub_path,
                project_type=project_type,
                template=template,
                image_name=image_name,
                tag=tag,
                push=push,
                push_registry=push_registry,
                template_params=template_params or {},
                use_project_dockerfile=use_project_dockerfile,
                dockerfile_name=dockerfile_name,
                webhook_token=webhook_token,
                webhook_secret=webhook_secret,
                webhook_branch_filter=webhook_branch_filter,
                webhook_use_push_branch=webhook_use_push_branch,
                branch_tag_mapping=branch_tag_mapping or {},
                source_id=source_id,
                selected_services=selected_services or [],
                service_push_config=service_push_config or {},
                service_template_params=service_template_params or {},
                push_mode=push_mode or "multi",
                resource_package_configs=resource_package_configs or [],
                cron_expression=cron_expression,
                task_queue=[],
            )
            
            db.add(pipeline)
            db.commit()
            return pipeline_id
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    def get_pipeline(self, pipeline_id: str) -> Optional[Dict]:
        """获取流水线配置"""
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.pipeline_id == pipeline_id).first()
            return self._to_dict(pipeline)
        finally:
            db.close()

    def get_pipeline_by_token(self, webhook_token: str) -> Optional[Dict]:
        """通过 Webhook Token 获取流水线配置"""
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.webhook_token == webhook_token).first()
            return self._to_dict(pipeline)
        finally:
            db.close()

    def list_pipelines(self, enabled: bool = None) -> List[Dict]:
        """列出所有流水线配置"""
        db = get_db_session()
        try:
            query = db.query(Pipeline)
            if enabled is not None:
                query = query.filter(Pipeline.enabled == enabled)
            pipelines = query.order_by(Pipeline.created_at.desc()).all()
            return [self._to_dict(p) for p in pipelines]
        finally:
            db.close()

    def update_pipeline(
        self,
        pipeline_id: str,
        name: str = None,
        git_url: str = None,
        branch: str = None,
        project_type: str = None,
        template: str = None,
        image_name: str = None,
        tag: str = None,
        push: bool = None,
        push_registry: str = None,
        template_params: dict = None,
        sub_path: str = None,
        use_project_dockerfile: bool = None,
        dockerfile_name: str = None,
        webhook_secret: str = None,
        webhook_token: str = None,
        enabled: bool = None,
        description: str = None,
        cron_expression: str = None,
        webhook_branch_filter: bool = None,
        webhook_use_push_branch: bool = None,
        branch_tag_mapping: dict = None,
        source_id: str = None,
        selected_services: list = None,
        service_push_config: dict = None,
        service_template_params: dict = None,
        push_mode: str = None,
        resource_package_configs: list = None,
    ) -> bool:
        """更新流水线配置"""
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.pipeline_id == pipeline_id).first()
            if not pipeline:
                return False

            # 更新字段
            if name is not None:
                pipeline.name = name
            if git_url is not None:
                pipeline.git_url = git_url
            if branch is not None:
                pipeline.branch = branch
            if project_type is not None:
                pipeline.project_type = project_type
            if template is not None:
                pipeline.template = template
            if image_name is not None:
                pipeline.image_name = image_name
            if tag is not None:
                pipeline.tag = tag
            if push is not None:
                pipeline.push = push
            if push_registry is not None:
                pipeline.push_registry = push_registry
            if template_params is not None:
                pipeline.template_params = template_params
            if sub_path is not None:
                pipeline.sub_path = sub_path
            if use_project_dockerfile is not None:
                pipeline.use_project_dockerfile = use_project_dockerfile
            if dockerfile_name is not None:
                pipeline.dockerfile_name = dockerfile_name
            if webhook_secret is not None:
                pipeline.webhook_secret = webhook_secret
            if webhook_token is not None:
                # 检查 token 是否已被其他流水线使用
                existing = db.query(Pipeline).filter(
                    Pipeline.webhook_token == webhook_token,
                    Pipeline.pipeline_id != pipeline_id
                ).first()
                if existing:
                    raise ValueError(f"Webhook Token '{webhook_token}' 已被其他流水线使用")
                pipeline.webhook_token = webhook_token
            if enabled is not None:
                pipeline.enabled = enabled
            if description is not None:
                pipeline.description = description
            if cron_expression is not None:
                pipeline.cron_expression = cron_expression
            if webhook_branch_filter is not None:
                pipeline.webhook_branch_filter = webhook_branch_filter
            if webhook_use_push_branch is not None:
                pipeline.webhook_use_push_branch = webhook_use_push_branch
            if branch_tag_mapping is not None:
                pipeline.branch_tag_mapping = branch_tag_mapping
            if source_id is not None:
                pipeline.source_id = source_id
            if selected_services is not None:
                pipeline.selected_services = selected_services
            if service_push_config is not None:
                pipeline.service_push_config = service_push_config
            if service_template_params is not None:
                pipeline.service_template_params = service_template_params
            if push_mode is not None:
                pipeline.push_mode = push_mode
            if resource_package_configs is not None:
                pipeline.resource_package_configs = resource_package_configs

            pipeline.updated_at = datetime.now()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    def delete_pipeline(self, pipeline_id: str) -> bool:
        """删除流水线配置"""
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.pipeline_id == pipeline_id).first()
            if not pipeline:
                return False
            
            db.delete(pipeline)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    def record_trigger(
        self,
        pipeline_id: str,
        task_id: str = None,
        trigger_source: str = "unknown",
        trigger_info: dict = None,
    ):
        """记录流水线触发"""
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.pipeline_id == pipeline_id).first()
            if not pipeline:
                return

            pipeline.last_triggered_at = datetime.now()
            pipeline.trigger_count = (pipeline.trigger_count or 0) + 1

            if task_id:
                pipeline.current_task_id = task_id
                
                # 记录到任务历史表
                history = PipelineTaskHistory(
                    pipeline_id=pipeline_id,
                    task_id=task_id,
                    trigger_source=trigger_source,
                    trigger_info=trigger_info or {},
                )
                db.add(history)
                
                # 限制历史记录数量（保留最近100条）
                history_count = db.query(PipelineTaskHistory).filter(
                    PipelineTaskHistory.pipeline_id == pipeline_id
                ).count()
                if history_count > 100:
                    # 删除最旧的记录
                    oldest = db.query(PipelineTaskHistory).filter(
                        PipelineTaskHistory.pipeline_id == pipeline_id
                    ).order_by(PipelineTaskHistory.triggered_at.asc()).first()
                    if oldest:
                        db.delete(oldest)

            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    def get_pipeline_running_task(self, pipeline_id: str) -> Optional[str]:
        """获取流水线当前正在执行的任务ID"""
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.pipeline_id == pipeline_id).first()
            return pipeline.current_task_id if pipeline else None
        finally:
            db.close()

    def unbind_task(self, pipeline_id: str):
        """解绑流水线的任务绑定"""
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.pipeline_id == pipeline_id).first()
            if pipeline:
                pipeline.current_task_id = None
                db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    def add_task_to_queue(self, pipeline_id: str, task_config: dict) -> str:
        """将任务添加到队列"""
        queue_id = str(uuid.uuid4())
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.pipeline_id == pipeline_id).first()
            if not pipeline:
                raise ValueError(f"流水线不存在: {pipeline_id}")
            
            queue = pipeline.task_queue or []
            queue.append({
                "queue_id": queue_id,
                "task_config": task_config,
                "created_at": datetime.now().isoformat(),
            })
            pipeline.task_queue = queue
            pipeline.last_triggered_at = datetime.now()
            db.commit()
            return queue_id
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    def get_queue_length(self, pipeline_id: str) -> int:
        """获取队列长度（从实际任务列表中统计）"""
        try:
            from backend.handlers import BuildManager
            
            build_manager = BuildManager()
            pending_tasks = build_manager.task_manager.list_tasks(status="pending")
            
            current_task_id = self.get_pipeline_running_task(pipeline_id)
            
            queue_count = 0
            for task in pending_tasks:
                task_config = task.get("task_config", {})
                task_pipeline_id = task_config.get("pipeline_id")
                task_id = task.get("task_id")
                
                if task_pipeline_id == pipeline_id and task_id != current_task_id:
                    queue_count += 1
            
            return queue_count
        except Exception as e:
            print(f"⚠️ 获取队列长度失败: {e}")
            import traceback
            traceback.print_exc()
            # 回退到使用字段的方式
            db = get_db_session()
            try:
                pipeline = db.query(Pipeline).filter(Pipeline.pipeline_id == pipeline_id).first()
                return len(pipeline.task_queue or []) if pipeline else 0
            finally:
                db.close()

    def get_next_queued_task(self, pipeline_id: str) -> Optional[dict]:
        """获取队列中的下一个任务配置"""
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.pipeline_id == pipeline_id).first()
            if pipeline and pipeline.task_queue:
                return pipeline.task_queue[0]
            return None
        finally:
            db.close()

    def remove_queued_task(self, pipeline_id: str, queue_id: str = None):
        """从队列中移除任务"""
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.pipeline_id == pipeline_id).first()
            if not pipeline or not pipeline.task_queue:
                return
            
            queue = pipeline.task_queue
            if queue_id:
                pipeline.task_queue = [q for q in queue if q.get("queue_id") != queue_id]
            else:
                pipeline.task_queue = queue[1:] if len(queue) > 1 else []
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    def find_pipeline_by_task(self, task_id: str) -> Optional[str]:
        """根据任务ID查找绑定的流水线ID"""
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.current_task_id == task_id).first()
            return pipeline.pipeline_id if pipeline else None
        finally:
            db.close()

    def check_debounce(self, pipeline_id: str, debounce_seconds: int = 5) -> bool:
        """检查是否在防抖时间内"""
        db = get_db_session()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.pipeline_id == pipeline_id).first()
            if not pipeline or not pipeline.last_triggered_at:
                return False
            
            elapsed = (datetime.now() - pipeline.last_triggered_at).total_seconds()
            return elapsed < debounce_seconds
        finally:
            db.close()

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
        signature_header: str = "sha256",
    ) -> bool:
        """验证 Webhook 签名"""
        try:
            if "=" in signature:
                algo, sig = signature.split("=", 1)
            else:
                algo = signature_header
                sig = signature

            if algo.lower() == "sha1":
                mac = hmac.new(secret.encode(), payload, hashlib.sha1)
            elif algo.lower() == "sha256":
                mac = hmac.new(secret.encode(), payload, hashlib.sha256)
            else:
                print(f"❌ 不支持的签名算法: {algo}")
                return False

            expected_sig = mac.hexdigest()
            result = hmac.compare_digest(expected_sig, sig)

            if not result:
                print(f"❌ 签名不匹配: expected={expected_sig[:8]}..., got={sig[:8]}..., algo={algo}")

            return result
        except Exception as e:
            print(f"❌ Webhook 签名验证异常: {e}")
            import traceback
            traceback.print_exc()
            return False
