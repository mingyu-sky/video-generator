"""
分镜设计服务测试
"""
import pytest
import os
import sys
import json
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.storyboard_service import StoryboardService


@pytest.fixture
def storyboard_service():
    """创建分镜服务实例"""
    return StoryboardService()


@pytest.fixture
def cleanup_storyboards(storyboard_service):
    """测试后清理生成的分镜文件"""
    storyboard_ids = []
    yield storyboard_ids
    # 清理测试生成的分镜
    for storyboard_id in storyboard_ids:
        storyboard_path = os.path.join(storyboard_service.base_dir, f"{storyboard_id}.json")
        if os.path.exists(storyboard_path):
            os.remove(storyboard_path)


class TestStoryboardServiceInit:
    """测试分镜服务初始化"""
    
    def test_service_initialization(self, storyboard_service):
        """测试服务正常初始化"""
        assert storyboard_service is not None
        assert hasattr(storyboard_service, 'base_dir')
        assert hasattr(storyboard_service, 'shot_types')
        assert os.path.exists(storyboard_service.base_dir)
    
    def test_shot_types(self, storyboard_service):
        """测试支持的镜头类型"""
        expected_types = ["wide", "closeup", "medium", "extreme"]
        for shot_type in expected_types:
            assert shot_type in storyboard_service.shot_types
    
    def test_default_shot_duration(self, storyboard_service):
        """测试默认镜头时长"""
        assert "wide" in storyboard_service.default_shot_duration
        assert "closeup" in storyboard_service.default_shot_duration
        assert "medium" in storyboard_service.default_shot_duration
        assert "extreme" in storyboard_service.default_shot_duration
        
        # 验证默认时长
        assert storyboard_service.default_shot_duration["wide"] == 5
        assert storyboard_service.default_shot_duration["closeup"] == 3
        assert storyboard_service.default_shot_duration["medium"] == 4
        assert storyboard_service.default_shot_duration["extreme"] == 2


class TestStoryboardGeneration:
    """测试分镜生成功能"""
    
    @pytest.mark.asyncio
    async def test_generate_storyboard_basic(self, storyboard_service, cleanup_storyboards):
        """测试基本分镜生成"""
        script_id = "test-script-001"
        script_content = """
        第一场：咖啡厅
        女主在吧台后忙碌，准备咖啡。
        
        第二场：男主登场
        男主推门而入，环顾四周。
        
        第三场：相遇
        两人目光交汇，时间仿佛静止。
        """
        
        storyboard = await storyboard_service.generate_storyboard(
            script_id=script_id,
            script_content=script_content,
            title="测试剧本"
        )
        
        # 验证返回数据结构
        assert storyboard is not None
        assert "storyboardId" in storyboard
        assert "scriptId" in storyboard
        assert "title" in storyboard
        assert "createdAt" in storyboard
        assert "scenes" in storyboard
        
        # 验证内容
        assert storyboard["scriptId"] == script_id
        assert storyboard["title"] == "测试剧本"
        assert len(storyboard["scenes"]) > 0
        
        # 验证场景结构
        for scene in storyboard["scenes"]:
            assert "sceneId" in scene
            assert "shots" in scene
            assert len(scene["shots"]) > 0
            
            # 验证镜头结构
            for shot in scene["shots"]:
                assert "shotId" in shot
                assert "type" in shot
                assert "description" in shot
                assert "duration" in shot
                assert "prompt" in shot
                assert shot["type"] in storyboard_service.shot_types
        
        # 记录 storyboard_id 用于清理
        cleanup_storyboards.append(storyboard["storyboardId"])
    
    @pytest.mark.asyncio
    async def test_generate_storyboard_without_title(self, storyboard_service, cleanup_storyboards):
        """测试不提供标题时的分镜生成"""
        script_id = "test-script-002"
        script_content = "这是一个测试剧本内容"
        
        storyboard = await storyboard_service.generate_storyboard(
            script_id=script_id,
            script_content=script_content
        )
        
        # 验证有默认标题
        assert "title" in storyboard
        assert storyboard["title"] == "未命名剧本"
        
        cleanup_storyboards.append(storyboard["storyboardId"])
    
    @pytest.mark.asyncio
    async def test_generate_storyboard_empty_script_id(self, storyboard_service):
        """测试空剧本 ID 的错误处理"""
        with pytest.raises(ValueError) as exc_info:
            await storyboard_service.generate_storyboard(script_id="")
        
        assert "剧本 ID 不能为空" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_storyboard_prompt_generation(self, storyboard_service, cleanup_storyboards):
        """测试 AI 绘画提示词生成"""
        script_id = "test-script-003"
        script_content = "咖啡厅场景，男女主角相遇"
        
        storyboard = await storyboard_service.generate_storyboard(
            script_id=script_id,
            script_content=script_content,
            title="提示词测试"
        )
        
        # 验证每个镜头都有提示词
        for scene in storyboard["scenes"]:
            for shot in scene["shots"]:
                assert "prompt" in shot
                assert len(shot["prompt"]) > 0
                # 提示词应该是英文（检查是否主要包含 ASCII 字符）
                prompt = shot["prompt"]
                ascii_chars = sum(1 for c in prompt if ord(c) < 128)
                assert ascii_chars / len(prompt) > 0.8  # 至少 80% 是 ASCII 字符
        
        cleanup_storyboards.append(storyboard["storyboardId"])


class TestStoryboardRetrieval:
    """测试分镜获取功能"""
    
    @pytest.mark.asyncio
    async def test_get_storyboard(self, storyboard_service, cleanup_storyboards):
        """测试获取分镜详情"""
        # 先生成一个分镜
        script_id = "test-script-004"
        script_content = "测试内容"
        
        created = await storyboard_service.generate_storyboard(
            script_id=script_id,
            script_content=script_content,
            title="获取测试"
        )
        
        storyboard_id = created["storyboardId"]
        cleanup_storyboards.append(storyboard_id)
        
        # 获取分镜
        retrieved = await storyboard_service.get_storyboard(storyboard_id)
        
        # 验证数据一致性
        assert retrieved["storyboardId"] == created["storyboardId"]
        assert retrieved["scriptId"] == created["scriptId"]
        assert retrieved["title"] == created["title"]
        assert len(retrieved["scenes"]) == len(created["scenes"])
    
    @pytest.mark.asyncio
    async def test_get_storyboard_not_found(self, storyboard_service):
        """测试获取不存在的分镜"""
        with pytest.raises(FileNotFoundError) as exc_info:
            await storyboard_service.get_storyboard("nonexistent-id")
        
        assert "分镜文件不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_storyboard_empty_id(self, storyboard_service):
        """测试空分镜 ID 的错误处理"""
        with pytest.raises(ValueError) as exc_info:
            await storyboard_service.get_storyboard("")
        
        assert "分镜 ID 不能为空" in str(exc_info.value)


class TestStoryboardList:
    """测试分镜列表功能"""
    
    @pytest.mark.asyncio
    async def test_list_storyboards(self, storyboard_service, cleanup_storyboards):
        """测试获取分镜列表"""
        # 创建几个测试分镜
        for i in range(3):
            storyboard = await storyboard_service.generate_storyboard(
                script_id=f"test-script-list-{i}",
                script_content=f"测试内容{i}",
                title=f"列表测试{i}"
            )
            cleanup_storyboards.append(storyboard["storyboardId"])
        
        # 获取列表
        result = await storyboard_service.list_storyboards(page=1, page_size=10)
        
        # 验证返回结构
        assert "total" in result
        assert "page" in result
        assert "pageSize" in result
        assert "storyboards" in result
        
        assert result["total"] >= 3
        assert result["page"] == 1
        assert result["pageSize"] == 10
        assert len(result["storyboards"]) >= 3
    
    @pytest.mark.asyncio
    async def test_list_storyboards_pagination(self, storyboard_service, cleanup_storyboards):
        """测试分镜列表分页"""
        # 创建测试分镜
        for i in range(5):
            storyboard = await storyboard_service.generate_storyboard(
                script_id=f"test-script-page-{i}",
                script_content=f"测试内容{i}",
                title=f"分页测试{i}"
            )
            cleanup_storyboards.append(storyboard["storyboardId"])
        
        # 第一页
        page1 = await storyboard_service.list_storyboards(page=1, page_size=2)
        assert page1["page"] == 1
        assert page1["pageSize"] == 2
        assert len(page1["storyboards"]) <= 2
        
        # 第二页
        page2 = await storyboard_service.list_storyboards(page=2, page_size=2)
        assert page2["page"] == 2
        assert page2["pageSize"] == 2
    
    @pytest.mark.asyncio
    async def test_list_storyboards_filter_by_script(self, storyboard_service, cleanup_storyboards):
        """测试按剧本 ID 过滤分镜"""
        script_id = "test-script-filter-unique"
        
        # 创建特定剧本的分镜
        storyboard = await storyboard_service.generate_storyboard(
            script_id=script_id,
            script_content="测试内容",
            title="过滤测试"
        )
        cleanup_storyboards.append(storyboard["storyboardId"])
        
        # 按剧本 ID 过滤
        result = await storyboard_service.list_storyboards(script_id=script_id)
        
        # 验证过滤结果
        assert result["total"] >= 1
        for sb in result["storyboards"]:
            assert sb["scriptId"] == script_id


class TestStoryboardDelete:
    """测试分镜删除功能"""
    
    @pytest.mark.asyncio
    async def test_delete_storyboard(self, storyboard_service):
        """测试删除分镜"""
        # 先生成一个分镜
        storyboard = await storyboard_service.generate_storyboard(
            script_id="test-script-delete",
            script_content="测试删除",
            title="删除测试"
        )
        
        storyboard_id = storyboard["storyboardId"]
        
        # 验证文件存在
        file_path = os.path.join(storyboard_service.base_dir, f"{storyboard_id}.json")
        assert os.path.exists(file_path)
        
        # 删除分镜
        success = await storyboard_service.delete_storyboard(storyboard_id)
        assert success is True
        
        # 验证文件已删除
        assert not os.path.exists(file_path)
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_storyboard(self, storyboard_service):
        """测试删除不存在的分镜"""
        success = await storyboard_service.delete_storyboard("nonexistent-id")
        assert success is False


class TestShotPromptGeneration:
    """测试镜头提示词生成功能"""
    
    @pytest.mark.asyncio
    async def test_generate_prompt_for_shot(self, storyboard_service):
        """测试为单个镜头生成提示词"""
        test_shots = [
            {"type": "wide", "description": "咖啡厅全景"},
            {"type": "closeup", "description": "女主特写"},
            {"type": "medium", "description": "两人对话"},
            {"type": "extreme", "description": "戒指细节"}
        ]
        
        for shot in test_shots:
            prompt = await storyboard_service._generate_prompt_for_shot(shot)
            
            assert prompt is not None
            assert len(prompt) > 0
            # 提示词应该包含镜头类型相关信息
            assert "shot" in prompt.lower() or "scene" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_generate_shot_prompts_full_storyboard(self, storyboard_service, cleanup_storyboards):
        """测试为完整分镜生成所有提示词"""
        storyboard = {
            "storyboardId": "test-sb-prompts",
            "scriptId": "test-script",
            "title": "提示词测试",
            "scenes": [
                {
                    "sceneId": "S01E01-001",
                    "shots": [
                        {"shotId": "SHOT-001", "type": "wide", "description": "场景 1"},
                        {"shotId": "SHOT-002", "type": "closeup", "description": "特写 1"}
                    ]
                },
                {
                    "sceneId": "S01E01-002",
                    "shots": [
                        {"shotId": "SHOT-003", "type": "medium", "description": "场景 2"}
                    ]
                }
            ]
        }
        
        # 生成提示词
        result = await storyboard_service.generate_shot_prompts(storyboard)
        
        # 验证所有镜头都有提示词
        total_shots = 0
        for scene in result["scenes"]:
            for shot in scene["shots"]:
                total_shots += 1
                assert "prompt" in shot
                assert len(shot["prompt"]) > 0
        
        assert total_shots == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
