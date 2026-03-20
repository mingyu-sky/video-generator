"""
AI 剧本生成服务测试
"""
import pytest
import os
import sys
import json
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.script_service import ScriptService


@pytest.fixture
def script_service():
    """创建剧本服务实例"""
    return ScriptService()


@pytest.fixture
def cleanup_scripts(script_service):
    """测试后清理生成的剧本文件"""
    script_ids = []
    yield script_ids
    # 清理测试生成的剧本
    for script_id in script_ids:
        script_path = os.path.join(script_service.base_dir, f"{script_id}.json")
        if os.path.exists(script_path):
            os.remove(script_path)


class TestScriptServiceInit:
    """测试剧本服务初始化"""
    
    def test_service_initialization(self, script_service):
        """测试服务正常初始化"""
        assert script_service is not None
        assert hasattr(script_service, 'base_dir')
        assert hasattr(script_service, 'supported_genres')
        assert os.path.exists(script_service.base_dir)
    
    def test_supported_genres(self, script_service):
        """测试支持的题材类型"""
        expected_genres = ["言情", "悬疑", "喜剧", "动作", "科幻", "古装", "都市", "奇幻"]
        for genre in expected_genres:
            assert genre in script_service.supported_genres


class TestScriptGeneration:
    """测试剧本生成功能"""
    
    @pytest.mark.asyncio
    async def test_generate_script_basic(self, script_service, cleanup_scripts):
        """测试基本剧本生成"""
        theme = "霸道总裁爱上我"
        script_data = await script_service.generate_script(
            theme=theme,
            episodes=80,
            genre="言情"
        )
        
        # 验证返回数据结构
        assert script_data is not None
        assert "scriptId" in script_data
        assert "title" in script_data
        assert "episodes" in script_data
        assert "genre" in script_data
        assert "createdAt" in script_data
        assert "scenes" in script_data
        
        # 验证内容
        assert script_data["title"] == theme
        assert script_data["episodes"] == 80
        assert script_data["genre"] == "言情"
        assert len(script_data["scenes"]) > 0
        
        # 记录 script_id 用于清理
        cleanup_scripts.append(script_data["scriptId"])
    
    @pytest.mark.asyncio
    async def test_generate_script_default_values(self, script_service, cleanup_scripts):
        """测试使用默认值生成剧本"""
        theme = "都市爱情故事"
        script_data = await script_service.generate_script(theme=theme)
        
        # 验证默认值
        assert script_data["episodes"] == 80
        assert script_data["genre"] == "言情"
        
        cleanup_scripts.append(script_data["scriptId"])
    
    @pytest.mark.asyncio
    async def test_generate_script_different_genres(self, script_service, cleanup_scripts):
        """测试不同题材的剧本生成"""
        test_cases = [
            ("悬疑推理", "悬疑"),
            ("搞笑日常", "喜剧"),
            ("武林争霸", "武侠"),
            ("未来世界", "科幻"),
        ]
        
        for theme, genre in test_cases:
            script_data = await script_service.generate_script(
                theme=theme,
                episodes=50,
                genre=genre
            )
            
            assert script_data["genre"] == genre
            assert script_data["episodes"] == 50
            cleanup_scripts.append(script_data["scriptId"])
    
    @pytest.mark.asyncio
    async def test_generate_script_scene_structure(self, script_service, cleanup_scripts):
        """测试生成场景的结构"""
        script_data = await script_service.generate_script(
            theme="测试剧本",
            episodes=1,
            genre="言情"
        )
        
        # 验证场景结构
        scenes = script_data["scenes"]
        assert len(scenes) > 0
        
        for scene in scenes:
            # 验证必需字段
            assert "sceneId" in scene
            assert "episode" in scene
            assert "location" in scene
            assert "time" in scene
            assert "characters" in scene
            assert "description" in scene
            assert "dialogue" in scene
            assert "duration" in scene
            
            # 验证字段类型
            assert isinstance(scene["characters"], list)
            assert isinstance(scene["dialogue"], list)
            assert isinstance(scene["duration"], (int, float))
            
            # 验证 duration 范围
            assert 10 <= scene["duration"] <= 30
            
            # 验证对话结构
            for dialogue in scene["dialogue"]:
                assert "character" in dialogue
                assert "text" in dialogue
                assert "emotion" in dialogue
        
        cleanup_scripts.append(script_data["scriptId"])


class TestScriptOperations:
    """测试剧本操作功能"""
    
    @pytest.mark.asyncio
    async def test_get_script(self, script_service, cleanup_scripts):
        """测试获取剧本详情"""
        # 先生成剧本
        script_data = await script_service.generate_script(
            theme="测试获取",
            episodes=10,
            genre="都市"
        )
        script_id = script_data["scriptId"]
        cleanup_scripts.append(script_id)
        
        # 获取剧本
        retrieved_data = script_service.get_script(script_id)
        
        assert retrieved_data is not None
        assert retrieved_data["scriptId"] == script_id
        assert retrieved_data["title"] == "测试获取"
    
    def test_get_nonexistent_script(self, script_service):
        """测试获取不存在的剧本"""
        result = script_service.get_script("nonexistent-id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_expand_script(self, script_service, cleanup_scripts):
        """测试扩展剧本"""
        # 先生成初始剧本
        script_data = await script_service.generate_script(
            theme="扩展测试",
            episodes=10,
            genre="言情"
        )
        script_id = script_data["scriptId"]
        cleanup_scripts.append(script_id)
        
        # 扩展剧本
        expanded_data = await script_service.expand_script(
            script_id=script_id,
            target_episodes=20
        )
        
        assert expanded_data["episodes"] == 20
        assert len(expanded_data["scenes"]) > len(script_data["scenes"])
    
    @pytest.mark.asyncio
    async def test_expand_script_invalid_target(self, script_service, cleanup_scripts):
        """测试无效的扩展目标"""
        # 先生成初始剧本
        script_data = await script_service.generate_script(
            theme="扩展测试",
            episodes=10,
            genre="言情"
        )
        script_id = script_data["scriptId"]
        cleanup_scripts.append(script_id)
        
        # 尝试扩展到更少集数，应该抛出异常
        with pytest.raises(ValueError, match="必须大于当前集数"):
            await script_service.expand_script(
                script_id=script_id,
                target_episodes=5
            )
    
    def test_list_scripts(self, script_service, cleanup_scripts):
        """测试获取剧本列表"""
        scripts = script_service.list_scripts(limit=10)
        
        assert isinstance(scripts, list)
        # 验证列表中的剧本结构
        for script in scripts:
            assert "scriptId" in script
            assert "title" in script
            assert "episodes" in script
            assert "genre" in script
    
    @pytest.mark.asyncio
    async def test_delete_script(self, script_service, cleanup_scripts):
        """测试删除剧本"""
        # 先生成剧本
        script_data = await script_service.generate_script(
            theme="删除测试",
            episodes=5,
            genre="喜剧"
        )
        script_id = script_data["scriptId"]
        
        # 删除剧本
        success = script_service.delete_script(script_id)
        assert success is True
        
        # 验证已删除
        retrieved = script_service.get_script(script_id)
        assert retrieved is None
        
        # 从清理列表移除（已删除）
        if script_id in cleanup_scripts:
            cleanup_scripts.remove(script_id)
    
    def test_delete_nonexistent_script(self, script_service):
        """测试删除不存在的剧本"""
        success = script_service.delete_script("nonexistent-id")
        assert success is False


class TestScriptValidation:
    """测试剧本验证功能"""
    
    @pytest.mark.asyncio
    async def test_invalid_genre_handling(self, script_service, cleanup_scripts):
        """测试无效题材处理"""
        script_data = await script_service.generate_script(
            theme="测试",
            episodes=10,
            genre="不存在的题材"
        )
        
        # 应该使用默认题材
        assert script_data["genre"] == "言情"
        cleanup_scripts.append(script_data["scriptId"])
    
    @pytest.mark.asyncio
    async def test_scene_id_format(self, script_service, cleanup_scripts):
        """测试场景 ID 格式"""
        script_data = await script_service.generate_script(
            theme="格式测试",
            episodes=5,
            genre="言情"
        )
        
        for scene in script_data["scenes"]:
            scene_id = scene["sceneId"]
            # 验证场景 ID 格式：SXXEXX-XXX
            assert scene_id.startswith("S")
            assert "-" in scene_id
            parts = scene_id.split("-")
            assert len(parts) == 2
            assert len(parts[1]) == 3  # 场景编号 3 位
        
        cleanup_scripts.append(script_data["scriptId"])


class TestScriptPersistence:
    """测试剧本持久化功能"""
    
    @pytest.mark.asyncio
    async def test_script_file_saved(self, script_service, cleanup_scripts):
        """测试剧本文件正确保存"""
        script_data = await script_service.generate_script(
            theme="持久化测试",
            episodes=3,
            genre="言情"
        )
        script_id = script_data["scriptId"]
        cleanup_scripts.append(script_id)
        
        # 验证文件存在
        script_path = os.path.join(script_service.base_dir, f"{script_id}.json")
        assert os.path.exists(script_path)
        
        # 验证文件内容
        with open(script_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data["scriptId"] == script_id
        assert saved_data["title"] == "持久化测试"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
