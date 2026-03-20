"""
配额管理数据模型
"""
from datetime import datetime
from typing import Optional


class Quota:
    """
    配额数据模型
    
    Attributes:
        user_id: 用户 ID
        quota_total: 总额度（秒）
        quota_used: 已用额度（秒）
        quota_expire: 过期时间
        daily_free_quota: 每日免费配额（秒）
        daily_quota_used: 今日已用配额（秒）
        last_reset_date: 最后重置日期（用于每日配额重置）
    """
    
    def __init__(
        self,
        user_id: str,
        quota_total: int = 0,
        quota_used: int = 0,
        quota_expire: Optional[datetime] = None,
        daily_free_quota: int = 60,
        daily_quota_used: int = 0,
        last_reset_date: Optional[str] = None
    ):
        self.user_id = user_id
        self.quota_total = quota_total
        self.quota_used = quota_used
        self.quota_expire = quota_expire
        self.daily_free_quota = daily_free_quota
        self.daily_quota_used = daily_quota_used
        self.last_reset_date = last_reset_date or datetime.now().strftime("%Y-%m-%d")
    
    @property
    def quota_remaining(self) -> int:
        """剩余额度（秒）"""
        return max(0, self.quota_total - self.quota_used)
    
    @property
    def daily_quota_remaining(self) -> int:
        """今日剩余免费配额（秒）"""
        return max(0, self.daily_free_quota - self.daily_quota_used)
    
    def is_expired(self) -> bool:
        """检查配额是否过期"""
        if self.quota_expire is None:
            return False
        return datetime.now() > self.quota_expire
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "userId": self.user_id,
            "quotaTotal": self.quota_total,
            "quotaUsed": self.quota_used,
            "quotaRemaining": self.quota_remaining,
            "quotaExpire": self.quota_expire.strftime("%Y-%m-%dT%H:%M:%SZ") if self.quota_expire else None,
            "dailyFreeQuota": self.daily_free_quota,
            "dailyQuotaUsed": self.daily_quota_used,
            "dailyQuotaRemaining": self.daily_quota_remaining,
            "lastResetDate": self.last_reset_date,
            "isExpired": self.is_expired()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Quota":
        """从字典创建"""
        quota_expire = None
        if data.get("quota_expire"):
            if isinstance(data["quota_expire"], str):
                # Python 3.6 兼容：使用 strptime 解析 ISO 格式
                expire_str = data["quota_expire"].replace("Z", "+00:00")
                try:
                    quota_expire = datetime.strptime(expire_str[:19], "%Y-%m-%dT%H:%M:%S")
                except:
                    quota_expire = None
            else:
                quota_expire = data["quota_expire"]
        
        return cls(
            user_id=data["user_id"],
            quota_total=data.get("quota_total", 0),
            quota_used=data.get("quota_used", 0),
            quota_expire=quota_expire,
            daily_free_quota=data.get("daily_free_quota", 60),
            daily_quota_used=data.get("daily_quota_used", 0),
            last_reset_date=data.get("last_reset_date")
        )
