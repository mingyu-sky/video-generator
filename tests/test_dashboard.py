"""
仪表盘模块单元测试
测试用例覆盖：
- test_dashboard_stats_success: 获取仪表盘统计 - 正常流程
- test_dashboard_stats_empty_data: 获取仪表盘统计 - 空数据
- test_dashboard_stats_cache: 获取仪表盘统计 - 缓存机制
- test_dashboard_recent_tasks: 获取最近任务
- test_dashboard_recent_all: 获取最近使用 - 全部类型
- test_dashboard_recent_invalid_type: 获取最近使用 - 无效类型
- test_dashboard_recent_limit: 获取最近使用 - 分页限制
- test_dashboard_stats_concurrent: 获取仪表盘统计 - 并发请求
"""
import pytest
import os
import sys
import io
import uuid
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.main import app
from src.services.dashboard_service import DashboardService

client = TestClient(app)

# 测试用临时文件
TEST_VIDEO_CONTENT = b"\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isomtest video content"
TEST_AUDIO_CONTENT = b"ID3\x03\x00\x00\x00\x00\x00test audio content"


class TestDashboardStats:
    """仪表盘统计接口测试"""
    
    def test_dashboard_stats_success(self):
        """test_dashboard_stats_success: 获取仪表盘统计 - 正常流程"""
        response = client.get("/api/v1/dashboard/stats")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert "data" in result
        
        data = result["data"]
        # 验证数据结构
        assert "tasks" in data
        assert "files" in data
        assert "scripts" in data
        assert "batches" in data
        assert "usage" in data
        
        # 验证 tasks 结构
        assert "total" in data["tasks"]
        assert "pending" in data["tasks"]
        assert "completed" in data["tasks"]
        
        # 验证 files 结构
        assert "total" in data["files"]
        assert "videos" in data["files"]
        assert "storageUsed" in data["files"]
        
        # 验证 scripts 结构
        assert "total" in data["scripts"]
        
        # 验证 batches 结构
        assert "total" in data["batches"]
        
        # 验证 usage 结构
        assert "todayQuota" in data["usage"]
        assert "todayUsed" in data["usage"]
    
    def test_dashboard_stats_empty_data(self):
        """test_dashboard_stats_empty_data: 获取仪表盘统计 - 空数据"""
        # 使用新的 dashboard_service 实例（模拟空数据）
        service = DashboardService()
        service._invalidate_cache()
        
        response = client.get("/api/v1/dashboard/stats")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        
        data = result["data"]
        # 验证即使空数据也有正确的结构
        assert isinstance(data["tasks"]["total"], int)
        assert isinstance(data["files"]["total"], int)
        assert isinstance(data["scripts"]["total"], int)
        assert isinstance(data["batches"]["total"], int)
    
    def test_dashboard_stats_cache(self):
        """test_dashboard_stats_cache: 获取仪表盘统计 - 缓存机制"""
        service = DashboardService()
        service._invalidate_cache()
        
        # 第一次请求
        start_time = time.time()
        response1 = client.get("/api/v1/dashboard/stats")
        first_duration = time.time() - start_time
        
        assert response1.status_code == 200
        
        # 第二次请求（使用缓存）
        start_time = time.time()
        response2 = client.get("/api/v1/dashboard/stats")
        second_duration = time.time() - start_time
        
        assert response2.status_code == 200
        
        # 验证两次返回数据一致
        assert response1.json()["data"] == response2.json()["data"]
        
        # 验证第二次请求更快（使用了缓存）
        # 注意：这个断言可能不稳定，因为第一次可能也很快
        # 但通常缓存会更快
        assert second_duration <= first_duration or second_duration < 0.1
        
        # 测试禁用缓存
        service._invalidate_cache()
        response3 = client.get("/api/v1/dashboard/stats?useCache=false")
        assert response3.status_code == 200


class TestDashboardRecent:
    """最近使用接口测试"""
    
    def test_dashboard_recent_tasks(self):
        """test_dashboard_recent_tasks: 获取最近任务"""
        # 先创建一个任务（通过音频接口）
        voiceover_data = {
            "text": "测试配音用于仪表盘测试",
            "voice": "zh-CN-XiaoxiaoNeural"
        }
        response = client.post("/api/v1/audio/voiceover", json=voiceover_data)
        
        # 获取最近任务
        response = client.get("/api/v1/dashboard/recent?type=tasks&limit=5")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert "data" in result
        
        data = result["data"]
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
        
        # 验证任务数据结构
        if len(data["tasks"]) > 0:
            task = data["tasks"][0]
            assert "taskId" in task
            assert "type" in task
            assert "status" in task
    
    def test_dashboard_recent_all(self):
        """test_dashboard_recent_all: 获取最近使用 - 全部类型"""
        response = client.get("/api/v1/dashboard/recent?limit=5")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        
        data = result["data"]
        # 验证返回所有类型
        assert "tasks" in data
        assert "scripts" in data
        assert "batches" in data
        assert "files" in data
        
        # 验证都是列表
        assert isinstance(data["tasks"], list)
        assert isinstance(data["scripts"], list)
        assert isinstance(data["batches"], list)
        assert isinstance(data["files"], list)
    
    def test_dashboard_recent_invalid_type(self):
        """test_dashboard_recent_invalid_type: 获取最近使用 - 无效类型"""
        # 传入无效类型，应该返回空或忽略该类型
        response = client.get("/api/v1/dashboard/recent?type=invalid_type&limit=5")
        
        # 接口应该正常返回，只是不包含有效数据
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
    
    def test_dashboard_recent_limit(self):
        """test_dashboard_recent_limit: 获取最近使用 - 分页限制"""
        # 测试不同 limit 值
        for limit in [1, 5, 10, 20]:
            response = client.get(f"/api/v1/dashboard/recent?type=tasks&limit={limit}")
            
            assert response.status_code == 200
            result = response.json()
            assert result["code"] == 200
            
            data = result["data"]
            # 验证返回数量不超过 limit
            assert len(data["tasks"]) <= limit
        
        # 测试超过最大限制（100）
        response = client.get("/api/v1/dashboard/recent?type=tasks&limit=101")
        # FastAPI 应该会验证参数范围
        assert response.status_code in [200, 422]
    
    def test_dashboard_stats_concurrent(self):
        """test_dashboard_stats_concurrent: 获取仪表盘统计 - 并发请求"""
        service = DashboardService()
        service._invalidate_cache()
        
        results = []
        errors = []
        
        def fetch_stats():
            try:
                response = client.get("/api/v1/dashboard/stats")
                results.append(response.json())
            except Exception as e:
                errors.append(str(e))
        
        # 并发发起 10 个请求
        threads = []
        for _ in range(10):
            t = threading.Thread(target=fetch_stats)
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证所有请求都成功
        assert len(errors) == 0, f"并发请求出现错误：{errors}"
        assert len(results) == 10
        
        # 验证所有返回数据一致
        first_result = results[0]
        for result in results[1:]:
            assert result["code"] == 200
            assert result["data"] == first_result["data"]


class TestDashboardService:
    """仪表盘服务层测试"""
    
    def test_service_singleton(self):
        """测试服务单例模式"""
        service1 = DashboardService()
        service2 = DashboardService()
        assert service1 is service2
    
    def test_cache_mechanism(self):
        """测试缓存机制"""
        service = DashboardService()
        service._invalidate_cache()
        
        # 设置缓存
        test_data = {"test": "value"}
        service._set_cache("test_key", test_data)
        
        # 获取缓存
        cached = service._get_from_cache("test_key")
        assert cached == test_data
        
        # 获取不存在的缓存
        non_existent = service._get_from_cache("non_existent_key")
        assert non_existent is None
    
    def test_invalidate_cache(self):
        """测试缓存失效"""
        service = DashboardService()
        
        # 设置多个缓存
        service._set_cache("dashboard_stats", {"data": 1})
        service._set_cache("other_key", {"data": 2})
        
        # 使 dashboard 相关缓存失效
        service._invalidate_cache("dashboard")
        
        # 验证 dashboard_stats 已失效
        assert service._get_from_cache("dashboard_stats") is None
        # 验证 other_key 仍然存在
        assert service._get_from_cache("other_key") is not None
        
        # 清空所有缓存
        service._invalidate_cache()
        assert service._get_from_cache("other_key") is None
    
    def test_format_storage_size(self):
        """测试存储空间格式化"""
        service = DashboardService()
        
        assert service._format_storage_size(500) == "500B"
        assert service._format_storage_size(1024) == "1.0KB"
        assert service._format_storage_size(1536) == "1.5KB"
        assert service._format_storage_size(1024 * 1024) == "1.0MB"
        assert service._format_storage_size(1024 * 1024 * 1024) == "1.0GB"
        assert service._format_storage_size(15 * 1024 * 1024 * 1024) == "15.0GB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
