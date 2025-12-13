# backend/deploy_config_parser.py
"""
部署配置解析器
解析 deploy-config.yaml 格式，验证配置有效性，支持模板变量替换
"""
import yaml
import re
from typing import Dict, Any, List, Optional
from pathlib import Path


class DeployConfigParser:
    """部署配置解析器"""
    
    def __init__(self):
        """初始化解析器"""
        pass
    
    def parse_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析 YAML 配置文件
        
        Args:
            file_path: YAML 文件路径
        
        Returns:
            解析后的配置字典
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return self.parse_yaml_content(content)
    
    def parse_yaml_content(self, content: str) -> Dict[str, Any]:
        """
        解析 YAML 内容
        
        Args:
            content: YAML 内容字符串
        
        Returns:
            解析后的配置字典
        """
        config = yaml.safe_load(content)
        
        if not isinstance(config, dict):
            raise ValueError("配置必须是字典格式")
        
        # 验证配置结构
        self._validate_config(config)
        
        return config
    
    def _validate_config(self, config: Dict[str, Any]):
        """
        验证配置有效性
        
        Args:
            config: 配置字典
        
        Raises:
            ValueError: 配置无效时抛出异常
        """
        # 检查必需字段
        if "app" not in config:
            raise ValueError("配置中缺少 'app' 字段")
        
        app_config = config.get("app", {})
        if "name" not in app_config:
            raise ValueError("app.name 是必需的")
        
        # 检查 targets
        if "targets" not in config:
            raise ValueError("配置中缺少 'targets' 字段")
        
        targets = config.get("targets", [])
        if not isinstance(targets, list) or len(targets) == 0:
            raise ValueError("targets 必须是非空列表")
        
        # 验证每个 target
        for i, target in enumerate(targets):
            if not isinstance(target, dict):
                raise ValueError(f"targets[{i}] 必须是字典格式")
            
            if "name" not in target:
                raise ValueError(f"targets[{i}].name 是必需的")
            
            mode = target.get("mode", "agent")
            if mode not in ["ssh", "agent"]:
                raise ValueError(f"targets[{i}].mode 必须是 'ssh' 或 'agent'")
            
            # 验证 mode 对应的配置
            if mode == "agent":
                if "agent" not in target:
                    raise ValueError(f"targets[{i}].agent 是必需的（当 mode=agent 时）")
                
                agent_config = target.get("agent", {})
                if "name" not in agent_config:
                    raise ValueError(f"targets[{i}].agent.name 是必需的")
            elif mode == "ssh":
                if "host" not in target:
                    raise ValueError(f"targets[{i}].host 是必需的（当 mode=ssh 时）")
            
            # 验证 docker 配置
            if "docker" not in target:
                raise ValueError(f"targets[{i}].docker 是必需的")
            
            docker_config = target.get("docker", {})
            if "image_template" not in docker_config:
                raise ValueError(f"targets[{i}].docker.image_template 是必需的")
    
    def render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        渲染模板字符串（支持 {{ variable }} 格式）
        
        Args:
            template: 模板字符串
            context: 变量上下文
        
        Returns:
            渲染后的字符串
        """
        result = template
        
        # 查找所有模板变量 {{ variable }}
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        matches = re.findall(pattern, template)
        
        for var_name in matches:
            if var_name in context:
                value = str(context[var_name])
                placeholder = f"{{{{ {var_name} }}}}"
                result = result.replace(placeholder, value)
            else:
                # 如果变量不存在，保留原样（或可以抛出异常）
                pass
        
        return result
    
    def build_deploy_context(
        self,
        config: Dict[str, Any],
        registry: Optional[str] = None,
        tag: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        构建部署上下文（模板变量）
        
        Args:
            config: 部署配置
            registry: 镜像仓库地址（可选）
            tag: 镜像标签（可选）
            task_id: 任务ID（可选）
        
        Returns:
            上下文字典
        """
        app_config = config.get("app", {})
        
        context = {
            "app": {
                "name": app_config.get("name", ""),
                "repo": app_config.get("repo", ""),
            },
            "registry": registry or "docker.io",
            "tag": tag or "latest",
        }
        
        if task_id:
            context["task_id"] = task_id
        
        # 支持嵌套访问，如 {{ app.name }}
        # 将 app.name 展开为 app_name
        context["app_name"] = app_config.get("name", "")
        context["app_repo"] = app_config.get("repo", "")
        
        return context
    
    def render_target_config(
        self,
        target: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        渲染目标配置（替换模板变量）
        
        Args:
            target: 目标配置
            context: 模板变量上下文
        
        Returns:
            渲染后的目标配置
        """
        rendered = target.copy()
        
        # 渲染 docker 配置
        docker_config = target.get("docker", {}).copy()
        
        # 渲染 image_template
        if "image_template" in docker_config:
            docker_config["image_template"] = self.render_template(
                docker_config["image_template"],
                context
            )
        
        # 渲染 container_name
        if "container_name" in docker_config:
            docker_config["container_name"] = self.render_template(
                docker_config["container_name"],
                context
            )
        
        # 渲染环境变量
        if "env" in docker_config:
            env_vars = []
            for env_var in docker_config["env"]:
                rendered_env = self.render_template(env_var, context)
                env_vars.append(rendered_env)
            docker_config["env"] = env_vars
        
        rendered["docker"] = docker_config
        
        return rendered
    
    def get_targets_by_mode(
        self,
        config: Dict[str, Any],
        mode: str
    ) -> List[Dict[str, Any]]:
        """
        根据模式获取目标列表
        
        Args:
            config: 部署配置
            mode: 模式（"ssh" 或 "agent"）
        
        Returns:
            目标列表
        """
        targets = config.get("targets", [])
        return [t for t in targets if t.get("mode") == mode]
    
    def get_agent_targets(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取所有 Agent 模式的目标
        
        Args:
            config: 部署配置
        
        Returns:
            Agent 目标列表
        """
        return self.get_targets_by_mode(config, "agent")
    
    def get_ssh_targets(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取所有 SSH 模式的目标
        
        Args:
            config: 部署配置
        
        Returns:
            SSH 目标列表
        """
        return self.get_targets_by_mode(config, "ssh")

