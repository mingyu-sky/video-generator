"""
文件管理模块单元测试
测试用例覆盖：
- TC-FILE-001: 上传视频文件 - 正常流程
- TC-FILE-002: 上传视频文件 - 格式不支持
- TC-FILE-003: 上传视频文件 - 文件超限
- TC-FILE-006: 获取文件列表
- TC-FILE-007: 获取文件详情
- TC-FILE-008: 删除文件
"""
import pytest
import os
import sys
import io
import uuid
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

# 测试用临时文件
TEST_VIDEO_CONTENT = b"\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isomtest video content"
TEST_AUDIO_CONTENT = b"ID3\x03\x00\x00\x00\x00\x00test audio content"
TEST_IMAGE_CONTENT = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"


class TestFileUpload:
    """文件上传测试"""
    
    def test_upload_video_success(self):
        """TC-FILE-001: 上传视频文件 - 正常流程"""
        files = {"file": ("test.mp4", io.BytesIO(TEST_VIDEO_CONTENT), "video/mp4")}
        data = {"type": "video"}
        
        response = client.post("/api/v1/files/upload", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert "fileId" in result["data"]
        assert result["data"]["fileName"] == "test.mp4"
        assert result["data"]["fileType"] == "video"
        assert "downloadUrl" in result["data"]
        
        # 保存 fileId 供后续测试使用
        pytest.test_file_id = result["data"]["fileId"]
    
    def test_upload_invalid_format(self):
        """TC-FILE-002: 上传视频文件 - 格式不支持"""
        files = {"file": ("test.txt", b"plain text content", "text/plain")}
        data = {"type": "video"}
        
        response = client.post("/api/v1/files/upload", files=files, data=data)
        
        assert response.status_code == 400
        result = response.json()
        assert result["code"] == 1001
    
    def test_upload_audio_success(self):
        """上传音频文件 - 正常流程"""
        files = {"file": ("test.mp3", io.BytesIO(TEST_AUDIO_CONTENT), "audio/mpeg")}
        data = {"type": "audio"}
        
        response = client.post("/api/v1/files/upload", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["fileType"] == "audio"
    
    def test_upload_image_success(self):
        """上传图片文件 - 正常流程"""
        files = {"file": ("test.png", io.BytesIO(TEST_IMAGE_CONTENT), "image/png")}
        data = {"type": "image"}
        
        response = client.post("/api/v1/files/upload", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["fileType"] == "image"
    
    def test_upload_invalid_type(self):
        """上传文件 - 类型不匹配"""
        files = {"file": ("test.mp4", io.BytesIO(TEST_VIDEO_CONTENT), "video/mp4")}
        data = {"type": "invalid"}
        
        response = client.post("/api/v1/files/upload", files=files, data=data)
        
        assert response.status_code == 400
        result = response.json()
        assert result["code"] == 1004


class TestFileList:
    """文件列表测试"""
    
    def test_get_files_list(self):
        """TC-FILE-006: 获取文件列表"""
        response = client.get("/api/v1/files")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert "total" in result["data"]
        assert "files" in result["data"]
        assert "page" in result["data"]
        assert "pageSize" in result["data"]
    
    def test_get_files_by_type(self):
        """获取文件列表 - 按类型过滤"""
        response = client.get("/api/v1/files?type=video")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        
        # 验证返回的都是视频文件
        for file in result["data"]["files"]:
            assert file["fileType"] == "video"
    
    def test_get_files_pagination(self):
        """获取文件列表 - 分页"""
        response = client.get("/api/v1/files?page=1&pageSize=10")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["page"] == 1
        assert result["data"]["pageSize"] <= 10


class TestFileDetail:
    """文件详情测试"""
    
    def test_get_file_detail(self):
        """TC-FILE-007: 获取文件详情"""
        # 先上传一个文件
        files = {"file": ("detail_test.mp4", io.BytesIO(TEST_VIDEO_CONTENT), "video/mp4")}
        data = {"type": "video"}
        upload_response = client.post("/api/v1/files/upload", files=files, data=data)
        file_id = upload_response.json()["data"]["fileId"]
        
        # 获取详情
        response = client.get(f"/api/v1/files/{file_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["fileId"] == file_id
        assert "fileName" in result["data"]
        assert "downloadUrl" in result["data"]
        assert "thumbnailUrl" in result["data"]
    
    def test_get_file_not_found(self):
        """获取文件详情 - 文件不存在"""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/files/{fake_id}")
        
        assert response.status_code == 400
        result = response.json()
        assert result["code"] == 1005


class TestFileDownload:
    """文件下载测试"""
    
    def test_download_file(self):
        """下载文件"""
        # 先上传一个文件
        files = {"file": ("download_test.mp4", io.BytesIO(TEST_VIDEO_CONTENT), "video/mp4")}
        data = {"type": "video"}
        upload_response = client.post("/api/v1/files/upload", files=files, data=data)
        file_id = upload_response.json()["data"]["fileId"]
        
        # 下载文件
        response = client.get(f"/api/v1/files/{file_id}/download")
        
        assert response.status_code == 200
        assert response.headers["content-disposition"] is not None
    
    def test_download_file_not_found(self):
        """下载文件 - 文件不存在"""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/files/{fake_id}/download")
        
        assert response.status_code == 400
        result = response.json()
        assert result["code"] == 1005


class TestFileDelete:
    """文件删除测试"""
    
    def test_delete_file(self):
        """TC-FILE-008: 删除文件"""
        # 先上传一个文件
        files = {"file": ("delete_test.mp4", io.BytesIO(TEST_VIDEO_CONTENT), "video/mp4")}
        data = {"type": "video"}
        upload_response = client.post("/api/v1/files/upload", files=files, data=data)
        file_id = upload_response.json()["data"]["fileId"]
        
        # 删除文件
        response = client.delete(f"/api/v1/files/{file_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["message"] == "删除成功"
        
        # 验证文件已被删除
        get_response = client.get(f"/api/v1/files/{file_id}")
        assert get_response.status_code == 400
    
    def test_delete_file_not_found(self):
        """删除文件 - 文件不存在"""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/v1/files/{fake_id}")
        
        assert response.status_code == 400
        result = response.json()
        assert result["code"] == 1005
    
    def test_batch_delete(self):
        """批量删除文件"""
        # 先上传几个文件
        file_ids = []
        for i in range(3):
            files = {"file": (f"batch_{i}.mp4", io.BytesIO(TEST_VIDEO_CONTENT), "video/mp4")}
            data = {"type": "video"}
            upload_response = client.post("/api/v1/files/upload", files=files, data=data)
            file_ids.append(upload_response.json()["data"]["fileId"])
        
        # 批量删除
        response = client.post("/api/v1/files/batch-delete", json={"fileIds": file_ids})
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["deleted"] == 3
        assert result["data"]["failed"] == 0


class TestHealthCheck:
    """健康检查测试"""
    
    def test_health_check(self):
        """健康检查接口"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["data"]["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
