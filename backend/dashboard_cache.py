# backend/dashboard_cache.py
"""仪表盘统计缓存管理模块"""
import threading
import time
from typing import Dict, Optional
from datetime import datetime


class DashboardCacheManager:
    """仪表盘统计缓存管理器"""

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
        self._cache: Optional[Dict] = None
        self._cache_time: Optional[float] = None
        self._cache_duration = 60  # 60秒缓存有效期
        self._refreshing = False
        self._refresh_lock = threading.Lock()

    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self._cache is None or self._cache_time is None:
            return False
        elapsed = time.time() - self._cache_time
        return elapsed < self._cache_duration

    def get_stats(self, force_refresh: bool = False) -> Dict:
        """
        获取仪表盘统计数据（带缓存）

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            统计数据字典
        """
        with self._lock:
            # 如果缓存有效且不强制刷新，直接返回
            if not force_refresh and self._is_cache_valid():
                return self._cache.copy()

            # 防止并发刷新
            with self._refresh_lock:
                if self._refreshing and not force_refresh:
                    # 如果正在刷新且不是强制刷新，返回旧缓存
                    if self._cache:
                        return self._cache.copy()

                self._refreshing = True
                try:
                    # 计算统计数据
                    stats = self._calculate_stats()
                    self._cache = stats
                    self._cache_time = time.time()
                finally:
                    self._refreshing = False

            return self._cache.copy()

    def _calculate_stats(self) -> Dict:
        """计算仪表盘统计数据"""
        try:
            # 导入必要的模块
            from backend.handlers import BuildTaskManager, BuildManager
            from backend.pipeline_manager import PipelineManager
            from backend.git_source_manager import GitSourceManager
            from backend.config import get_all_registries, get_all_templates
            from backend.resource_package_manager import ResourcePackageManager
            from backend.host_manager import HostManager
            from backend.stats_cache import StatsCacheManager
            from backend.handlers import BUILD_DIR, EXPORT_DIR

            # 获取任务列表
            build_manager = BuildTaskManager()
            all_tasks = build_manager.list_tasks()

            # 计算任务统计
            total_tasks = len(all_tasks)
            running_tasks = len([t for t in all_tasks if t.get("status") == "running"])
            completed_tasks = len(
                [t for t in all_tasks if t.get("status") == "completed"]
            )

            # 获取流水线列表
            pipeline_manager = PipelineManager()
            pipelines = pipeline_manager.list_pipelines()
            total_pipelines = len(pipelines)
            enabled_pipelines = len([p for p in pipelines if p.get("enabled", False)])
            disabled_pipelines = total_pipelines - enabled_pipelines

            # 获取数据源列表
            git_source_manager = GitSourceManager()
            datasources = git_source_manager.list_sources()
            total_datasources = len(datasources)

            # 获取仓库列表
            registries = get_all_registries()
            total_registries = len(registries)

            # 获取模板列表
            templates = get_all_templates()
            total_templates = len(templates)

            # 获取资源包列表
            resource_package_manager = ResourcePackageManager()
            resource_packages = resource_package_manager.list_packages()
            total_resource_packages = len(resource_packages)

            # 获取主机列表
            host_manager = HostManager()
            hosts = host_manager.list_hosts()
            total_hosts = len(hosts)

            # 获取存储统计
            build_cache_manager = StatsCacheManager(BUILD_DIR)
            build_stats = build_cache_manager.get_build_dir_stats()
            build_storage_mb = build_stats.get("total_size_mb", 0)

            export_cache_manager = StatsCacheManager(EXPORT_DIR)
            export_stats = export_cache_manager.get_export_dir_stats()
            export_storage_mb = export_stats.get("total_size_mb", 0)

            # 转换为字节
            build_storage = build_storage_mb * 1024 * 1024
            export_storage = export_storage_mb * 1024 * 1024
            total_storage = build_storage + export_storage

            return {
                "success": True,
                "stats": {
                    "totalTasks": total_tasks,
                    "runningTasks": running_tasks,
                    "completedTasks": completed_tasks,
                    "pipelines": total_pipelines,
                    "enabledPipelines": enabled_pipelines,
                    "disabledPipelines": disabled_pipelines,
                    "datasources": total_datasources,
                    "registries": total_registries,
                    "templates": total_templates,
                    "resourcePackages": total_resource_packages,
                    "hosts": total_hosts,
                    "buildStorage": build_storage,
                    "exportStorage": export_storage,
                    "totalStorage": total_storage,
                },
                "buildStats": {
                    "total_size_mb": build_storage_mb,
                    "dir_count": build_stats.get("dir_count", 0),
                },
                "exportStats": {
                    "total_size_mb": export_storage_mb,
                    "file_count": export_stats.get("file_count", 0),
                },
            }
        except Exception as e:
            print(f"⚠️ 计算仪表盘统计失败: {e}")
            import traceback

            traceback.print_exc()
            # 返回默认值
            return {
                "success": True,
                "stats": {
                    "totalTasks": 0,
                    "runningTasks": 0,
                    "completedTasks": 0,
                    "pipelines": 0,
                    "enabledPipelines": 0,
                    "disabledPipelines": 0,
                    "datasources": 0,
                    "registries": 0,
                    "templates": 0,
                    "resourcePackages": 0,
                    "hosts": 0,
                    "buildStorage": 0,
                    "exportStorage": 0,
                    "totalStorage": 0,
                },
                "buildStats": {
                    "total_size_mb": 0,
                    "dir_count": 0,
                },
                "exportStats": {
                    "total_size_mb": 0,
                    "file_count": 0,
                },
            }

    def clear_cache(self):
        """清空缓存"""
        with self._lock:
            self._cache = None
            self._cache_time = None


# 全局缓存实例
dashboard_cache = DashboardCacheManager()
