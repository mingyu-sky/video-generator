"""
模板管理服务单元测试
测试模板的创建、查询、删除、应用等功能
"""
import pytest
import os
import sys
import json
import shutil
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.template_service import TemplateService


@pytest.fixture
def template_service():
    """创建模板服务实例"""
    # 使用测试目录
    service = TemplateService()
    service.base_dir = os.path.join(os.path.dirname(__file__), "test_templates")
    
    # 创建必要的目录
    os.makedirs(service.base_dir, exist_ok=True)
    os.makedirs(os.path.join(service.base_dir, "public"), exist_ok=True)
    os.makedirs(os.path.join(service.base_dir, "private"), exist_ok=True)
    os.makedirs(os.path.join(service.base_dir, "records"), exist_ok=True)
    
    yield service
    
    # 清理测试目录
    if os.path.exists(service.base_dir):
        shutil.rmtree(service.base_dir)


@pytest.fixture
def sample_template_data():
    """样本模板数据"""
    return {
        "name": "测试模板",
        "description": "这是一个测试用的视频生成模板",
        "steps": [
            {
                "stepType": "script",
                "config": {
                    "theme": "科幻",
                    "duration": 60
                },
                "order": 0
            },
            {
                "stepType": "storyboard",
                "config": {
                    "shotStyle": "电影感",
                    "aspectRatio": "16:9"
                },
                "order": 1
            },
            {
                "stepType": "audio",
                "config": {
                    "voice": "zh-CN-XiaoxiaoNeural",
                    "speed": 1.0
                },
                "order": 2
            },
            {
                "stepType": "video",
                "config": {
                    "resolution": "1080p",
                    "fps": 30
                },
                "order": 3
            }
        ],
        "is_public": False
    }


class TestTemplateServiceInit:
    """测试模板服务初始化"""
    
    def test_service_initialization(self, template_service):
        """测试服务正常初始化"""
        assert template_service is not None
        assert hasattr(template_service, 'base_dir')
        assert os.path.exists(template_service.base_dir)
        assert os.path.exists(os.path.join(template_service.base_dir, "public"))
        assert os.path.exists(os.path.join(template_service.base_dir, "private"))
    
    def test_directory_structure(self, template_service):
        """测试目录结构正确创建"""
        assert os.path.isdir(os.path.join(template_service.base_dir, "public"))
        assert os.path.isdir(os.path.join(template_service.base_dir, "private"))


class TestCreateTemplate:
    """测试创建模板功能"""
    
    def test_create_template_basic(self, template_service, sample_template_data):
        """测试基本创建模板"""
        template = template_service.create_template(
            name=sample_template_data["name"],
            description=sample_template_data["description"],
            steps=sample_template_data["steps"],
            is_public=sample_template_data["is_public"]
        )
        
        # 验证返回数据
        assert template is not None
        assert "templateId" in template
        assert template["templateId"].startswith("tmpl-")
        assert template["name"] == sample_template_data["name"]
        assert template["description"] == sample_template_data["description"]
        assert len(template["steps"]) == len(sample_template_data["steps"])
        assert template["isPublic"] == sample_template_data["is_public"]
        assert "createdAt" in template
        assert "updatedAt" in template
        assert template["version"] == "1.0.0"
        
        # 验证文件已保存
        template_path = template_service._get_template_path(
            template["templateId"], 
            sample_template_data["is_public"]
        )
        assert os.path.exists(template_path)
    
    def test_create_template_public(self, template_service):
        """测试创建公开模板"""
        template = template_service.create_template(
            name="公开模板",
            description="这是一个公开模板",
            steps=[{"stepType": "script", "config": {}, "order": 0}],
            is_public=True
        )
        
        assert template["isPublic"] is True
        template_path = template_service._get_template_path(template["templateId"], True)
        assert os.path.exists(template_path)
    
    def test_create_template_empty_name(self, template_service):
        """测试创建模板 - 名称为空"""
        with pytest.raises(ValueError, match="模板名称不能为空"):
            template_service.create_template(
                name="",
                description="测试",
                steps=[{"stepType": "script", "config": {}, "order": 0}]
            )
    
    def test_create_template_empty_steps(self, template_service):
        """测试创建模板 - 步骤为空"""
        with pytest.raises(ValueError, match="模板步骤不能为空"):
            template_service.create_template(
                name="测试",
                description="测试",
                steps=[]
            )
    
    def test_create_template_missing_step_type(self, template_service):
        """测试创建模板 - 步骤缺少 stepType"""
        with pytest.raises(ValueError, match="缺少 stepType 字段"):
            template_service.create_template(
                name="测试",
                description="测试",
                steps=[{"config": {}, "order": 0}]  # 缺少 stepType
            )


class TestGetTemplates:
    """测试获取模板列表功能"""
    
    def test_get_templates_empty(self, template_service):
        """测试获取空列表"""
        result = template_service.get_templates(page=1, page_size=20)
        
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["pageSize"] == 20
        assert result["totalPages"] == 0
        assert result["templates"] == []
    
    def test_get_templates_with_data(self, template_service, sample_template_data):
        """测试获取模板列表 - 有数据"""
        # 创建多个模板
        templates_created = []
        for i in range(5):
            template = template_service.create_template(
                name=f"测试模板{i+1}",
                description=f"描述{i+1}",
                steps=sample_template_data["steps"],
                is_public=(i % 2 == 0)  # 交替公开/私有
            )
            templates_created.append(template)
        
        result = template_service.get_templates(page=1, page_size=10)
        
        assert result["total"] == 5
        assert result["page"] == 1
        assert result["pageSize"] == 10
        assert len(result["templates"]) == 5
    
    def test_get_templates_pagination(self, template_service, sample_template_data):
        """测试分页功能"""
        # 创建 15 个模板
        for i in range(15):
            template_service.create_template(
                name=f"模板{i+1}",
                description=f"描述{i+1}",
                steps=sample_template_data["steps"],
                is_public=False
            )
        
        # 第一页
        result1 = template_service.get_templates(page=1, page_size=10)
        assert result1["total"] == 15
        assert result1["totalPages"] == 2
        assert len(result1["templates"]) == 10
        
        # 第二页
        result2 = template_service.get_templates(page=2, page_size=10)
        assert result2["total"] == 15
        assert len(result2["templates"]) == 5
    
    def test_get_templates_filter_public(self, template_service, sample_template_data):
        """测试筛选公开模板"""
        # 创建公开和私有模板
        for i in range(3):
            template_service.create_template(
                name=f"公开模板{i+1}",
                description="公开",
                steps=sample_template_data["steps"],
                is_public=True
            )
        
        for i in range(2):
            template_service.create_template(
                name=f"私有模板{i+1}",
                description="私有",
                steps=sample_template_data["steps"],
                is_public=False
            )
        
        # 只获取公开模板
        result = template_service.get_templates(is_public=True)
        assert result["total"] == 3
        for tmpl in result["templates"]:
            assert tmpl["isPublic"] is True
    
    def test_get_templates_filter_private(self, template_service, sample_template_data):
        """测试筛选私有模板"""
        # 创建公开和私有模板
        for i in range(2):
            template_service.create_template(
                name=f"公开模板{i+1}",
                description="公开",
                steps=sample_template_data["steps"],
                is_public=True
            )
        
        for i in range(3):
            template_service.create_template(
                name=f"私有模板{i+1}",
                description="私有",
                steps=sample_template_data["steps"],
                is_public=False
            )
        
        # 只获取私有模板
        result = template_service.get_templates(is_public=False)
        assert result["total"] == 3
        for tmpl in result["templates"]:
            assert tmpl["isPublic"] is False


class TestGetTemplate:
    """测试获取模板详情功能"""
    
    def test_get_template_success(self, template_service, sample_template_data):
        """测试获取模板详情 - 成功"""
        created = template_service.create_template(
            name="详情测试",
            description="测试详情",
            steps=sample_template_data["steps"],
            is_public=False
        )
        
        template = template_service.get_template(created["templateId"])
        
        assert template["templateId"] == created["templateId"]
        assert template["name"] == "详情测试"
        assert template["description"] == "测试详情"
        assert len(template["steps"]) == len(sample_template_data["steps"])
    
    def test_get_template_not_found(self, template_service):
        """测试获取模板详情 - 不存在"""
        with pytest.raises(FileNotFoundError, match="模板不存在"):
            template_service.get_template("tmpl-nonexistent")
    
    def test_get_template_empty_id(self, template_service):
        """测试获取模板详情 - ID 为空"""
        with pytest.raises(ValueError, match="模板 ID 不能为空"):
            template_service.get_template("")


class TestDeleteTemplate:
    """测试删除模板功能"""
    
    def test_delete_template_success(self, template_service, sample_template_data):
        """测试删除模板 - 成功"""
        created = template_service.create_template(
            name="删除测试",
            description="测试删除",
            steps=sample_template_data["steps"],
            is_public=False
        )
        
        result = template_service.delete_template(created["templateId"])
        assert result is True
        
        # 验证文件已删除
        template_path = template_service._get_template_path(
            created["templateId"], 
            False
        )
        assert not os.path.exists(template_path)
    
    def test_delete_template_not_found(self, template_service):
        """测试删除模板 - 不存在"""
        with pytest.raises(FileNotFoundError, match="模板不存在"):
            template_service.delete_template("tmpl-nonexistent")
    
    def test_delete_template_empty_id(self, template_service):
        """测试删除模板 - ID 为空"""
        with pytest.raises(ValueError, match="模板 ID 不能为空"):
            template_service.delete_template("")


class TestApplyTemplate:
    """测试应用模板功能"""
    
    def test_apply_template_basic(self, template_service, sample_template_data):
        """测试基本应用模板"""
        created = template_service.create_template(
            name="应用测试",
            description="测试应用",
            steps=sample_template_data["steps"],
            is_public=False
        )
        
        result = template_service.apply_template(
            created["templateId"],
            video_id="video-123"
        )
        
        assert result is not None
        assert "applyId" in result
        assert result["applyId"].startswith("apply-")
        assert result["templateId"] == created["templateId"]
        assert result["templateName"] == "应用测试"
        assert result["videoId"] == "video-123"
        assert result["status"] == "ready"
        assert result["currentStep"] == 0
        assert len(result["steps"]) == len(sample_template_data["steps"])
        
        # 验证应用记录已保存
        records_dir = os.path.join(template_service.base_dir, "records")
        assert os.path.exists(records_dir)
        record_path = os.path.join(records_dir, f"{result['applyId']}.json")
        assert os.path.exists(record_path)
    
    def test_apply_template_without_video_id(self, template_service, sample_template_data):
        """测试应用模板 - 不提供视频 ID"""
        created = template_service.create_template(
            name="应用测试",
            description="测试应用",
            steps=sample_template_data["steps"],
            is_public=False
        )
        
        result = template_service.apply_template(created["templateId"])
        
        assert result["videoId"] is None
        assert result["status"] == "ready"
    
    def test_apply_template_not_found(self, template_service):
        """测试应用模板 - 模板不存在"""
        with pytest.raises(FileNotFoundError, match="模板不存在"):
            template_service.apply_template("tmpl-nonexistent")
    
    def test_apply_template_empty_id(self, template_service):
        """测试应用模板 - ID 为空"""
        with pytest.raises(ValueError, match="模板 ID 不能为空"):
            template_service.apply_template("")


class TestUpdateTemplate:
    """测试更新模板功能"""
    
    def test_update_template_name(self, template_service, sample_template_data):
        """测试更新模板名称"""
        created = template_service.create_template(
            name="原名",
            description="原描述",
            steps=sample_template_data["steps"],
            is_public=False
        )
        
        updated = template_service.update_template(
            created["templateId"],
            name="新名称"
        )
        
        assert updated["name"] == "新名称"
        assert updated["description"] == "原描述"
        assert updated["updatedAt"] != updated["createdAt"]
    
    def test_update_template_steps(self, template_service, sample_template_data):
        """测试更新模板步骤"""
        created = template_service.create_template(
            name="测试",
            description="测试",
            steps=sample_template_data["steps"],
            is_public=False
        )
        
        new_steps = [
            {"stepType": "video", "config": {"resolution": "4k"}, "order": 0}
        ]
        
        updated = template_service.update_template(
            created["templateId"],
            steps=new_steps
        )
        
        assert len(updated["steps"]) == 1
        assert updated["steps"][0]["stepType"] == "video"
    
    def test_update_template_visibility(self, template_service, sample_template_data):
        """测试更新模板公开状态"""
        created = template_service.create_template(
            name="测试",
            description="测试",
            steps=sample_template_data["steps"],
            is_public=False
        )
        
        # 从私有改为公开
        updated = template_service.update_template(
            created["templateId"],
            is_public=True
        )
        
        assert updated["isPublic"] is True
        
        # 验证文件已移动到公开目录
        public_path = template_service._get_template_path(created["templateId"], True)
        private_path = template_service._get_template_path(created["templateId"], False)
        
        assert os.path.exists(public_path)
        assert not os.path.exists(private_path)
    
    def test_update_template_empty_steps(self, template_service, sample_template_data):
        """测试更新模板 - 步骤为空"""
        created = template_service.create_template(
            name="测试",
            description="测试",
            steps=sample_template_data["steps"],
            is_public=False
        )
        
        with pytest.raises(ValueError, match="模板步骤不能为空"):
            template_service.update_template(
                created["templateId"],
                steps=[]
            )
