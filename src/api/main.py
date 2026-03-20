"""
Video Generator API - FastAPI Application
版本：v2.0
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import os
import shutil
from datetime import datetime, timezone
import json
import sys
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# 导入文件管理服务
from src.services.file_service import FileService

app = FastAPI(
    title="Video Generator API",
    version="2.0",
    description="视频生成处理 API 服务"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化文件服务
file_service = FileService()

# ==================== 数据模型 ====================

class FileUploadResponse(BaseModel):
    fileId: str
    fileName: str
    fileSize: int
    fileType: str
    duration: Optional[float] = None
    format: Optional[str] = None
    resolution: Optional[str] = None
    uploadTime: str
    downloadUrl: str

class FileInfo(BaseModel):
    fileId: str
    fileName: str
    fileSize: int
    fileType: str
    duration: Optional[float] = None
    uploadTime: str

class FileListResponse(BaseModel):
    total: int
    page: int
    pageSize: int
    files: List[FileInfo]

class FileDetailResponse(BaseModel):
    fileId: str
    fileName: str
    fileSize: int
    fileType: str
    duration: Optional[float] = None
    format: Optional[str] = None
    resolution: Optional[str] = None
    uploadTime: str
    downloadUrl: str
    thumbnailUrl: str

class BatchDeleteRequest(BaseModel):
    fileIds: List[str]

class BatchDeleteResponse(BaseModel):
    deleted: int
    failed: int

class ErrorResponse(BaseModel):
    code: int
    message: str
    details: Optional[str] = None
    timestamp: str
    path: str

# ==================== 错误码 ====================

ERROR_CODES = {
    1001: "文件格式不支持",
    1002: "文件大小超限",
    1003: "文件损坏",
    1004: "文件类型不匹配",
    1005: "文件不存在",
}

def error_response(code: int, message: str = None, details: str = None, path: str = None):
    """生成统一错误响应"""
    return JSONResponse(
        status_code=400 if code < 5000 else 500,
        content={
            "code": code,
            "message": message or ERROR_CODES.get(code, "未知错误"),
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "path": path
        }
    )

# ==================== 文件管理接口 ====================

@app.post("/api/v1/files/upload", response_model=Dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    type: str = Form(...)
):
    """
    上传文件
    
    - **file**: 文件内容
    - **type**: 文件类型 (video/audio/image)
    """
    try:
        # 验证文件类型
        if type not in ["video", "audio", "image"]:
            return error_response(1004, "文件类型不匹配", "仅支持 video/audio/image")
        
        # 验证文件大小 (2GB 限制)
        file_content = await file.read()
        file_size = len(file_content)
        if file_size > 2 * 1024 * 1024 * 1024:
            return error_response(1002, "文件大小超限，最大支持 2GB")
        
        # 验证文件格式
        allowed_extensions = {
            "video": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
            "audio": [".mp3", ".wav", ".aac", ".m4a", ".flac"],
            "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
        }
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions.get(type, []):
            return error_response(1001, f"文件格式不支持，仅支持 {', '.join(allowed_extensions.get(type, [])).upper()} 格式")
        
        # 保存文件
        file_id = str(uuid.uuid4())
        saved_path = await file_service.save_file(file_id, file_content, file.filename, type)
        
        # 获取文件元数据
        metadata = await file_service.get_file_metadata(saved_path, type)
        
        upload_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        return {
            "code": 200,
            "data": {
                "fileId": file_id,
                "fileName": file.filename,
                "fileSize": file_size,
                "fileType": type,
                "duration": metadata.get("duration"),
                "format": metadata.get("format"),
                "resolution": metadata.get("resolution"),
                "uploadTime": upload_time,
                "downloadUrl": f"/api/v1/files/{file_id}/download"
            },
            "message": "上传成功"
        }
        
    except Exception as e:
        return error_response(5003, "上传失败", str(e), "/api/v1/files/upload")

@app.get("/api/v1/files", response_model=Dict[str, Any])
async def get_files(
    type: Optional[str] = Query(None, description="文件类型：video/audio/image"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    sortBy: str = Query("uploadTime", description="排序字段：uploadTime/fileName"),
    order: str = Query("desc", description="排序顺序：asc/desc")
):
    """
    获取文件列表
    
    - **type**: 文件类型过滤
    - **page**: 页码
    - **pageSize**: 每页数量
    - **sortBy**: 排序字段
    - **order**: 排序顺序
    """
    try:
        files = await file_service.list_files(type=type, page=page, page_size=pageSize, sort_by=sortBy, order=order)
        total = await file_service.count_files(type=type)
        
        return {
            "code": 200,
            "data": {
                "total": total,
                "page": page,
                "pageSize": pageSize,
                "files": files
            },
            "message": "success"
        }
        
    except Exception as e:
        return error_response(5003, "获取文件列表失败", str(e), "/api/v1/files")

@app.get("/api/v1/files/{file_id}", response_model=Dict[str, Any])
async def get_file(file_id: str = Path(..., description="文件 ID")):
    """
    获取文件详情
    
    - **file_id**: 文件 ID
    """
    try:
        file_info = await file_service.get_file(file_id)
        if not file_info:
            return error_response(1005, "文件不存在", path=f"/api/v1/files/{file_id}")
        
        return {
            "code": 200,
            "data": {
                **file_info,
                "downloadUrl": f"/api/v1/files/{file_id}/download",
                "thumbnailUrl": f"/api/v1/files/{file_id}/thumbnail"
            }
        }
        
    except Exception as e:
        return error_response(5003, "获取文件详情失败", str(e), f"/api/v1/files/{file_id}")

@app.get("/api/v1/files/{file_id}/download")
async def download_file(file_id: str = Path(..., description="文件 ID")):
    """
    下载文件
    
    - **file_id**: 文件 ID
    """
    try:
        file_path = await file_service.get_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            return error_response(1005, "文件不存在", path=f"/api/v1/files/{file_id}/download")
        
        file_info = await file_service.get_file(file_id)
        
        return FileResponse(
            path=file_path,
            filename=file_info["fileName"],
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        return error_response(5003, "下载失败", str(e), f"/api/v1/files/{file_id}/download")

@app.delete("/api/v1/files/{file_id}", response_model=Dict[str, Any])
async def delete_file(file_id: str = Path(..., description="文件 ID")):
    """
    删除文件
    
    - **file_id**: 文件 ID
    """
    try:
        file_path = await file_service.get_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            return error_response(1005, "文件不存在", path=f"/api/v1/files/{file_id}")
        
        await file_service.delete_file(file_id)
        
        return {
            "code": 200,
            "message": "删除成功"
        }
        
    except Exception as e:
        return error_response(5003, "删除失败", str(e), f"/api/v1/files/{file_id}")

@app.post("/api/v1/files/batch-delete", response_model=Dict[str, Any])
async def batch_delete_files(request: BatchDeleteRequest):
    """
    批量删除文件
    
    - **fileIds**: 文件 ID 列表
    """
    try:
        deleted = 0
        failed = 0
        
        for file_id in request.fileIds:
            try:
                await file_service.delete_file(file_id)
                deleted += 1
            except:
                failed += 1
        
        return {
            "code": 200,
            "data": {
                "deleted": deleted,
                "failed": failed
            },
            "message": "批量删除完成"
        }
        
    except Exception as e:
        return error_response(5003, "批量删除失败", str(e), "/api/v1/files/batch-delete")

# ==================== 健康检查 ====================

@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {
        "code": 200,
        "data": {
            "status": "healthy",
            "version": "v2.0",
            "uptime": 0,
            "checks": {
                "database": "ok",
                "storage": "ok",
                "redis": "ok"
            }
        }
    }

# ==================== 启动服务器 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=15321)
