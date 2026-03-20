"""
配额管理服务单元测试
测试配额查询、扣费、充值等功能
"""
import pytest
import asyncio
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.quota_service import QuotaService
from src.models.quota import Quota


@pytest.fixture
def quota_service():
    """创建配额服务实例"""
    # 使用测试数据库
    service = QuotaService()
    # 重置初始化标志以便重新初始化
    service._initialized = False
    service.base_dir = os.path.join(os.path.dirname(__file__), "test_uploads")
    service.db_path = os.path.join(service.base_dir, "test_quota.db")
    os.makedirs(service.base_dir, exist_ok=True)
    service._init_db()
    service._initialized = True
    yield service
    # 清理测试数据库
    if os.path.exists(service.db_path):
        os.remove(service.db_path)
    if os.path.exists(service.base_dir):
        os.rmdir(service.base_dir)


class TestQuotaModel:
    """测试配额数据模型"""
    
    def test_quota_creation(self):
        """测试配额对象创建"""
        quota = Quota(
            user_id="user-123",
            quota_total=3600,
            quota_used=1200,
            daily_free_quota=60,
            daily_quota_used=30
        )
        
        assert quota.user_id == "user-123"
        assert quota.quota_total == 3600
        assert quota.quota_used == 1200
        assert quota.quota_remaining == 2400
        assert quota.daily_free_quota == 60
        assert quota.daily_quota_used == 30
        assert quota.daily_quota_remaining == 30
    
    def test_quota_remaining_calculation(self):
        """测试剩余额度计算"""
        quota = Quota(
            user_id="user-123",
            quota_total=1000,
            quota_used=1200  # 超过总额度
        )
        
        # 剩余额度不能为负数
        assert quota.quota_remaining == 0
    
    def test_quota_is_expired(self):
        """测试配额过期检查"""
        # 未设置过期时间
        quota1 = Quota(user_id="user-123")
        assert not quota1.is_expired()
        
        # 未来过期时间
        future_date = datetime.now() + timedelta(days=30)
        quota2 = Quota(user_id="user-123", quota_expire=future_date)
        assert not quota2.is_expired()
        
        # 过去过期时间
        past_date = datetime.now() - timedelta(days=1)
        quota3 = Quota(user_id="user-123", quota_expire=past_date)
        assert quota3.is_expired()
    
    def test_quota_to_dict(self):
        """测试配额转字典"""
        quota = Quota(
            user_id="user-123",
            quota_total=3600,
            quota_used=1200
        )
        
        data = quota.to_dict()
        
        assert data["userId"] == "user-123"
        assert data["quotaTotal"] == 3600
        assert data["quotaUsed"] == 1200
        assert data["quotaRemaining"] == 2400
        assert data["dailyFreeQuota"] == 60
        assert data["dailyQuotaUsed"] == 0
        assert data["dailyQuotaRemaining"] == 60
    
    def test_quota_from_dict(self):
        """测试从字典创建配额"""
        data = {
            "user_id": "user-456",
            "quota_total": 5000,
            "quota_used": 1000,
            "quota_expire": None,
            "daily_free_quota": 60,
            "daily_quota_used": 20
        }
        
        quota = Quota.from_dict(data)
        
        assert quota.user_id == "user-456"
        assert quota.quota_total == 5000
        assert quota.quota_used == 1000


class TestQuotaService:
    """测试配额服务"""
    
    @pytest.mark.asyncio
    async def test_get_quota_new_user(self, quota_service):
        """测试查询新用户配额"""
        quota = await quota_service.get_quota("new-user-123")
        
        assert quota.user_id == "new-user-123"
        assert quota.quota_total == 0
        assert quota.quota_used == 0
        assert quota.daily_free_quota == 60
        assert quota.daily_quota_used == 0
    
    @pytest.mark.asyncio
    async def test_add_quota(self, quota_service):
        """测试添加配额（充值）"""
        result = await quota_service.add_quota(
            user_id="user-123",
            amount=3600,
            expire_days=30
        )
        
        assert result["success"] is True
        assert result["added"] == 3600
        
        # 验证配额已添加
        quota = await quota_service.get_quota("user-123")
        assert quota.quota_total == 3600
        assert quota.quota_expire is not None
    
    @pytest.mark.asyncio
    async def test_deduct_quota_voiceover_free(self, quota_service):
        """测试 AI 配音免费"""
        result = await quota_service.deduct_quota(
            user_id="user-123",
            amount=100,
            task_type="voiceover"
        )
        
        assert result["success"] is True
        assert result["deducted"] == 0
        assert "免费" in result.get("message", "")
    
    @pytest.mark.asyncio
    async def test_deduct_quota_with_daily_free(self, quota_service):
        """测试使用每日免费配额扣费"""
        # 先添加一些配额
        await quota_service.add_quota("user-123", 100, 30)
        
        # 扣费 30 秒（在每日免费额度内）
        result = await quota_service.deduct_quota(
            user_id="user-123",
            amount=30,
            task_type="ai_video",
            task_id="user-123-task-001"
        )
        
        assert result["success"] is True
        assert result["deducted"] == 30
        
        # 验证配额已扣除
        quota = await quota_service.get_quota("user-123")
        assert quota.daily_quota_used == 30
    
    @pytest.mark.asyncio
    async def test_deduct_quota_insufficient(self, quota_service):
        """测试配额不足时扣费失败"""
        # 不添加配额，直接扣费
        result = await quota_service.deduct_quota(
            user_id="user-123",
            amount=100,  # 超过每日免费额度 60 秒
            task_type="ai_video"
        )
        
        # 每日免费额度只有 60 秒，100 秒应该失败
        assert result["success"] is False
        assert "配额不足" in result.get("error", "")
    
    @pytest.mark.asyncio
    async def test_check_quota_sufficient(self, quota_service):
        """测试检查配额充足"""
        await quota_service.add_quota("user-123", 1000, 30)
        
        result = await quota_service.check_quota(
            user_id="user-123",
            required_amount=50,
            task_type="ai_video"
        )
        
        assert result["sufficient"] is True
        assert result["available"] >= 50
    
    @pytest.mark.asyncio
    async def test_check_quota_insufficient(self, quota_service):
        """测试检查配额不足"""
        result = await quota_service.check_quota(
            user_id="user-123",
            required_amount=1000,
            task_type="ai_video"
        )
        
        assert result["sufficient"] is False
        assert result["available"] < 1000
    
    @pytest.mark.asyncio
    async def test_daily_quota_reset(self, quota_service):
        """测试每日配额重置"""
        # 先使用一些每日配额
        await quota_service.add_quota("user-123", 100, 30)
        await quota_service.deduct_quota("user-123", 30, "ai_video", "task-1")
        
        # 验证已使用
        quota1 = await quota_service.get_quota("user-123")
        assert quota1.daily_quota_used == 30
        
        # 模拟第二天（修改 last_reset_date）
        conn = quota_service._get_connection()
        cursor = conn.cursor()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        cursor.execute(
            "UPDATE quotas SET last_reset_date = ? WHERE user_id = ?",
            (yesterday, "user-123")
        )
        conn.commit()
        conn.close()
        
        # 再次查询，应该自动重置
        quota2 = await quota_service.get_quota("user-123")
        assert quota2.daily_quota_used == 0
        assert quota2.last_reset_date == datetime.now().strftime("%Y-%m-%d")
    
    @pytest.mark.asyncio
    async def test_transaction_history(self, quota_service):
        """测试交易历史查询"""
        # 添加配额
        await quota_service.add_quota("user-123", 1000, 30)
        
        # 扣费
        await quota_service.deduct_quota("user-123", 30, "ai_video", "task-1")
        await quota_service.deduct_quota("user-123", 20, "ai_video", "task-2")
        
        # 查询交易历史
        transactions = await quota_service.get_transaction_history("user-123")
        
        assert len(transactions) >= 3  # 至少 3 条记录（1 次充值 + 2 次扣费）
        
        # 验证交易类型
        types = [t["transactionType"] for t in transactions]
        assert "topup" in types
        assert "deduct" in types
    
    @pytest.mark.asyncio
    async def test_quota_mixed_payment(self, quota_service):
        """测试混合支付（每日免费 + 付费配额）"""
        # 添加付费配额
        await quota_service.add_quota("user-123", 100, 30)
        
        # 先用完每日免费额度
        result1 = await quota_service.deduct_quota("user-123", 60, "ai_video", "task-1")
        assert result1["success"] is True
        
        # 验证每日配额已使用
        quota1 = await quota_service.get_quota("user-123")
        assert quota1.daily_quota_used == 60
        
        # 再扣费 50 秒（应该使用付费配额，因为每日免费已用完）
        result2 = await quota_service.deduct_quota("user-123", 50, "ai_video", "task-2")
        assert result2["success"] is True
        
        # 验证剩余额度
        quota2 = await quota_service.get_quota("user-123")
        assert quota2.quota_used == 50  # 付费部分
        assert quota2.daily_quota_used == 60  # 免费部分保持不变


class TestQuotaIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_quota_lifecycle(self, quota_service):
        """测试完整的配额生命周期"""
        user_id = "test-user"
        
        # 1. 新用户查询
        quota1 = await quota_service.get_quota(user_id)
        assert quota1.quota_total == 0
        
        # 2. 充值
        topup_result = await quota_service.add_quota(user_id, 3600, 30)
        assert topup_result["success"] is True
        
        # 3. 查询充值后
        quota2 = await quota_service.get_quota(user_id)
        assert quota2.quota_total == 3600
        
        # 4. 检查配额
        check_result = await quota_service.check_quota(user_id, 100, "ai_video")
        assert check_result["sufficient"] is True
        
        # 5. 扣费
        deduct_result = await quota_service.deduct_quota(user_id, 100, "ai_video", "task-1")
        assert deduct_result["success"] is True
        
        # 6. 查询扣费后（60 秒来自每日免费，40 秒来自付费配额）
        quota3 = await quota_service.get_quota(user_id)
        assert quota3.quota_used == 40  # 付费部分
        assert quota3.daily_quota_used == 60  # 免费部分
        
        # 7. 查询交易历史
        transactions = await quota_service.get_transaction_history(user_id)
        assert len(transactions) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
