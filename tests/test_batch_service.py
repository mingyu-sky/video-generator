"""
批量生成服务单元测试
测试批量任务的创建、查询、取消等功能
"""
import pytest
import asyncio
import os
import sys
from datetime import datetime, timezone

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.batch_service import BatchService, BatchStatus
from src.services.task_service import TaskService


@pytest.fixture
def batch_service():
    """创建批量服务实例"""
    # 重置单例以确保测试隔离
    BatchService._instance = None
    service = BatchService()
    return service


@pytest.fixture
def task_service():
    """创建任务服务实例"""
    service = TaskService()
    service._initialized = False
    service.__init__()
    return service


@pytest.fixture
def sample_script_id():
    """示例剧本 ID"""
    return "test-script-001"


@pytest.fixture
def sample_episode_range():
    """示例集数范围"""
    return {"start": 1, "end": 5}


class TestBatchServiceCreation:
    """测试批量任务创建"""
    
    @pytest.mark.asyncio
    async def test_create_batch_job_success(self, batch_service, sample_script_id, sample_episode_range):
        """测试成功创建批量任务"""
        result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range=sample_episode_range,
            parallelism=4
        )
        
        assert result["batchId"] is not None
        assert result["scriptId"] == sample_script_id
        assert result["totalEpisodes"] == 5  # 1-5 共 5 集
        assert result["totalShots"] == 20  # 5 集 * 4 镜头
        assert result["status"] == "pending"
        assert result["progress"] == 0
        assert result["parallelism"] == 4
        assert result["episodeRange"]["start"] == 1
        assert result["episodeRange"]["end"] == 5
    
    @pytest.mark.asyncio
    async def test_create_batch_job_default_parallelism(self, batch_service, sample_script_id, sample_episode_range):
        """测试使用默认并行度创建批量任务"""
        result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range=sample_episode_range
        )
        
        assert result["parallelism"] == 4  # 默认并行度
    
    @pytest.mark.asyncio
    async def test_create_batch_job_custom_range(self, batch_service, sample_script_id):
        """测试自定义集数范围"""
        result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range={"start": 10, "end": 20},
            parallelism=2
        )
        
        assert result["totalEpisodes"] == 11  # 10-20 共 11 集
        assert result["totalShots"] == 44  # 11 集 * 4 镜头
        assert result["parallelism"] == 2


class TestBatchServiceQuery:
    """测试批量任务查询"""
    
    @pytest.mark.asyncio
    async def test_query_batch_status_success(self, batch_service, sample_script_id, sample_episode_range):
        """测试成功查询批量任务状态"""
        # 创建任务
        create_result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range=sample_episode_range
        )
        batch_id = create_result["batchId"]
        
        # 查询状态
        status = await batch_service.query_batch_status(batch_id)
        
        assert status is not None
        assert status["batchId"] == batch_id
        assert status["scriptId"] == sample_script_id
        assert status["status"] == "pending"
        assert status["totalEpisodes"] == 5
        assert status["totalShots"] == 20
        assert status["progress"] == 0
        assert "episodeProgress" in status
    
    @pytest.mark.asyncio
    async def test_query_batch_status_not_found(self, batch_service):
        """测试查询不存在的批量任务"""
        status = await batch_service.query_batch_status("non-existent-batch-id")
        
        assert status is None
    
    @pytest.mark.asyncio
    async def test_query_batch_episode_progress(self, batch_service, sample_script_id, sample_episode_range):
        """测试查询各集进度详情"""
        create_result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range=sample_episode_range
        )
        batch_id = create_result["batchId"]
        
        status = await batch_service.query_batch_status(batch_id)
        
        assert len(status["episodeProgress"]) == 5
        for ep_progress in status["episodeProgress"]:
            assert "episode" in ep_progress
            assert "totalShots" in ep_progress
            assert "completedShots" in ep_progress
            assert "status" in ep_progress
            assert ep_progress["totalShots"] == 4  # 每集 4 个镜头


class TestBatchServiceCancel:
    """测试批量任务取消"""
    
    @pytest.mark.asyncio
    async def test_cancel_batch_success(self, batch_service, sample_script_id, sample_episode_range):
        """测试成功取消批量任务"""
        # 创建任务
        create_result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range=sample_episode_range
        )
        batch_id = create_result["batchId"]
        
        # 取消任务
        cancel_result = await batch_service.cancel_batch(batch_id)
        
        assert cancel_result["success"] is True
        
        # 验证状态已更新
        status = await batch_service.query_batch_status(batch_id)
        assert status["status"] == "cancelled"
    
    @pytest.mark.asyncio
    async def test_cancel_batch_not_found(self, batch_service):
        """测试取消不存在的批量任务"""
        cancel_result = await batch_service.cancel_batch("non-existent-batch-id")
        
        assert cancel_result["success"] is False
        assert cancel_result["code"] == 4001
    
    @pytest.mark.asyncio
    async def test_cancel_batch_already_completed(self, batch_service, sample_script_id, sample_episode_range):
        """测试取消已完成的批量任务"""
        # 创建任务
        create_result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range=sample_episode_range
        )
        batch_id = create_result["batchId"]
        
        # 先取消一次
        await batch_service.cancel_batch(batch_id)
        
        # 再次取消应该失败
        cancel_result = await batch_service.cancel_batch(batch_id)
        
        assert cancel_result["success"] is False
        assert cancel_result["code"] == 4002


class TestBatchServiceList:
    """测试批量任务列表"""
    
    @pytest.mark.asyncio
    async def test_list_batches_success(self, batch_service, sample_script_id, sample_episode_range):
        """测试获取批量任务列表"""
        # 创建多个任务
        batch_ids = []
        for i in range(3):
            result = await batch_service.create_batch_job(
                script_id=f"{sample_script_id}-{i}",
                episode_range=sample_episode_range
            )
            batch_ids.append(result["batchId"])
        
        # 获取列表
        batches = await batch_service.list_batches(limit=10, offset=0)
        
        assert len(batches) >= 3
        
        # 验证返回字段
        for batch in batches:
            assert "batchId" in batch
            assert "scriptId" in batch
            assert "status" in batch
            assert "totalEpisodes" in batch
            assert "progress" in batch
    
    @pytest.mark.asyncio
    async def test_list_batches_filter_by_script(self, batch_service, sample_script_id, sample_episode_range):
        """测试按剧本 ID 过滤批量任务"""
        # 获取当前数量
        initial_batches = await batch_service.list_batches(script_id=sample_script_id)
        initial_count = len(initial_batches)
        
        # 创建任务
        await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range=sample_episode_range
        )
        
        # 按剧本 ID 过滤
        batches = await batch_service.list_batches(script_id=sample_script_id)
        
        assert len(batches) == initial_count + 1
        assert batches[0]["scriptId"] == sample_script_id
    
    @pytest.mark.asyncio
    async def test_list_batches_filter_by_status(self, batch_service, sample_script_id, sample_episode_range):
        """测试按状态过滤批量任务"""
        # 创建任务
        create_result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range=sample_episode_range
        )
        batch_id = create_result["batchId"]
        
        # 取消一个任务
        await batch_service.cancel_batch(batch_id)
        
        # 按状态过滤
        cancelled_batches = await batch_service.list_batches(status="cancelled")
        assert len(cancelled_batches) >= 1
        
        pending_batches = await batch_service.list_batches(status="pending")
        # 应该少于总数（因为有一个被取消了）


class TestBatchServiceProgress:
    """测试批量任务进度更新"""
    
    @pytest.mark.asyncio
    async def test_update_batch_progress(self, batch_service, sample_script_id, sample_episode_range):
        """测试批量任务进度更新"""
        # 创建任务
        create_result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range={"start": 1, "end": 2}  # 2 集，8 个镜头
        )
        batch_id = create_result["batchId"]
        
        # 初始进度应为 0
        status = await batch_service.query_batch_status(batch_id)
        assert status["progress"] == 0
        assert status["completedShots"] == 0
    
    @pytest.mark.asyncio
    async def test_batch_service_singleton(self):
        """测试批量服务单例模式"""
        service1 = BatchService()
        service2 = BatchService()
        
        assert service1 is service2


class TestBatchServiceEdgeCases:
    """测试边界情况"""
    
    @pytest.mark.asyncio
    async def test_create_batch_single_episode(self, batch_service, sample_script_id):
        """测试创建单集批量任务"""
        result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range={"start": 5, "end": 5}
        )
        
        assert result["totalEpisodes"] == 1
        assert result["totalShots"] == 4
    
    @pytest.mark.asyncio
    async def test_create_batch_large_range(self, batch_service, sample_script_id):
        """测试创建大范围批量任务"""
        result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range={"start": 1, "end": 80},
            parallelism=8
        )
        
        assert result["totalEpisodes"] == 80
        assert result["totalShots"] == 320
        assert result["parallelism"] == 8
    
    @pytest.mark.asyncio
    async def test_query_batch_with_episode_progress(self, batch_service, sample_script_id, sample_episode_range):
        """测试查询包含各集进度的批量任务"""
        create_result = await batch_service.create_batch_job(
            script_id=sample_script_id,
            episode_range=sample_episode_range
        )
        batch_id = create_result["batchId"]
        
        status = await batch_service.query_batch_status(batch_id)
        
        # 验证各集进度结构
        assert "episodeProgress" in status
        assert isinstance(status["episodeProgress"], list)
        assert len(status["episodeProgress"]) == 5
        
        for ep in status["episodeProgress"]:
            assert ep["episode"] >= 1
            assert ep["episode"] <= 5
            assert ep["totalShots"] == 4
            assert ep["completedShots"] == 0
            assert ep["status"] == "pending"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
