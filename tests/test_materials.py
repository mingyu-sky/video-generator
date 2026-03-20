"""
素材管理服务测试
测试素材库模块的核心功能
"""
import pytest
import os
import sys
import json
import shutil
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.material_service import MaterialService


@pytest.fixture
def material_service():
    """创建素材服务实例"""
    return MaterialService()


@pytest.fixture
def cleanup_materials(material_service):
    """测试后清理生成的素材文件"""
    material_ids = []
    yield material_ids
    # 清理测试生成的素材
    for material_id in material_ids:
        # 删除元数据文件
        meta_paths = [
            os.path.join(material_service.base_dir, "music", f"{material_id}.json"),
            os.path.join(material_service.base_dir, "templates", f"{material_id}.json"),
            os.path.join(material_service.base_dir, "uploads", f"{material_id}.json"),
        ]
        for path in meta_paths:
            if os.path.exists(path):
                os.remove(path)
        
        # 删除上传文件
        upload_dir = os.path.join(material_service.base_dir, "uploads")
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                if filename.startswith(f"{material_id}_"):
                    os.remove(os.path.join(upload_dir, filename))


class TestMaterialServiceInit:
    """测试素材服务初始化"""
    
    def test_service_initialization(self, material_service):
        """测试服务正常初始化"""
        assert material_service is not None
        assert hasattr(material_service, 'base_dir')
        assert hasattr(material_service, 'music_genres')
        assert hasattr(material_service, 'music_moods')
        assert hasattr(material_service, 'template_types')
    
    def test_directories_created(self, material_service):
        """测试目录自动创建"""
        assert os.path.exists(material_service.base_dir)
        assert os.path.exists(os.path.join(material_service.base_dir, "music"))
        assert os.path.exists(os.path.join(material_service.base_dir, "templates"))
        assert os.path.exists(os.path.join(material_service.base_dir, "uploads"))
    
    def test_music_genres(self, material_service):
        """测试音乐类型列表"""
        expected_genres = ["流行", "摇滚", "电子", "古典", "爵士", "民谣", "说唱", "轻音乐"]
        for genre in expected_genres:
            assert genre in material_service.music_genres
    
    def test_music_moods(self, material_service):
        """测试音乐情绪列表"""
        expected_moods = ["欢快", "悲伤", "激昂", "平静", "浪漫", "紧张", "温馨", "励志"]
        for mood in expected_moods:
            assert mood in material_service.music_moods
    
    def test_template_types(self, material_service):
        """测试模板类型列表"""
        expected_types = ["片头", "片尾", "转场", "字幕", "特效", "滤镜"]
        for t in expected_types:
            assert t in material_service.template_types


class TestMusicList:
    """测试音乐列表功能"""
    
    def test_get_music_list_empty(self, material_service):
        """测试空音乐列表"""
        result = material_service.get_music_list()
        assert result is not None
        assert result["total"] == 0
        assert result["musicList"] == []
        assert result["page"] == 1
        assert result["pageSize"] == 20
    
    def test_get_music_list_with_pagination(self, material_service):
        """测试分页参数"""
        result = material_service.get_music_list(page=1, page_size=10)
        assert result["page"] == 1
        assert result["pageSize"] == 10
        assert "totalPages" in result
    
    def test_get_music_list_returns_genres_and_moods(self, material_service):
        """测试返回类型和情绪列表"""
        result = material_service.get_music_list()
        assert "genres" in result
        assert "moods" in result
        assert len(result["genres"]) > 0
        assert len(result["moods"]) > 0


class TestTemplatesList:
    """测试模板列表功能"""
    
    def test_get_templates_list_empty(self, material_service):
        """测试空模板列表"""
        result = material_service.get_templates_list()
        assert result is not None
        assert result["total"] == 0
        assert result["templates"] == []
        assert result["types"] == ["片头", "片尾", "转场", "字幕", "特效", "滤镜"]
    
    def test_get_templates_list_with_type_filter(self, material_service):
        """测试类型筛选"""
        result = material_service.get_templates_list(type="片头")
        assert result is not None
        assert "templates" in result
        assert "types" in result


class TestUploadMaterial:
    """测试素材上传功能"""
    
    def test_upload_music_material(self, material_service, cleanup_materials):
        """测试上传音乐素材"""
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mp3', delete=False) as f:
            f.write("test music content")
            temp_file = f.name
        
        try:
            result = material_service.upload_material(
                file_path=temp_file,
                material_type="music",
                category="流行",
                tags=["欢快", "励志"],
                description="测试音乐"
            )
            
            assert result is not None
            assert "materialId" in result
            assert result["materialId"].startswith("mat-")
            assert result["fileName"] == os.path.basename(temp_file)
            assert result["materialType"] == "music"
            assert result["category"] == "流行"
            assert result["fileSize"] > 0
            
            cleanup_materials.append(result["materialId"])
        finally:
            os.unlink(temp_file)
    
    def test_upload_template_material(self, material_service, cleanup_materials):
        """测试上传模板素材"""
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"template": "test"}, f)
            temp_file = f.name
        
        try:
            result = material_service.upload_material(
                file_path=temp_file,
                material_type="template",
                category="片头",
                tags=["现代", "简洁"],
                description="测试模板"
            )
            
            assert result is not None
            assert "materialId" in result
            assert result["materialId"].startswith("mat-")
            assert result["materialType"] == "template"
            assert result["category"] == "片头"
            
            cleanup_materials.append(result["materialId"])
        finally:
            os.unlink(temp_file)
    
    def test_upload_other_material(self, material_service, cleanup_materials):
        """测试上传其他类型素材"""
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            result = material_service.upload_material(
                file_path=temp_file,
                material_type="other",
                category="文档",
                tags=["测试"],
                description="测试文档"
            )
            
            assert result is not None
            assert result["materialType"] == "other"
            
            cleanup_materials.append(result["materialId"])
        finally:
            os.unlink(temp_file)
    
    def test_upload_file_not_found(self, material_service):
        """测试文件不存在错误"""
        with pytest.raises(FileNotFoundError):
            material_service.upload_material(
                file_path="/nonexistent/file.mp3",
                material_type="music",
                category="流行"
            )
    
    def test_upload_invalid_material_type(self, material_service):
        """测试无效素材类型"""
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test")
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="素材类型必须是"):
                material_service.upload_material(
                    file_path=temp_file,
                    material_type="invalid",
                    category="测试"
                )
        finally:
            os.unlink(temp_file)
    
    def test_upload_missing_category(self, material_service):
        """测试缺少分类参数"""
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test")
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="分类不能为空"):
                material_service.upload_material(
                    file_path=temp_file,
                    material_type="music",
                    category=""
                )
        finally:
            os.unlink(temp_file)
    
    def test_upload_with_empty_tags(self, material_service, cleanup_materials):
        """测试空标签列表"""
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mp3', delete=False) as f:
            f.write("test music")
            temp_file = f.name
        
        try:
            result = material_service.upload_material(
                file_path=temp_file,
                material_type="music",
                category="流行",
                tags=[]
            )
            
            assert result is not None
            assert "materialId" in result
            cleanup_materials.append(result["materialId"])
        finally:
            os.unlink(temp_file)


class TestPreviewMaterial:
    """测试素材预览功能"""
    
    def test_preview_music_material(self, material_service, cleanup_materials):
        """测试预览音乐素材"""
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mp3', delete=False) as f:
            f.write("test music content")
            temp_file = f.name
        
        try:
            upload_result = material_service.upload_material(
                file_path=temp_file,
                material_type="music",
                category="流行",
                tags=["欢快"],
                description="测试音乐"
            )
            
            material_id = upload_result["materialId"]
            cleanup_materials.append(material_id)
            
            # 测试预览
            preview = material_service.preview_material(material_id)
            
            assert preview is not None
            assert preview["materialId"] == material_id
            assert preview["materialType"] == "music"
            assert preview["genre"] == "流行"
            assert "previewUrl" in preview
            assert preview["status"] == "active"
        finally:
            os.unlink(temp_file)
    
    def test_preview_template_material(self, material_service, cleanup_materials):
        """测试预览模板素材"""
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"template": "test"}, f)
            temp_file = f.name
        
        try:
            upload_result = material_service.upload_material(
                file_path=temp_file,
                material_type="template",
                category="片头",
                tags=["现代"]
            )
            
            material_id = upload_result["materialId"]
            cleanup_materials.append(material_id)
            
            # 测试预览
            preview = material_service.preview_material(material_id)
            
            assert preview is not None
            assert preview["materialType"] == "template"
            assert preview["templateType"] == "片头"
        finally:
            os.unlink(temp_file)
    
    def test_preview_nonexistent_material(self, material_service):
        """测试预览不存在的素材"""
        with pytest.raises(FileNotFoundError):
            material_service.preview_material("mat-nonexistent")
    
    def test_preview_empty_material_id(self, material_service):
        """测试空素材 ID"""
        with pytest.raises(ValueError, match="素材 ID 不能为空"):
            material_service.preview_material("")


class TestMaterialStats:
    """测试素材统计功能"""
    
    def test_get_material_stats(self, material_service):
        """测试获取素材统计"""
        stats = material_service.get_material_stats()
        
        assert stats is not None
        assert "totalMusic" in stats
        assert "totalTemplates" in stats
        assert "totalUploads" in stats
        assert "totalStorageBytes" in stats
        assert "totalStorageMB" in stats
    
    def test_stats_initial_values(self, material_service):
        """测试初始统计值"""
        stats = material_service.get_material_stats()
        assert stats["totalMusic"] >= 0
        assert stats["totalTemplates"] >= 0
        assert stats["totalUploads"] >= 0


class TestDeleteMaterial:
    """测试素材删除功能"""
    
    def test_delete_music_material(self, material_service):
        """测试删除音乐素材"""
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mp3', delete=False) as f:
            f.write("test music content")
            temp_file = f.name
        
        try:
            upload_result = material_service.upload_material(
                file_path=temp_file,
                material_type="music",
                category="流行",
                tags=["欢快"]
            )
            
            material_id = upload_result["materialId"]
            
            # 测试删除
            delete_result = material_service.delete_material(material_id)
            
            assert delete_result is not None
            assert delete_result["success"] == True
            assert "已删除" in delete_result["message"]
        finally:
            os.unlink(temp_file)
    
    def test_delete_nonexistent_material(self, material_service):
        """测试删除不存在的素材"""
        result = material_service.delete_material("mat-nonexistent")
        assert result["success"] == True  # 应该不报错，只是没有实际删除


class TestMusicListWithFilter:
    """测试音乐列表筛选功能"""
    
    def test_music_list_genre_filter(self, material_service, cleanup_materials):
        """测试音乐类型筛选"""
        # 上传不同风格的音乐
        for genre in ["流行", "摇滚", "古典"]:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mp3', delete=False) as f:
                f.write(f"test {genre}")
                temp_file = f.name
            
            try:
                result = material_service.upload_material(
                    file_path=temp_file,
                    material_type="music",
                    category=genre,
                    tags=["测试"]
                )
                cleanup_materials.append(result["materialId"])
            finally:
                os.unlink(temp_file)
        
        # 测试筛选
        result = material_service.get_music_list(genre="流行")
        assert result["total"] >= 1
        
        for music in result["musicList"]:
            if music.get("genre"):
                assert music["genre"] == "流行"
    
    def test_music_list_mood_filter(self, material_service, cleanup_materials):
        """测试音乐情绪筛选"""
        # 上传不同情绪的音乐
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mp3', delete=False) as f:
            f.write("test happy music")
            temp_file = f.name
        
        try:
            result = material_service.upload_material(
                file_path=temp_file,
                material_type="music",
                category="流行",
                tags=["欢快"]
            )
            cleanup_materials.append(result["materialId"])
        finally:
            os.unlink(temp_file)
        
        # 测试筛选
        result = material_service.get_music_list(mood="欢快")
        assert result["total"] >= 1
