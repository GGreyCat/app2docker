# backend/docker_info_cache.py
"""
Docker信息缓存管理器
统一管理Docker信息的获取和缓存，30分钟缓存，支持强制刷新
"""
import threading
import time
import subprocess
import shutil
import re
from typing import Dict, Optional
from datetime import datetime, timedelta
from backend.handlers import docker_builder, DOCKER_AVAILABLE


class DockerInfoCache:
    """Docker信息缓存管理器"""
    
    _instance = None
    _lock = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._lock = threading.Lock()
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        """初始化缓存管理器"""
        self.cache: Optional[Dict] = None
        self.cache_time: Optional[datetime] = None
        self.cache_duration = timedelta(minutes=30)  # 30分钟缓存
        self.refreshing = False
        self._refresh_lock = threading.Lock()
    
    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self.cache is None or self.cache_time is None:
            return False
        
        elapsed = datetime.now() - self.cache_time
        return elapsed < self.cache_duration
    
    def _fetch_docker_info(self) -> Dict:
        """获取Docker信息（实际获取逻辑）"""
        info = {
            "connected": DOCKER_AVAILABLE,
            "builder_type": "unknown",
            "version": None,
            "api_version": None,
            "remote_host": None,
            "images_count": 0,
            "images_size": 0,
            "containers_total": 0,
            "containers_running": 0,
            "containers_size": 0,
            "storage_driver": None,
            "os_type": None,
            "arch": None,
            "kernel_version": None,
            "docker_root": None,
            "ncpu": None,
            "mem_total": None,
            "runtime": None,
            "volumes_count": 0,
            "networks_count": 0,
            "buildx_available": False,
            "buildx_version": None,
        }

        # 优先从配置中读取远程 Docker 信息
        from backend.config import load_config
        config = load_config()
        docker_config = config.get("docker", {})
        use_remote = docker_config.get("use_remote", False)
        remote_config = docker_config.get("remote", {})

        # 设置构建器类型和远程配置
        if use_remote:
            info["builder_type"] = "remote"
            remote_host = remote_config.get("host", "")
            remote_port = remote_config.get("port", 2375)
            if remote_host:
                info["remote_host"] = f"{remote_host}:{remote_port}"
                info["remote_config"] = {
                    "host": remote_host,
                    "port": remote_port,
                    "use_tls": remote_config.get("use_tls", False),
                    "cert_path": remote_config.get("cert_path", ""),
                    "verify_tls": remote_config.get("verify_tls", False),
                }

        # 获取连接信息
        connection_info = ""
        if docker_builder:
            try:
                connection_info = docker_builder.get_connection_info()
                connection_error = None
                if hasattr(docker_builder, "get_connection_error"):
                    connection_error = docker_builder.get_connection_error()
                    if connection_error and connection_error != "未知错误":
                        info["connection_error"] = connection_error
            except Exception as e:
                print(f"⚠️ 获取连接信息失败: {e}")

        # 如果配置中没有设置，尝试从连接信息中获取
        if not use_remote and connection_info:
            if "本地" in connection_info:
                info["builder_type"] = "local"
            elif "远程" in connection_info:
                info["builder_type"] = "remote"
                match = re.search(r"\((.+?)\)", connection_info)
                if match:
                    info["remote_host"] = match.group(1)
            elif "模拟" in connection_info:
                info["builder_type"] = "mock"
        elif use_remote:
            if not info.get("remote_host") and remote_config.get("host"):
                remote_host = remote_config.get("host", "")
                remote_port = remote_config.get("port", 2375)
                info["remote_host"] = f"{remote_host}:{remote_port}"
                if not info.get("remote_config"):
                    info["remote_config"] = {
                        "host": remote_host,
                        "port": remote_port,
                        "use_tls": remote_config.get("use_tls", False),
                        "cert_path": remote_config.get("cert_path", ""),
                        "verify_tls": remote_config.get("verify_tls", False),
                    }
        elif "本地" in connection_info:
            info["builder_type"] = "local"
        elif "远程" in connection_info:
            info["builder_type"] = "remote"
            match = re.search(r"\((.+?)\)", connection_info)
            if match:
                info["remote_host"] = match.group(1)
        elif "模拟" in connection_info:
            info["builder_type"] = "mock"

        # 获取 Docker 详细信息
        try:
            if (
                docker_builder
                and hasattr(docker_builder, "client")
                and docker_builder.client
            ):
                try:
                    # 获取版本信息
                    version_info = docker_builder.client.version()
                    info["version"] = version_info.get("Version", "Unknown")
                    info["api_version"] = version_info.get("ApiVersion", "Unknown")
                    info["os_type"] = version_info.get("Os", "Unknown")
                    info["arch"] = version_info.get("Arch", "Unknown")
                    info["kernel_version"] = version_info.get("KernelVersion", "")
                except Exception as version_error:
                    print(f"⚠️ 获取 Docker 版本信息失败: {version_error}")

                # 获取系统信息
                try:
                    system_info = docker_builder.client.info()
                    info["images_count"] = system_info.get("Images", 0)
                    info["containers_total"] = system_info.get("Containers", 0)
                    info["containers_running"] = system_info.get("ContainersRunning", 0)
                    info["storage_driver"] = system_info.get("Driver", "Unknown")
                    info["docker_root"] = system_info.get("DockerRootDir", "")
                    info["ncpu"] = system_info.get("NCPU", 0)
                    info["mem_total"] = system_info.get("MemTotal", 0)
                    info["runtime"] = system_info.get("DefaultRuntime", "runc")
                except Exception as system_error:
                    print(f"⚠️ 获取 Docker 系统信息失败: {system_error}")

                # 获取卷和网络数量
                try:
                    volumes_data = docker_builder.client.volumes.list()
                    # volumes.list() 返回字典，包含 "Volumes" 键
                    if isinstance(volumes_data, dict):
                        info["volumes_count"] = len(volumes_data.get("Volumes", []))
                    else:
                        info["volumes_count"] = len(volumes_data) if volumes_data else 0
                except Exception as volumes_error:
                    print(f"⚠️ 获取卷数量失败: {volumes_error}")

                try:
                    networks = docker_builder.client.networks.list()
                    info["networks_count"] = len(networks) if networks else 0
                except Exception as networks_error:
                    print(f"⚠️ 获取网络数量失败: {networks_error}")

                # 获取镜像大小
                try:
                    images = docker_builder.client.images.list()
                    total_size = 0
                    for img in images:
                        total_size += img.attrs.get("Size", 0)
                    info["images_size"] = total_size
                except Exception as images_error:
                    print(f"⚠️ 获取镜像大小失败: {images_error}")

                # 获取容器大小
                try:
                    containers = docker_builder.client.containers.list(all=True)
                    total_size = 0
                    for container in containers:
                        stats = container.stats(stream=False)
                        total_size += stats.get("memory_stats", {}).get("usage", 0)
                    info["containers_size"] = total_size
                except Exception as containers_error:
                    print(f"⚠️ 获取容器大小失败: {containers_error}")

                # 检查 buildx 是否可用
                try:
                    docker_path = shutil.which("docker")
                    if docker_path:
                        result = subprocess.run(
                            [docker_path, "buildx", "version"],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        if result.returncode == 0:
                            info["buildx_available"] = True
                            # 提取版本号
                            version_line = result.stdout.split("\n")[0]
                            match = re.search(r"v?(\d+\.\d+\.\d+)", version_line)
                            if match:
                                info["buildx_version"] = match.group(1)
                            else:
                                info["buildx_version"] = "unknown"
                except Exception as buildx_error:
                    print(f"⚠️ 检查 buildx 失败: {buildx_error}")

        except Exception as e:
            print(f"⚠️ 获取 Docker 信息失败: {e}")

        # 添加缓存时间戳
        info["cached_at"] = datetime.now().isoformat()
        
        return info
    
    def get_docker_info(self, force_refresh: bool = False) -> Dict:
        """获取Docker信息（带缓存）
        
        Args:
            force_refresh: 是否强制刷新缓存
        
        Returns:
            Docker信息字典
        """
        with self._lock:
            # 如果需要强制刷新或缓存无效，则刷新
            if force_refresh or not self._is_cache_valid():
                # 防止并发刷新
                with self._refresh_lock:
                    if self.refreshing and not force_refresh:
                        # 如果正在刷新且不是强制刷新，返回旧缓存
                        if self.cache:
                            return self.cache.copy()
                    
                    self.refreshing = True
                    try:
                        self.cache = self._fetch_docker_info()
                        self.cache_time = datetime.now()
                        print(f"✅ Docker信息已刷新，缓存时间: {self.cache_time}")
                    finally:
                        self.refreshing = False
            
            # 返回缓存副本
            if self.cache:
                return self.cache.copy()
            else:
                # 如果缓存为空，返回默认值
                return self._fetch_docker_info()
    
    def refresh_cache(self) -> Dict:
        """强制刷新缓存"""
        return self.get_docker_info(force_refresh=True)
    
    def get_cache_age(self) -> Optional[float]:
        """获取缓存年龄（秒）"""
        if self.cache_time is None:
            return None
        elapsed = datetime.now() - self.cache_time
        return elapsed.total_seconds()
    
    def clear_cache(self):
        """清空缓存"""
        with self._lock:
            self.cache = None
            self.cache_time = None


# 全局缓存实例
docker_info_cache = DockerInfoCache()

