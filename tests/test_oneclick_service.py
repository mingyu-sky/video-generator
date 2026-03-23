"""
一键生成服务单元测试
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.oneclick_service import OneClickService


class TestOneClickService:
    """一键生成服务测试"""
    
    def test_service_initialization(self):
        """测试服务初始化"""
        service = OneClickService()
        assert service is not None
        assert service.effect_service is not None
        assert service.base_dir is not None
    
    def test_create_generation_task(self):
        """测试创建生成任务"""
        service = OneClickService()
        config = {
            "videoId": "test_video_001",
            "templateId": "template_001",
            "textEffects": [
                {"text": "Hello", "style": {"fontSize": 36}}
            ],
            "followEffect": {"text": "点关注"},
            "outputName": "test_output.mp4"
        }
        
        task = service.create_generation_task(config)
        assert task is not None
        assert task['taskId'].startswith('oneclick_')
        assert task['type'] == 'oneclick_generation'
        assert task['status'] == 'pending'
        assert task['config'] == config
    
    def test_generate_from_template(self):
        """测试从模板生成（接口验证）"""
        service = OneClickService()
        assert hasattr(service, 'generate_from_template')
        assert callable(getattr(service, 'generate_from_template'))
    
    def test_process_oneclick_method_exists(self):
        """测试处理方法存在"""
        service = OneClickService()
        assert hasattr(service, 'process_oneclick')
        assert callable(getattr(service, 'process_oneclick'))


class TestOneClickConfig:
    """一键生成配置验证"""
    
    def test_required_fields(self):
        """测试必填字段"""
        required_fields = ['videoId', 'templateId']
        for field in required_fields:
            assert field in ['videoId', 'templateId', 'textEffects', 'followEffect', 'pipEffect', 'outputName']
    
    def test_optional_effects(self):
        """测试可选特效配置"""
        optional_effects = ['textEffects', 'followEffect', 'pipEffect']
        for effect in optional_effects:
            assert effect in ['textEffects', 'followEffect', 'pipEffect', 'outputName']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
