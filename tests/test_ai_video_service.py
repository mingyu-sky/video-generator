"""
AI 视频生成服务单元测试 (AIVideoService)
测试用例覆盖：
- TC-AI-VIDEO-001: 视频生成 - 正常流程
- TC-AI-VIDEO-002: 视频生成 - 默认参数
- TC-AI-VIDEO-003: 视频生成 - 自定义时长和分辨率
- TC-AI-VIDEO-004: 视频生成 - 空提示词验证
- TC-AI-VIDEO-005: 视频生成 - 无效时长验证
- TC-AI-VIDEO-006: 视频生成 - 无效分辨率验证
- TC-AI-VIDEO-007: 查询状态 - 正常流程
- TC-AI-VIDEO-008: 获取配置信息
"""
import pytest
import os
import sys
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# Python 3.6 兼容 AsyncMock
try:
    from unittest.mock import AsyncMock
except ImportError:
    # Python 3.6 手动实现 AsyncMock
    from unittest.mock import MagicMock
    import asyncio
    
    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, *args):
            return None

from src.services.ai_video_service import AIVideoService, VideoResolution, VideoDuration


class TestAIVideoServiceInit:
    """AI 视频服务 - 初始化测试"""
    
    def test_singleton_pattern(self):
        """TC-AI-VIDEO-INIT-001: 单例模式测试"""
        service1 = AIVideoService()
        service2 = AIVideoService()
        assert service1 is service2
    
    def test_default_config(self):
        """TC-AI-VIDEO-INIT-002: 默认配置测试"""
        service = AIVideoService()
        assert service.default_resolution == "1080p"
        assert service.default_duration == 5
        assert "720p" in service.supported_resolutions
        assert "1080p" in service.supported_resolutions
        assert "4k" in service.supported_resolutions
        assert 5 in service.supported_durations
        assert 10 in service.supported_durations
        assert 15 in service.supported_durations
        assert 30 in service.supported_durations


class TestAIVideoServiceGenerate:
    """AI 视频服务 - 视频生成测试"""
    
    @pytest.fixture
    def ai_service(self):
        """创建 AI 视频服务实例"""
        return AIVideoService()
    
    @pytest.mark.asyncio
    async def test_generate_video_success(self, ai_service):
        """TC-AI-VIDEO-001: 视频生成 - 正常流程"""
        # Mock Sora API 响应
        mock_response = {
            "task_id": "sora-task-123",
            "estimated_time": 60
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await ai_service.generate_video(
                prompt="Modern coffee shop interior, warm lighting, cinematic shot",
                duration=10,
                resolution="1080p"
            )
            
            assert "taskId" in result
            assert result["status"] == "pending"
            assert result["duration"] == 10
            assert result["resolution"] == "1080p"
            assert "estimatedTime" in result
    
    @pytest.mark.asyncio
    async def test_generate_video_default_params(self, ai_service):
        """TC-AI-VIDEO-002: 视频生成 - 使用默认参数"""
        mock_response = {
            "task_id": "sora-task-456",
            "estimated_time": 60
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await ai_service.generate_video(
                prompt="Sunset over ocean waves"
            )
            
            assert "taskId" in result
            assert result["duration"] == 5  # 默认时长
            assert result["resolution"] == "1080p"  # 默认分辨率
    
    @pytest.mark.asyncio
    async def test_generate_video_custom_resolution(self, ai_service):
        """TC-AI-VIDEO-003: 视频生成 - 自定义时长和分辨率"""
        mock_response = {
            "task_id": "sora-task-789",
            "estimated_time": 120
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await ai_service.generate_video(
                prompt="Cyberpunk city at night",
                duration=30,
                resolution="4k"
            )
            
            assert result["duration"] == 30
            assert result["resolution"] == "4k"
    
    @pytest.mark.asyncio
    async def test_generate_video_empty_prompt(self, ai_service):
        """TC-AI-VIDEO-004: 视频生成 - 空提示词验证"""
        with pytest.raises(ValueError, match="提示词不能为空"):
            await ai_service.generate_video(prompt="")
        
        with pytest.raises(ValueError, match="提示词不能为空"):
            await ai_service.generate_video(prompt="   ")
    
    @pytest.mark.asyncio
    async def test_generate_video_invalid_duration(self, ai_service):
        """TC-AI-VIDEO-005: 视频生成 - 无效时长验证"""
        with pytest.raises(ValueError, match="不支持的时长"):
            await ai_service.generate_video(
                prompt="Test prompt",
                duration=7  # 不支持的时长
            )
    
    @pytest.mark.asyncio
    async def test_generate_video_invalid_resolution(self, ai_service):
        """TC-AI-VIDEO-006: 视频生成 - 无效分辨率验证"""
        with pytest.raises(ValueError, match="不支持的分辨率"):
            await ai_service.generate_video(
                prompt="Test prompt",
                resolution="2k"  # 不支持的分辨率
            )
    
    @pytest.mark.asyncio
    async def test_generate_video_api_error(self, ai_service):
        """TC-AI-VIDEO-007: 视频生成 - API 错误处理"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 500
            mock_response_obj.text = "Internal Server Error"
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception, match="Sora API 返回错误"):
                await ai_service.generate_video(prompt="Test prompt")


class TestAIVideoServiceStatus:
    """AI 视频服务 - 状态查询测试"""
    
    @pytest.fixture
    def ai_service(self):
        """创建 AI 视频服务实例"""
        return AIVideoService()
    
    @pytest.mark.asyncio
    async def test_query_status_success(self, ai_service):
        """TC-AI-VIDEO-008: 查询状态 - 正常流程"""
        mock_response = {
            "status": "processing",
            "progress": 45,
            "message": "Rendering frames..."
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await ai_service.query_video_status("video-task-123")
            
            assert result["taskId"] == "video-task-123"
            assert result["status"] == "processing"
            assert result["progress"] == 45
    
    @pytest.mark.asyncio
    async def test_query_status_completed(self, ai_service):
        """TC-AI-VIDEO-009: 查询状态 - 已完成"""
        mock_response = {
            "status": "completed",
            "progress": 100,
            "message": "Video generated successfully",
            "video_url": "http://example.com/video.mp4",
            "video_id": "video-123"
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await ai_service.query_video_status("video-task-123")
            
            assert result["status"] == "completed"
            assert result["progress"] == 100
            assert result["video_url"] is not None
    
    @pytest.mark.asyncio
    async def test_query_status_empty_task_id(self, ai_service):
        """TC-AI-VIDEO-010: 查询状态 - 空任务 ID 验证"""
        with pytest.raises(ValueError, match="任务 ID 不能为空"):
            await ai_service.query_video_status("")


class TestAIVideoServiceConfig:
    """AI 视频服务 - 配置信息测试"""
    
    @pytest.fixture
    def ai_service(self):
        """创建 AI 视频服务实例"""
        return AIVideoService()
    
    def test_get_supported_resolutions(self, ai_service):
        """TC-AI-VIDEO-011: 获取支持的分辨率列表"""
        resolutions = ai_service.get_supported_resolutions()
        assert isinstance(resolutions, list)
        assert "720p" in resolutions
        assert "1080p" in resolutions
        assert "4k" in resolutions
    
    def test_get_supported_durations(self, ai_service):
        """TC-AI-VIDEO-012: 获取支持的时长列表"""
        durations = ai_service.get_supported_durations()
        assert isinstance(durations, list)
        assert 5 in durations
        assert 10 in durations
        assert 15 in durations
        assert 30 in durations


class TestAIVideoServiceDownload:
    """AI 视频服务 - 视频下载测试"""
    
    @pytest.fixture
    def ai_service(self):
        """创建 AI 视频服务实例"""
        return AIVideoService()
    
    @pytest.mark.asyncio
    async def test_download_video_not_completed(self, ai_service):
        """TC-AI-VIDEO-013: 视频下载 - 未完成视频验证"""
        async def mock_query(*args, **kwargs):
            return {
                "status": "processing",
                "progress": 50
            }
        
        with patch.object(ai_service, 'query_video_status', mock_query):
            with pytest.raises(ValueError, match="视频尚未完成"):
                await ai_service.download_video("video-123")
    
    @pytest.mark.asyncio
    async def test_download_video_empty_id(self, ai_service):
        """TC-AI-VIDEO-014: 视频下载 - 空视频 ID 验证"""
        with pytest.raises(ValueError, match="视频 ID 不能为空"):
            await ai_service.download_video("")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
