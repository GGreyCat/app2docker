# host_manager.py
"""
主机资源管理模块
用于管理远程主机SSH连接和Docker编译支持配置
"""
import os
import json
import uuid
import paramiko
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# 主机配置存储目录
HOST_CONFIG_DIR = "data/hosts"
# 主机配置元数据文件
METADATA_FILE = os.path.join(HOST_CONFIG_DIR, "metadata.json")


class HostManager:
    """主机资源管理器"""
    
    _instance = None
    _lock = None
    
    def __new__(cls):
        if cls._instance is None:
            import threading
            cls._instance = super().__new__(cls)
            cls._lock = threading.Lock()
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        """初始化主机管理器"""
        # 确保目录存在
        os.makedirs(HOST_CONFIG_DIR, exist_ok=True)
        # 加载元数据
        self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """加载主机元数据"""
        if os.path.exists(METADATA_FILE):
            try:
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 加载主机元数据失败: {e}")
                return {}
        return {}
    
    def _save_metadata(self, metadata: Dict):
        """保存主机元数据"""
        try:
            with open(METADATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存主机元数据失败: {e}")
            raise
    
    def test_ssh_connection(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        key_password: Optional[str] = None,
        timeout: int = 10
    ) -> Dict:
        """
        测试SSH连接
        
        Args:
            host: 主机地址
            port: SSH端口
            username: 用户名
            password: 密码（如果使用密码认证）
            private_key: SSH私钥内容（如果使用密钥认证）
            key_password: 私钥密码（如果私钥有密码）
            timeout: 连接超时时间（秒）
        
        Returns:
            测试结果字典，包含success、message、docker_available等信息
        """
        ssh_client = None
        try:
            # 创建SSH客户端
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 准备认证方式
            auth_methods = []
            
            # 如果提供了私钥，优先使用密钥认证
            if private_key:
                try:
                    import io
                    key_file = io.StringIO(private_key)
                    # 尝试不同的密钥类型
                    for key_class in [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.DSSKey]:
                        try:
                            key_file.seek(0)
                            if key_password:
                                pkey = key_class.from_private_key(key_file, password=key_password)
                            else:
                                pkey = key_class.from_private_key(key_file)
                            auth_methods.append(pkey)
                            break
                        except:
                            continue
                    key_file.close()
                except Exception as e:
                    print(f"⚠️ 解析SSH私钥失败: {e}")
            
            # 如果提供了密码，添加密码认证
            if password:
                auth_methods.append(password)
            
            if not auth_methods:
                return {
                    "success": False,
                    "message": "请提供密码或SSH私钥",
                    "docker_available": False
                }
            
            # 连接SSH
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": username,
                "timeout": timeout,
            }
            
            if isinstance(auth_methods[0], (paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.DSSKey)):
                connect_kwargs["pkey"] = auth_methods[0]
            else:
                connect_kwargs["password"] = auth_methods[0]
            
            ssh_client.connect(**connect_kwargs)
            
            # 测试Docker是否可用
            docker_available = False
            docker_version = None
            try:
                stdin, stdout, stderr = ssh_client.exec_command("docker --version", timeout=5)
                exit_status = stdout.channel.recv_exit_status()
                if exit_status == 0:
                    docker_version = stdout.read().decode('utf-8').strip()
                    docker_available = True
            except Exception as e:
                print(f"⚠️ 检查Docker失败: {e}")
            
            return {
                "success": True,
                "message": "SSH连接成功",
                "docker_available": docker_available,
                "docker_version": docker_version
            }
            
        except paramiko.AuthenticationException:
            return {
                "success": False,
                "message": "SSH认证失败，请检查用户名和密码/密钥",
                "docker_available": False
            }
        except paramiko.SSHException as e:
            return {
                "success": False,
                "message": f"SSH连接错误: {str(e)}",
                "docker_available": False
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接失败: {str(e)}",
                "docker_available": False
            }
        finally:
            if ssh_client:
                try:
                    ssh_client.close()
                except:
                    pass
    
    def add_host(
        self,
        name: str,
        host: str,
        port: int = 22,
        username: str = "",
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        key_password: Optional[str] = None,
        docker_enabled: bool = False,
        description: str = ""
    ) -> Dict:
        """
        添加主机
        
        Args:
            name: 主机名称
            host: 主机地址
            port: SSH端口
            username: SSH用户名
            password: SSH密码（可选）
            private_key: SSH私钥（可选）
            key_password: 私钥密码（可选）
            docker_enabled: 是否支持Docker编译
            description: 描述信息
        
        Returns:
            主机信息字典
        """
        with self._lock:
            metadata = self._load_metadata()
            
            # 检查名称是否已存在
            for host_id, host_info in metadata.items():
                if host_info.get("name") == name:
                    raise ValueError(f"主机名称 '{name}' 已存在")
            
            # 生成唯一ID
            host_id = str(uuid.uuid4())
            
            # 创建主机信息
            host_info = {
                "host_id": host_id,
                "name": name,
                "host": host,
                "port": port,
                "username": username,
                "password": password,  # 注意：实际应用中应该加密存储
                "private_key": private_key,  # 注意：实际应用中应该加密存储
                "key_password": key_password,  # 注意：实际应用中应该加密存储
                "docker_enabled": docker_enabled,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            
            # 保存元数据
            metadata[host_id] = host_info
            self._save_metadata(metadata)
            
            print(f"✅ 主机添加成功: {host_id} ({name})")
            return host_info
    
    def update_host(
        self,
        host_id: str,
        name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        key_password: Optional[str] = None,
        docker_enabled: Optional[bool] = None,
        description: Optional[str] = None
    ) -> Optional[Dict]:
        """
        更新主机信息
        
        Args:
            host_id: 主机ID
            其他参数：要更新的字段
        
        Returns:
            更新后的主机信息字典，如果主机不存在则返回None
        """
        with self._lock:
            metadata = self._load_metadata()
            
            if host_id not in metadata:
                return None
            
            host_info = metadata[host_id]
            
            # 如果更新名称，检查是否与其他主机冲突
            if name and name != host_info.get("name"):
                for other_id, other_info in metadata.items():
                    if other_id != host_id and other_info.get("name") == name:
                        raise ValueError(f"主机名称 '{name}' 已存在")
            
            # 更新字段
            if name is not None:
                host_info["name"] = name
            if host is not None:
                host_info["host"] = host
            if port is not None:
                host_info["port"] = port
            if username is not None:
                host_info["username"] = username
            # 密码和私钥：如果传入空字符串，则清除；如果传入None，则保留原值
            if password is not None:
                if password == "":
                    # 空字符串表示清除密码
                    host_info["password"] = None
                else:
                    host_info["password"] = password
            if private_key is not None:
                if private_key == "":
                    # 空字符串表示清除私钥
                    host_info["private_key"] = None
                    host_info["key_password"] = None  # 清除私钥时也清除私钥密码
                else:
                    host_info["private_key"] = private_key
            if key_password is not None:
                host_info["key_password"] = key_password if key_password else None
            if docker_enabled is not None:
                host_info["docker_enabled"] = docker_enabled
            if description is not None:
                host_info["description"] = description
            
            host_info["updated_at"] = datetime.now().isoformat()
            
            # 保存元数据
            self._save_metadata(metadata)
            
            print(f"✅ 主机更新成功: {host_id}")
            return host_info
    
    def list_hosts(self) -> List[Dict]:
        """列出所有主机"""
        metadata = self._load_metadata()
        hosts = []
        
        for host_id, host_info in metadata.items():
            # 创建返回副本，隐藏敏感信息
            host_copy = host_info.copy()
            # 不返回密码和私钥的完整内容，只返回是否已设置
            if host_copy.get("password"):
                host_copy["has_password"] = True
                host_copy["password"] = "***"
            else:
                host_copy["has_password"] = False
            
            if host_copy.get("private_key"):
                host_copy["has_private_key"] = True
                host_copy["private_key"] = "***"
            else:
                host_copy["has_private_key"] = False
            
            if host_copy.get("key_password"):
                host_copy["key_password"] = "***"
            
            hosts.append(host_copy)
        
        # 按创建时间倒序排列
        hosts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return hosts
    
    def get_host(self, host_id: str) -> Optional[Dict]:
        """获取主机信息"""
        metadata = self._load_metadata()
        host_info = metadata.get(host_id)
        
        if host_info:
            # 创建返回副本，隐藏敏感信息
            host_copy = host_info.copy()
            if host_copy.get("password"):
                host_copy["has_password"] = True
                host_copy["password"] = "***"
            else:
                host_copy["has_password"] = False
            
            if host_copy.get("private_key"):
                host_copy["has_private_key"] = True
                host_copy["private_key"] = "***"
            else:
                host_copy["has_private_key"] = False
            
            if host_copy.get("key_password"):
                host_copy["key_password"] = "***"
        
        return host_copy
    
    def get_host_full(self, host_id: str) -> Optional[Dict]:
        """获取主机完整信息（包含密码和私钥，用于连接）"""
        metadata = self._load_metadata()
        return metadata.get(host_id)
    
    def delete_host(self, host_id: str) -> bool:
        """删除主机"""
        with self._lock:
            metadata = self._load_metadata()
            
            if host_id not in metadata:
                return False
            
            # 从元数据中移除
            del metadata[host_id]
            self._save_metadata(metadata)
            
            print(f"✅ 主机已删除: {host_id}")
            return True

