# backend/stats_cache.py
"""目录统计缓存管理模块"""
import os
import json
import threading
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path


class StatsCacheManager:
    """目录统计缓存管理器"""

    def __init__(self, base_dir: str, cache_filename: str = ".stats.json"):
        """
        初始化缓存管理器

        Args:
            base_dir: 要统计的目录路径
            cache_filename: 缓存文件名，默认为 .stats.json
        """
        self.base_dir = base_dir
        self.cache_file = os.path.join(base_dir, cache_filename)
        self.lock = threading.Lock()

    def _load_cache(self) -> Dict:
        """加载缓存文件"""
        if not os.path.exists(self.cache_file):
            return {
                "cache_time": None,
                "total_size": 0,
                "total_size_mb": 0,
                "dir_count": 0,
                "file_count": 0,
                "items": {},
            }

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
                # 兼容旧格式
                if "items" not in cache:
                    cache["items"] = {}
                return cache
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ 加载缓存文件失败 ({self.cache_file}): {e}，将重新扫描")
            return {
                "cache_time": None,
                "total_size": 0,
                "total_size_mb": 0,
                "dir_count": 0,
                "file_count": 0,
                "items": {},
            }

    def _save_cache(self, cache: Dict):
        """保存缓存文件"""
        try:
            # 确保目录存在
            os.makedirs(self.base_dir, exist_ok=True)

            # 更新缓存时间
            cache["cache_time"] = datetime.now().isoformat()

            # 写入文件（使用临时文件确保原子性）
            temp_file = self.cache_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)

            # 原子替换
            if os.path.exists(self.cache_file):
                os.replace(temp_file, self.cache_file)
            else:
                os.rename(temp_file, self.cache_file)
        except Exception as e:
            print(f"⚠️ 保存缓存文件失败 ({self.cache_file}): {e}")
            # 清理临时文件
            temp_file = self.cache_file + ".tmp"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def _get_dir_mtime(self, dir_path: str) -> float:
        """获取目录的修改时间（取目录本身及其所有子项的最近修改时间）"""
        if not os.path.exists(dir_path):
            return 0

        max_mtime = os.path.getmtime(dir_path)
        try:
            for root, dirs, files in os.walk(dir_path):
                for d in dirs:
                    d_path = os.path.join(root, d)
                    try:
                        max_mtime = max(max_mtime, os.path.getmtime(d_path))
                    except:
                        pass
                for f in files:
                    f_path = os.path.join(root, f)
                    try:
                        max_mtime = max(max_mtime, os.path.getmtime(f_path))
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ 获取目录修改时间失败 ({dir_path}): {e}")

        return max_mtime

    def _calculate_dir_size(self, dir_path: str) -> Tuple[int, int]:
        """
        计算目录大小和文件数量

        Returns:
            (total_size, file_count)
        """
        total_size = 0
        file_count = 0

        try:
            for root, dirs, files in os.walk(dir_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    try:
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                        file_count += 1
                    except Exception as e:
                        print(f"⚠️ 计算文件大小失败 ({file_path}): {e}")
        except Exception as e:
            print(f"⚠️ 遍历目录失败 ({dir_path}): {e}")

        return total_size, file_count

    def get_build_dir_stats(self) -> Dict:
        """
        获取构建目录统计信息（带缓存）

        Returns:
            {
                "success": True,
                "total_size_mb": float,
                "dir_count": int,
                "exists": bool
            }
        """
        with self.lock:
            if not os.path.exists(self.base_dir):
                return {
                    "success": True,
                    "total_size_mb": 0,
                    "dir_count": 0,
                    "exists": False,
                }

            cache = self._load_cache()
            cache_time = None
            if cache["cache_time"]:
                try:
                    cache_time = datetime.fromisoformat(cache["cache_time"]).timestamp()
                except:
                    cache_time = None

            total_size = 0
            dir_count = 0
            items = cache.get("items", {})
            updated_items = {}

            # 遍历构建目录
            for item in os.listdir(self.base_dir):
                item_path = os.path.join(self.base_dir, item)
                if not os.path.isdir(item_path):
                    continue

                # 跳过 tasks 目录和缓存文件
                if item == "tasks" or item.startswith(".stats"):
                    continue

                try:
                    # 获取目录修改时间
                    dir_mtime = self._get_dir_mtime(item_path)

                    # 检查是否需要重新计算
                    item_cache = items.get(item)
                    need_rescan = True

                    if item_cache and cache_time:
                        cached_mtime = item_cache.get("mtime", 0)
                        if dir_mtime <= cached_mtime:
                            # 使用缓存
                            item_size = item_cache.get("size", 0)
                            total_size += item_size
                            dir_count += 1
                            updated_items[item] = item_cache.copy()
                            need_rescan = False

                    if need_rescan:
                        # 重新计算
                        item_size, _ = self._calculate_dir_size(item_path)
                        total_size += item_size
                        dir_count += 1
                        updated_items[item] = {
                            "size": item_size,
                            "mtime": dir_mtime,
                            "file_count": 0,  # 构建目录不统计文件数
                        }

                except Exception as e:
                    print(f"⚠️ 计算目录大小失败 ({item_path}): {e}")

            # 更新缓存（移除已删除的目录）
            cache["items"] = updated_items
            cache["total_size"] = total_size
            cache["total_size_mb"] = round(total_size / 1024 / 1024, 2)
            cache["dir_count"] = dir_count
            self._save_cache(cache)

            return {
                "success": True,
                "total_size_mb": cache["total_size_mb"],
                "dir_count": dir_count,
                "exists": True,
            }

    def get_export_dir_stats(self) -> Dict:
        """
        获取导出目录统计信息（带缓存）

        Returns:
            {
                "success": True,
                "total_size_mb": float,
                "file_count": int,
                "exists": bool
            }
        """
        with self.lock:
            if not os.path.exists(self.base_dir):
                return {
                    "success": True,
                    "total_size_mb": 0,
                    "file_count": 0,
                    "exists": False,
                }

            cache = self._load_cache()
            cache_time = None
            if cache["cache_time"]:
                try:
                    cache_time = datetime.fromisoformat(cache["cache_time"]).timestamp()
                except:
                    cache_time = None

            total_size = 0
            file_count = 0
            items = cache.get("items", {})
            updated_items = {}

            # 遍历导出目录（包括所有子目录）
            for root, dirs, files in os.walk(self.base_dir):
                # 跳过缓存文件目录
                if ".stats" in root:
                    continue

                for filename in files:
                    # 跳过 tasks.json 元数据文件和缓存文件
                    if filename == "tasks.json" or filename.startswith(".stats"):
                        continue

                    file_path = os.path.join(root, filename)
                    try:
                        # 获取文件修改时间
                        file_mtime = os.path.getmtime(file_path)

                        # 使用相对路径作为 key
                        rel_path = os.path.relpath(file_path, self.base_dir)

                        # 检查是否需要重新计算
                        item_cache = items.get(rel_path)
                        need_rescan = True

                        if item_cache and cache_time:
                            cached_mtime = item_cache.get("mtime", 0)
                            if file_mtime <= cached_mtime:
                                # 使用缓存
                                file_size = item_cache.get("size", 0)
                                total_size += file_size
                                file_count += 1
                                updated_items[rel_path] = item_cache.copy()
                                need_rescan = False

                        if need_rescan:
                            # 重新计算
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            file_count += 1
                            updated_items[rel_path] = {
                                "size": file_size,
                                "mtime": file_mtime,
                                "file_count": 1,
                            }

                    except Exception as e:
                        print(f"⚠️ 计算文件大小失败 ({file_path}): {e}")

            # 更新缓存（移除已删除的文件）
            cache["items"] = updated_items
            cache["total_size"] = total_size
            cache["total_size_mb"] = round(total_size / 1024 / 1024, 2)
            cache["file_count"] = file_count
            self._save_cache(cache)

            return {
                "success": True,
                "total_size_mb": cache["total_size_mb"],
                "file_count": file_count,
                "exists": True,
            }

    def update_cache_async(self, stats_type: str = "build"):
        """
        异步更新缓存（在后台线程中执行）

        Args:
            stats_type: 统计类型，"build" 或 "export"
        """

        def _update():
            try:
                if stats_type == "build":
                    self.get_build_dir_stats()
                elif stats_type == "export":
                    self.get_export_dir_stats()
            except Exception as e:
                print(f"⚠️ 异步更新统计缓存失败: {e}")

        thread = threading.Thread(target=_update, daemon=True)
        thread.start()
