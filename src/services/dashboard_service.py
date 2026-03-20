"""
仪表盘服务
提供仪表盘统计数据和最近使用记录
支持缓存机制（5 分钟过期）
"""
import os
import json
import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import sqlite3


class DashboardService:
    """仪表盘服务"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
        self.db_path = os.path.join(self.base_dir, "tasks.db")
        self.files_db_path = os.path.join(self.base_dir, "files.db")
        self.scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts")
        self.batches_db_path = os.path.join(self.base_dir, "batches.db")
        
        # 缓存相关
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._cache_ttl = 300  # 5 分钟过期
        
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        self._initialized = True
    
    def _get_tasks_connection(self) -> sqlite3.Connection:
        """获取任务数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_files_connection(self) -> sqlite3.Connection:
        """获取文件数据库连接"""
        conn = sqlite3.connect(self.files_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_batches_connection(self) -> sqlite3.Connection:
        """获取批量任务数据库连接"""
        conn = sqlite3.connect(self.batches_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
        with self._cache_lock:
            if key in self._cache:
                data, timestamp = self._cache[key]
                if time.time() - timestamp < self._cache_ttl:
                    return data
                else:
                    del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """设置缓存"""
        with self._cache_lock:
            self._cache[key] = (data, time.time())
    
    def _invalidate_cache(self, key_prefix: str = None):
        """使缓存失效"""
        with self._cache_lock:
            if key_prefix:
                keys_to_delete = [k for k in self._cache.keys() if k.startswith(key_prefix)]
                for key in keys_to_delete:
                    del self._cache[key]
            else:
                self._cache.clear()
    
    def _format_storage_size(self, bytes_size: int) -> str:
        """格式化存储空间大小"""
        if bytes_size < 1024:
            return f"{bytes_size}B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f}KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.1f}MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.1f}GB"
    
    async def get_stats(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取仪表盘统计数据
        
        Args:
            use_cache: 是否使用缓存，默认 True
            
        Returns:
            统计数据字典
        """
        # 尝试从缓存获取
        cache_key = "dashboard_stats"
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
        
        stats = {
            "tasks": {"total": 0, "pending": 0, "completed": 0},
            "files": {"total": 0, "videos": 0, "storageUsed": "0B"},
            "scripts": {"total": 0},
            "batches": {"total": 0},
            "usage": {"todayQuota": 60, "todayUsed": 0}
        }
        
        # 统计任务
        try:
            conn = self._get_tasks_connection()
            cursor = conn.cursor()
            
            # 总任务数
            cursor.execute('SELECT COUNT(*) FROM tasks')
            stats["tasks"]["total"] = cursor.fetchone()[0]
            
            # 待处理任务数
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
            stats["tasks"]["pending"] = cursor.fetchone()[0]
            
            # 已完成任务数
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
            stats["tasks"]["completed"] = cursor.fetchone()[0]
            
            conn.close()
        except Exception:
            pass
        
        # 统计文件
        try:
            conn = self._get_files_connection()
            cursor = conn.cursor()
            
            # 总文件数
            cursor.execute('SELECT COUNT(*) FROM files')
            stats["files"]["total"] = cursor.fetchone()[0]
            
            # 视频文件数
            cursor.execute("SELECT COUNT(*) FROM files WHERE file_type = 'video'")
            stats["files"]["videos"] = cursor.fetchone()[0]
            
            # 总存储空间
            cursor.execute('SELECT SUM(file_size) FROM files')
            total_size = cursor.fetchone()[0] or 0
            stats["files"]["storageUsed"] = self._format_storage_size(total_size)
            
            conn.close()
        except Exception:
            pass
        
        # 统计剧本
        try:
            if os.path.exists(self.scripts_dir):
                scripts = [f for f in os.listdir(self.scripts_dir) if f.endswith('.json')]
                stats["scripts"]["total"] = len(scripts)
        except Exception:
            pass
        
        # 统计批量任务
        try:
            conn = self._get_batches_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM batches')
            stats["batches"]["total"] = cursor.fetchone()[0]
            
            conn.close()
        except Exception:
            pass
        
        # 今日使用配额（模拟数据，实际应从 quota_service 获取）
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        stats["usage"]["todayQuota"] = 60
        stats["usage"]["todayUsed"] = min(stats["tasks"]["completed"], 60)
        
        # 存入缓存
        if use_cache:
            self._set_cache(cache_key, stats)
        
        return stats
    
    async def get_recent(self, type: str = None, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取最近使用记录
        
        Args:
            type: 类型过滤 (tasks/files/scripts/batches)，None 表示全部
            limit: 每种类型返回数量限制，默认 10
            
        Returns:
            最近使用记录字典
        """
        result = {}
        
        if type is None or type == "tasks":
            result["tasks"] = await self._get_recent_tasks(limit)
        
        if type is None or type == "scripts":
            result["scripts"] = await self._get_recent_scripts(limit)
        
        if type is None or type == "batches":
            result["batches"] = await self._get_recent_batches(limit)
        
        if type is None or type == "files":
            result["files"] = await self._get_recent_files(limit)
        
        return result
    
    async def _get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近任务"""
        tasks = []
        try:
            conn = self._get_tasks_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT task_id, task_type, status, progress, created_at 
                FROM tasks 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            for row in rows:
                tasks.append({
                    "taskId": row["task_id"],
                    "type": row["task_type"],
                    "status": row["status"],
                    "progress": row["progress"]
                })
            
            conn.close()
        except Exception:
            pass
        
        return tasks
    
    async def _get_recent_scripts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近剧本"""
        scripts = []
        try:
            if os.path.exists(self.scripts_dir):
                script_files = []
                for filename in os.listdir(self.scripts_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(self.scripts_dir, filename)
                        try:
                            mtime = os.path.getmtime(filepath)
                            script_files.append((filename, mtime))
                        except Exception:
                            pass
                
                # 按修改时间倒序
                script_files.sort(key=lambda x: x[1], reverse=True)
                
                for filename, _ in script_files[:limit]:
                    filepath = os.path.join(self.scripts_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            scripts.append({
                                "scriptId": data.get("scriptId"),
                                "title": data.get("title"),
                                "episodes": data.get("episodes"),
                                "genre": data.get("genre")
                            })
                    except Exception:
                        continue
        except Exception:
            pass
        
        return scripts
    
    async def _get_recent_batches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近批量任务"""
        batches = []
        try:
            conn = self._get_batches_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT batch_id, script_id, status, progress, created_at 
                FROM batches 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            for row in rows:
                batches.append({
                    "batchId": row["batch_id"],
                    "scriptId": row["script_id"],
                    "status": row["status"],
                    "progress": row["progress"]
                })
            
            conn.close()
        except Exception:
            pass
        
        return batches
    
    async def _get_recent_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近文件"""
        files = []
        try:
            conn = self._get_files_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_id, file_name, file_type, file_size, upload_time 
                FROM files 
                ORDER BY upload_time DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            for row in rows:
                files.append({
                    "fileId": row["file_id"],
                    "fileName": row["file_name"],
                    "fileType": row["file_type"],
                    "fileSize": row["file_size"]
                })
            
            conn.close()
        except Exception:
            pass
        
        return files
    
    def invalidate_stats_cache(self):
        """使统计数据缓存失效（在数据变更时调用）"""
        self._invalidate_cache("dashboard_stats")


# 全局服务实例
dashboard_service = DashboardService()
