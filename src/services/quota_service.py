"""
配额管理服务
处理用户配额的查询、扣费、充值等操作
使用 SQLite 存储配额数据
"""
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import threading

from src.models.quota import Quota


class QuotaService:
    """
    配额管理服务
    
    核心功能：
    - get_quota(user_id): 查询配额
    - deduct_quota(user_id, amount, task_type): 扣费
    - add_quota(user_id, amount, expire_days): 添加配额
    - check_quota(user_id, required_amount): 检查配额是否充足
    """
    
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
        self.db_path = os.path.join(self.base_dir, "quota.db")
        
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
            CREATE TABLE IF NOT EXISTS quotas (
                user_id TEXT PRIMARY KEY,
                quota_total INTEGER NOT NULL DEFAULT 0,
                quota_used INTEGER NOT NULL DEFAULT 0,
                quota_expire TEXT,
                daily_free_quota INTEGER NOT NULL DEFAULT 60,
                daily_quota_used INTEGER NOT NULL DEFAULT 0,
                last_reset_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # 创建配额记录表（用于记录扣费历史）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quota_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount INTEGER NOT NULL,
                task_type TEXT NOT NULL,
                task_id TEXT,
                transaction_type TEXT NOT NULL,  -- deduct/topup/reset
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES quotas(user_id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON quotas(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_user ON quota_transactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_created ON quota_transactions(created_at)')
        
        conn.commit()
        conn.close()
    
    def _reset_daily_quota_if_needed(self, user_id: str, cursor: sqlite3.Cursor) -> None:
        """检查并重置每日配额（如果需要）"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute('SELECT last_reset_date FROM quotas WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row and row["last_reset_date"] != today:
            # 需要重置每日配额
            cursor.execute('''
                UPDATE quotas 
                SET daily_quota_used = 0, last_reset_date = ?, updated_at = ?
                WHERE user_id = ?
            ''', (today, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), user_id))
    
    async def get_quota(self, user_id: str) -> Quota:
        """
        查询用户配额
        
        Args:
            user_id: 用户 ID
            
        Returns:
            Quota 对象
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 检查并重置每日配额
        self._reset_daily_quota_if_needed(user_id, cursor)
        
        cursor.execute('SELECT * FROM quotas WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            # 用户不存在，返回默认配额（只有每日免费配额）
            return Quota(
                user_id=user_id,
                quota_total=0,
                quota_used=0,
                quota_expire=None,
                daily_free_quota=60,
                daily_quota_used=0
            )
        
        quota_expire = None
        if row["quota_expire"]:
            # Python 3.6 兼容：使用 strptime 解析 ISO 格式
            expire_str = row["quota_expire"].replace("Z", "+00:00")
            try:
                quota_expire = datetime.strptime(expire_str[:19], "%Y-%m-%dT%H:%M:%S")
            except:
                quota_expire = None
        
        return Quota(
            user_id=row["user_id"],
            quota_total=row["quota_total"],
            quota_used=row["quota_used"],
            quota_expire=quota_expire,
            daily_free_quota=row["daily_free_quota"],
            daily_quota_used=row["daily_quota_used"],
            last_reset_date=row["last_reset_date"]
        )
    
    async def check_quota(self, user_id: str, required_amount: int, task_type: str = "ai_video") -> Dict[str, Any]:
        """
        检查用户配额是否充足
        
        Args:
            user_id: 用户 ID
            required_amount: 需要的配额量（秒）
            task_type: 任务类型（ai_video/asr_subtitle）
            
        Returns:
            {
                "sufficient": bool,  # 配额是否充足
                "available": int,    # 可用配额
                "required": int,     # 需要配额
                "source": str        # 配额来源 (daily/paid)
            }
        """
        quota = await self.get_quota(user_id)
        
        # 检查配额是否过期
        if quota.is_expired():
            return {
                "sufficient": False,
                "available": 0,
                "required": required_amount,
                "source": "none",
                "error": "配额已过期"
            }
        
        # AI 配音免费
        if task_type == "voiceover":
            return {
                "sufficient": True,
                "available": 999999,
                "required": 0,
                "source": "free"
            }
        
        # 优先使用每日免费配额
        if quota.daily_quota_remaining >= required_amount:
            return {
                "sufficient": True,
                "available": quota.daily_quota_remaining,
                "required": required_amount,
                "source": "daily"
            }
        
        # 使用付费配额
        remaining_needed = required_amount - quota.daily_quota_remaining
        if quota.quota_remaining >= remaining_needed:
            return {
                "sufficient": True,
                "available": quota.daily_quota_remaining + quota.quota_remaining,
                "required": required_amount,
                "source": "mixed"
            }
        
        # 配额不足
        return {
            "sufficient": False,
            "available": quota.daily_quota_remaining + quota.quota_remaining,
            "required": required_amount,
            "source": "none",
            "error": "配额不足"
        }
    
    async def deduct_quota(
        self, 
        user_id: str, 
        amount: int, 
        task_type: str,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        扣除用户配额
        
        Args:
            user_id: 用户 ID
            amount: 扣除配额量（秒）
            task_type: 任务类型（ai_video/asr_subtitle/voiceover）
            task_id: 任务 ID（可选）
            
        Returns:
            {
                "success": bool,
                "deducted": int,  # 实际扣除量
                "remaining": int,  # 剩余额度
                "error": str  # 错误信息（如果有）
            }
        """
        # AI 配音免费
        if task_type == "voiceover":
            return {
                "success": True,
                "deducted": 0,
                "remaining": 999999,
                "message": "AI 配音免费"
            }
        
        # 检查配额
        check_result = await self.check_quota(user_id, amount, task_type)
        if not check_result["sufficient"]:
            return {
                "success": False,
                "deducted": 0,
                "remaining": 0,
                "error": check_result.get("error", "配额不足")
            }
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc)
        now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 检查并重置每日配额
        self._reset_daily_quota_if_needed(user_id, cursor)
        
        # 获取当前每日配额使用情况
        cursor.execute('SELECT daily_quota_used FROM quotas WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        current_daily_used = row["daily_quota_used"] if row else 0
        
        # 优先扣除每日免费配额（最多 60 秒/日）
        daily_remaining = 60 - current_daily_used
        daily_deducted = min(amount, daily_remaining)
        paid_deducted = amount - daily_deducted
        
        # 更新配额
        if paid_deducted > 0:
            cursor.execute('''
                UPDATE quotas 
                SET quota_used = quota_used + ?, daily_quota_used = daily_quota_used + ?, updated_at = ?
                WHERE user_id = ?
            ''', (paid_deducted, daily_deducted, now_str, user_id))
        else:
            cursor.execute('''
                UPDATE quotas 
                SET daily_quota_used = daily_quota_used + ?, updated_at = ?
                WHERE user_id = ?
            ''', (daily_deducted, now_str, user_id))
        
        # 记录交易
        cursor.execute('''
            INSERT INTO quota_transactions (user_id, amount, task_type, task_id, transaction_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, task_type, task_id, "deduct", now_str))
        
        conn.commit()
        conn.close()
        
        # 获取更新后的配额
        quota = await self.get_quota(user_id)
        
        return {
            "success": True,
            "deducted": amount,
            "daily_deducted": daily_deducted,
            "paid_deducted": paid_deducted,
            "remaining": quota.quota_remaining + quota.daily_quota_remaining,
            "message": "扣费成功"
        }
    
    async def add_quota(
        self, 
        user_id: str, 
        amount: int, 
        expire_days: int = 30
    ) -> Dict[str, Any]:
        """
        添加用户配额（充值）
        
        Args:
            user_id: 用户 ID
            amount: 添加配额量（秒）
            expire_days: 过期天数，默认 30 天
            
        Returns:
            {
                "success": bool,
                "added": int,
                "total": int,
                "expire": str
            }
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc)
        now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        expire_date = now + timedelta(days=expire_days)
        expire_str = expire_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 检查用户是否存在
        cursor.execute('SELECT * FROM quotas WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            # 用户已存在，增加配额并更新过期时间
            cursor.execute('''
                UPDATE quotas 
                SET quota_total = quota_total + ?, quota_expire = ?, updated_at = ?
                WHERE user_id = ?
            ''', (amount, expire_str, now_str, user_id))
        else:
            # 新用户，创建配额记录
            cursor.execute('''
                INSERT INTO quotas (user_id, quota_total, quota_used, quota_expire, daily_free_quota, 
                                   daily_quota_used, last_reset_date, created_at, updated_at)
                VALUES (?, ?, 0, ?, 60, 0, ?, ?, ?)
            ''', (user_id, amount, expire_str, datetime.now().strftime("%Y-%m-%d"), now_str, now_str))
        
        # 记录交易
        cursor.execute('''
            INSERT INTO quota_transactions (user_id, amount, task_type, task_id, transaction_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, "topup", None, "topup", now_str))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "added": amount,
            "total": amount,  # 简化处理，实际应该查询数据库
            "expire": expire_str,
            "message": f"充值成功，配额将在 {expire_days} 天后过期"
        }
    
    async def get_transaction_history(
        self, 
        user_id: str, 
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """
        获取用户配额交易历史
        
        Args:
            user_id: 用户 ID
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            交易记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM quota_transactions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row["id"],
                "userId": row["user_id"],
                "amount": row["amount"],
                "taskType": row["task_type"],
                "taskId": row["task_id"],
                "transactionType": row["transaction_type"],
                "createdAt": row["created_at"]
            }
            for row in rows
        ]
