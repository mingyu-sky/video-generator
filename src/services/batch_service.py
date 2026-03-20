"""
批量生成服务
处理多集短剧的批量视频生成任务
支持并行处理、进度追踪、任务取消
"""
import os
import json
import sqlite3
import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from enum import Enum
import threading

from .task_service import TaskService, TaskStatus


class BatchStatus(Enum):
    """批量任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchService:
    """批量生成服务"""
    
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
        self.db_path = os.path.join(self.base_dir, "batches.db")
        
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 初始化数据库
        self._init_db()
        self._initialized = True
        
        # 服务引用
        self.task_service = TaskService()
        
        # 并行处理控制
        self._running_batches: Dict[str, asyncio.Task] = {}
        self._default_parallelism = 4
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 批量任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS batches (
                batch_id TEXT PRIMARY KEY,
                script_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                total_episodes INTEGER NOT NULL,
                total_shots INTEGER NOT NULL,
                completed_episodes INTEGER NOT NULL DEFAULT 0,
                completed_shots INTEGER NOT NULL DEFAULT 0,
                failed_episodes INTEGER NOT NULL DEFAULT 0,
                parallelism INTEGER NOT NULL DEFAULT 4,
                episode_range_start INTEGER NOT NULL,
                episode_range_end INTEGER NOT NULL,
                task_ids TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            )
        ''')
        
        # 批量任务明细表（记录每集的任务 ID）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                episode_number INTEGER NOT NULL,
                shot_number INTEGER NOT NULL,
                task_id TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                UNIQUE(batch_id, episode_number, shot_number)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_batch_status ON batches(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_batch_script ON batches(script_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_episode_batch ON batch_episodes(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_episode_task ON batch_episodes(task_id)')
        
        conn.commit()
        conn.close()
    
    async def create_batch_job(self, script_id: str, episode_range: Dict[str, int], 
                               parallelism: int = None) -> Dict[str, Any]:
        """
        创建批量生成任务
        
        Args:
            script_id: 剧本 ID
            episode_range: 集数范围 {"start": 1, "end": 80}
            parallelism: 并行度，默认 4
            
        Returns:
            批量任务信息
        """
        batch_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        start_episode = episode_range.get("start", 1)
        end_episode = episode_range.get("end", 80)
        total_episodes = end_episode - start_episode + 1
        
        # 假设每集 4 个镜头（可根据实际情况调整）
        shots_per_episode = 4
        total_shots = total_episodes * shots_per_episode
        
        parallelism = parallelism or self._default_parallelism
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 插入批量任务
        cursor.execute('''
            INSERT INTO batches (
                batch_id, script_id, status, total_episodes, total_shots,
                parallelism, episode_range_start, episode_range_end,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (batch_id, script_id, BatchStatus.PENDING.value, total_episodes, 
              total_shots, parallelism, start_episode, end_episode, now, now))
        
        # 初始化每集的明细记录
        for ep in range(start_episode, end_episode + 1):
            for shot in range(1, shots_per_episode + 1):
                cursor.execute('''
                    INSERT INTO batch_episodes (
                        batch_id, episode_number, shot_number, status, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (batch_id, ep, shot, BatchStatus.PENDING.value, now))
        
        conn.commit()
        conn.close()
        
        return {
            "batchId": batch_id,
            "scriptId": script_id,
            "totalEpisodes": total_episodes,
            "totalShots": total_shots,
            "status": BatchStatus.PENDING.value,
            "progress": 0,
            "parallelism": parallelism,
            "episodeRange": {"start": start_episode, "end": end_episode},
            "createdAt": now
        }
    
    async def query_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        查询批量任务进度
        
        Args:
            batch_id: 批量任务 ID
            
        Returns:
            批量任务状态，不存在则返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 查询批量任务主记录
        cursor.execute('SELECT * FROM batches WHERE batch_id = ?', (batch_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # 查询各集进度详情
        cursor.execute('''
            SELECT episode_number, status, error_message
            FROM batch_episodes
            WHERE batch_id = ?
            ORDER BY episode_number, shot_number
        ''', (batch_id,))
        
        episode_rows = cursor.fetchall()
        conn.close()
        
        # 按集数汇总进度
        episode_progress = {}
        for ep_row in episode_rows:
            ep_num = ep_row["episode_number"]
            if ep_num not in episode_progress:
                episode_progress[ep_num] = {
                    "episode": ep_num,
                    "totalShots": 0,
                    "completedShots": 0,
                    "failedShots": 0,
                    "status": "pending",
                    "error": None
                }
            
            episode_progress[ep_num]["totalShots"] += 1
            if ep_row["status"] == "completed":
                episode_progress[ep_num]["completedShots"] += 1
            elif ep_row["status"] == "failed":
                episode_progress[ep_num]["failedShots"] += 1
                episode_progress[ep_num]["error"] = ep_row["error_message"]
        
        # 计算每集状态
        for ep_num, ep_data in episode_progress.items():
            if ep_data["failedShots"] > 0:
                ep_data["status"] = "failed"
            elif ep_data["completedShots"] == ep_data["totalShots"]:
                ep_data["status"] = "completed"
            elif ep_data["completedShots"] > 0:
                ep_data["status"] = "processing"
        
        # 计算总体进度
        completed_shots = row["completed_shots"]
        total_shots = row["total_shots"]
        progress = int((completed_shots / total_shots * 100)) if total_shots > 0 else 0
        
        result = {
            "batchId": row["batch_id"],
            "scriptId": row["script_id"],
            "status": row["status"],
            "totalEpisodes": row["total_episodes"],
            "totalShots": row["total_shots"],
            "completedEpisodes": row["completed_episodes"],
            "completedShots": completed_shots,
            "failedEpisodes": row["failed_episodes"],
            "progress": progress,
            "parallelism": row["parallelism"],
            "episodeRange": {
                "start": row["episode_range_start"],
                "end": row["episode_range_end"]
            },
            "episodeProgress": list(episode_progress.values()),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"]
        }
        
        if row["completed_at"]:
            result["completedAt"] = row["completed_at"]
        
        if row["error_message"]:
            result["error"] = {"message": row["error_message"]}
        
        return result
    
    async def cancel_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        取消批量任务
        
        Args:
            batch_id: 批量任务 ID
            
        Returns:
            取消结果
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 查询任务状态
        cursor.execute('SELECT status FROM batches WHERE batch_id = ?', (batch_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {"success": False, "error": "批量任务不存在", "code": 4001}
        
        current_status = row["status"]
        if current_status in [BatchStatus.COMPLETED.value, BatchStatus.FAILED.value, 
                              BatchStatus.CANCELLED.value]:
            conn.close()
            return {"success": False, "error": "任务已完成，无法取消", "code": 4002}
        
        # 更新批量任务状态
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        cursor.execute('''
            UPDATE batches 
            SET status = ?, updated_at = ?, completed_at = ?
            WHERE batch_id = ?
        ''', (BatchStatus.CANCELLED.value, now, now, batch_id))
        
        # 取消所有子任务
        cursor.execute('''
            UPDATE batch_episodes 
            SET status = ?, completed_at = ?
            WHERE batch_id = ? AND status = 'pending'
        ''', (BatchStatus.CANCELLED.value, now, batch_id))
        
        conn.commit()
        conn.close()
        
        # 取消关联的任务服务任务
        task_ids = await self._get_batch_task_ids(batch_id)
        for task_id in task_ids:
            await self.task_service.cancel_task(task_id)
        
        # 如果正在运行，从运行列表中移除
        if batch_id in self._running_batches:
            del self._running_batches[batch_id]
        
        return {"success": True}
    
    async def start_batch_processing(self, batch_id: str, 
                                     video_generate_func=None) -> bool:
        """
        开始处理批量任务
        
        Args:
            batch_id: 批量任务 ID
            video_generate_func: 视频生成函数 (async)
            
        Returns:
            是否成功启动
        """
        # 检查任务状态
        batch_info = await self.query_batch_status(batch_id)
        if not batch_info:
            return False
        
        if batch_info["status"] != BatchStatus.PENDING.value:
            return False
        
        # 更新状态为处理中
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        cursor.execute('''
            UPDATE batches SET status = ?, updated_at = ?
            WHERE batch_id = ?
        ''', (BatchStatus.PROCESSING.value, now, batch_id))
        conn.commit()
        conn.close()
        
        # 创建后台处理任务
        async def process_batch():
            await self._process_batch_internal(batch_id, video_generate_func)
        
        task = asyncio.create_task(process_batch())
        self._running_batches[batch_id] = task
        
        return True
    
    async def _process_batch_internal(self, batch_id: str, 
                                      video_generate_func=None):
        """内部批量处理逻辑"""
        try:
            # 获取批量任务信息
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM batches WHERE batch_id = ?', (batch_id,))
            row = cursor.fetchone()
            
            if not row:
                return
            
            parallelism = row["parallelism"]
            start_ep = row["episode_range_start"]
            end_ep = row["episode_range_end"]
            script_id = row["script_id"]
            
            conn.close()
            
            # 获取所有待处理的镜头任务
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, episode_number, shot_number, task_id
                FROM batch_episodes
                WHERE batch_id = ? AND status = 'pending'
                ORDER BY episode_number, shot_number
            ''', (batch_id,))
            
            pending_tasks = cursor.fetchall()
            conn.close()
            
            if not pending_tasks:
                return
            
            # 创建信号量控制并发
            semaphore = asyncio.Semaphore(parallelism)
            
            async def process_shot(episode_record):
                async with semaphore:
                    ep_num = episode_record["episode_number"]
                    shot_num = episode_record["shot_number"]
                    record_id = episode_record["id"]
                    
                    try:
                        # 更新状态为处理中
                        await self._update_episode_status(
                            batch_id, record_id, "processing"
                        )
                        
                        # 调用视频生成函数（如果提供）
                        if video_generate_func:
                            task_id = str(uuid.uuid4())
                            await video_generate_func(
                                script_id=script_id,
                                episode_number=ep_num,
                                shot_number=shot_num,
                                task_id=task_id
                            )
                            # 更新任务 ID
                            await self._update_episode_task_id(
                                batch_id, record_id, task_id
                            )
                        
                        # 更新为完成
                        await self._update_episode_status(
                            batch_id, record_id, "completed"
                        )
                        
                        # 更新批量进度
                        await self._update_batch_progress(batch_id)
                        
                    except Exception as e:
                        # 更新为失败
                        await self._update_episode_status(
                            batch_id, record_id, "failed", str(e)
                        )
                        
                        # 更新批量进度
                        await self._update_batch_progress(batch_id)
            
            # 并发处理所有镜头
            tasks = [process_shot(record) for record in pending_tasks]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # 检查是否有失败
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as failed_count
                FROM batch_episodes
                WHERE batch_id = ? AND status = 'failed'
            ''', (batch_id,))
            failed_count = cursor.fetchone()["failed_count"]
            
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
            if failed_count > 0:
                # 部分失败
                cursor.execute('''
                    UPDATE batches 
                    SET status = ?, updated_at = ?, completed_at = ?, error_message = ?
                    WHERE batch_id = ?
                ''', (BatchStatus.FAILED.value, now, now, 
                      f"部分镜头生成失败，共 {failed_count} 个", batch_id))
            else:
                # 全部成功
                cursor.execute('''
                    UPDATE batches 
                    SET status = ?, updated_at = ?, completed_at = ?
                    WHERE batch_id = ?
                ''', (BatchStatus.COMPLETED.value, now, now, batch_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            # 处理异常
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            cursor.execute('''
                UPDATE batches 
                SET status = ?, updated_at = ?, completed_at = ?, error_message = ?
                WHERE batch_id = ?
            ''', (BatchStatus.FAILED.value, now, now, str(e), batch_id))
            conn.commit()
            conn.close()
        
        finally:
            # 从运行列表中移除
            if batch_id in self._running_batches:
                del self._running_batches[batch_id]
    
    async def _update_episode_status(self, batch_id: str, record_id: int,
                                     status: str, error_message: str = None):
        """更新单集镜头状态"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        if status == "completed" or status == "failed":
            cursor.execute('''
                UPDATE batch_episodes 
                SET status = ?, completed_at = ?, error_message = ?
                WHERE id = ?
            ''', (status, now, error_message, record_id))
        else:
            cursor.execute('''
                UPDATE batch_episodes SET status = ?
                WHERE id = ?
            ''', (status, record_id))
        
        conn.commit()
        conn.close()
    
    async def _update_episode_task_id(self, batch_id: str, record_id: int, 
                                      task_id: str):
        """更新镜头关联的任务 ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE batch_episodes SET task_id = ?
            WHERE id = ?
        ''', (task_id, record_id))
        conn.commit()
        conn.close()
    
    async def _update_batch_progress(self, batch_id: str):
        """更新批量任务进度"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 统计完成的集数和镜头数
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT CASE WHEN status = 'completed' THEN episode_number END) as completed_episodes,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_shots,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_shots
            FROM batch_episodes
            WHERE batch_id = ?
        ''', (batch_id,))
        
        stats = cursor.fetchone()
        completed_episodes = stats["completed_episodes"] or 0
        completed_shots = stats["completed_shots"] or 0
        failed_shots = stats["failed_shots"] or 0
        
        # 统计失败的集数（只要有镜头失败就算）
        cursor.execute('''
            SELECT COUNT(DISTINCT episode_number) as failed_episodes
            FROM batch_episodes
            WHERE batch_id = ? AND status = 'failed'
        ''', (batch_id,))
        failed_episodes = cursor.fetchone()["failed_episodes"] or 0
        
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        cursor.execute('''
            UPDATE batches 
            SET completed_episodes = ?, completed_shots = ?, 
                failed_episodes = ?, updated_at = ?
            WHERE batch_id = ?
        ''', (completed_episodes, completed_shots, failed_episodes, now, batch_id))
        
        conn.commit()
        conn.close()
    
    async def _get_batch_task_ids(self, batch_id: str) -> List[str]:
        """获取批量任务关联的所有任务 ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT task_id FROM batch_episodes
            WHERE batch_id = ? AND task_id IS NOT NULL
        ''', (batch_id,))
        
        task_ids = [row["task_id"] for row in cursor.fetchall() if row["task_id"]]
        conn.close()
        
        return task_ids
    
    async def list_batches(self, script_id: str = None, status: str = None,
                          limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取批量任务列表
        
        Args:
            script_id: 剧本 ID 过滤
            status: 状态过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            批量任务列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM batches WHERE 1=1"
        params = []
        
        if script_id:
            query += " AND script_id = ?"
            params.append(script_id)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            "batchId": row["batch_id"],
            "scriptId": row["script_id"],
            "status": row["status"],
            "totalEpisodes": row["total_episodes"],
            "completedEpisodes": row["completed_episodes"],
            "progress": int((row["completed_shots"] / row["total_shots"] * 100)) if row["total_shots"] > 0 else 0,
            "createdAt": row["created_at"]
        } for row in rows]
