"""
任务管理服务
处理任务创建、查询、取消等操作
使用 SQLite 存储任务状态
"""
import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from enum import Enum
import threading


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskService:
    """任务管理服务"""
    
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
        
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 初始化数据库
        self._init_db()
        self._initialized = True
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                progress INTEGER NOT NULL DEFAULT 0,
                message TEXT,
                input_data TEXT,
                result_data TEXT,
                error_code INTEGER,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            )
        ''')
        
        # 创建状态索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON tasks(created_at)')
        
        conn.commit()
        conn.close()
    
    async def create_task(self, task_id: str, task_type: str, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        创建任务
        
        Args:
            task_id: 任务 ID
            task_type: 任务类型（如 video/concat, audio/voiceover）
            input_data: 输入数据
            
        Returns:
            任务信息
        """
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (task_id, task_type, status, progress, message, input_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (task_id, task_type, TaskStatus.PENDING.value, 0, "等待处理", 
              json.dumps(input_data) if input_data else None, now, now))
        
        conn.commit()
        conn.close()
        
        return {
            "taskId": task_id,
            "type": task_type,
            "status": TaskStatus.PENDING.value,
            "progress": 0,
            "message": "等待处理",
            "createdAt": now
        }
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务详情
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务信息，不存在则返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_dict(row)
    
    async def update_task(self, task_id: str, status: TaskStatus = None, progress: int = None, 
                         message: str = None, result_data: Dict[str, Any] = None,
                         error_code: int = None, error_message: str = None) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务 ID
            status: 任务状态
            progress: 进度 (0-100)
            message: 消息
            result_data: 结果数据
            error_code: 错误码
            error_message: 错误信息
            
        Returns:
            是否更新成功
        """
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        updates = ["updated_at = ?"]
        params = [now]
        
        if status is not None:
            updates.append("status = ?")
            params.append(status.value)
            if status == TaskStatus.COMPLETED or status == TaskStatus.FAILED or status == TaskStatus.CANCELLED:
                updates.append("completed_at = ?")
                params.append(now)
        
        if progress is not None:
            updates.append("progress = ?")
            params.append(progress)
        
        if message is not None:
            updates.append("message = ?")
            params.append(message)
        
        if result_data is not None:
            updates.append("result_data = ?")
            params.append(json.dumps(result_data))
        
        if error_code is not None:
            updates.append("error_code = ?")
            params.append(error_code)
        
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)
        
        params.append(task_id)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'UPDATE tasks SET {", ".join(updates)} WHERE task_id = ?', params)
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        取消任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            结果字典
        """
        task = await self.get_task(task_id)
        
        if not task:
            return {"success": False, "error": "任务不存在", "code": 3001}
        
        if task["status"] in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
            return {"success": False, "error": "任务已完成，无法取消", "code": 3002}
        
        await self.update_task(task_id, status=TaskStatus.CANCELLED, message="任务已取消")
        
        return {"success": True}
    
    async def batch_get_tasks(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取任务
        
        Args:
            task_ids: 任务 ID 列表
            
        Returns:
            任务列表
        """
        if not task_ids:
            return []
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in task_ids])
        cursor.execute(f'SELECT * FROM tasks WHERE task_id IN ({placeholders})', task_ids)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    async def list_tasks(self, status: TaskStatus = None, limit: int = 100, 
                        offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取任务列表
        
        Args:
            status: 状态过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            任务列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
                          (status.value, limit, offset))
        else:
            cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC LIMIT ? OFFSET ?',
                          (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        result = {
            "taskId": row["task_id"],
            "type": row["task_type"],
            "status": row["status"],
            "progress": row["progress"],
            "message": row["message"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"]
        }
        
        if row["completed_at"]:
            result["completedAt"] = row["completed_at"]
        
        # 解析结果数据
        if row["result_data"]:
            try:
                result["result"] = json.loads(row["result_data"])
            except:
                result["result"] = {}
        
        # 解析错误信息
        error = {}
        if row["error_code"]:
            error["code"] = row["error_code"]
        if row["error_message"]:
            error["message"] = row["error_message"]
        
        if error:
            result["error"] = error
        
        return result
