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
from src.services.task_service import TaskService, TaskStatus
from src.services.audio_service import AudioService

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

# 初始化服务
file_service = FileService()
task_service = TaskService()
audio_service = AudioService(file_service=file_service)

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

# ==================== 任务管理数据模型 ====================

class TaskResponse(BaseModel):
    taskId: str
    type: str
    status: str
    progress: int
    message: Optional[str] = None
    createdAt: str
    updatedAt: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class BatchQueryRequest(BaseModel):
    taskIds: List[str]

class BatchQueryResponse(BaseModel):
    tasks: List[Dict[str, Any]]

# ==================== 音频处理数据模型 ====================

class VoiceoverRequest(BaseModel):
    text: str = Field(..., max_length=10000, description="配音文本")
    voice: Optional[str] = Field(None, description="音色")
    speed: Optional[float] = Field(1.0, ge=0.5, le=2.0, description="语速")
    volume: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="音量")
    outputName: Optional[str] = Field(None, description="输出文件名")

class VoiceoverResponse(BaseModel):
    audioId: str
    duration: Optional[float] = None
    downloadUrl: str

class ASRRequest(BaseModel):
    audioId: str
    language: Optional[str] = Field("zh-CN", description="语言")
    outputFormat: Optional[str] = Field("srt", description="输出格式")

class ASRResponse(BaseModel):
    taskId: str
    status: str

# ==================== 错误码 ====================

ERROR_CODES = {
    # 文件管理 (1000-1999)
    1001: "文件格式不支持",
    1002: "文件大小超限",
    1003: "文件损坏",
    1004: "文件类型不匹配",
    1005: "文件不存在",
    # 音频处理 (2000-2999)
    2010: "文本过长",
    2011: "音色不支持",
    2012: "配音生成失败",
    2020: "ASR 识别失败",
    2021: "音频格式不支持",
    # 任务管理 (3000-3999)
    3001: "任务不存在",
    3002: "任务已完成，无法取消",
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

# ==================== 任务管理接口 ====================

@app.get("/api/v1/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task(task_id: str = Path(..., description="任务 ID")):
    """
    查询任务进度
    
    - **task_id**: 任务 ID
    """
    try:
        task = await task_service.get_task(task_id)
        
        if not task:
            return error_response(3001, "任务不存在", path=f"/api/v1/tasks/{task_id}")
        
        # 添加下载 URL
        if "result" in task and task["result"] and "outputId" in task["result"]:
            task["result"]["downloadUrl"] = f"/api/v1/files/{task['result']['outputId']}/download"
        
        return {
            "code": 200,
            "data": task
        }
        
    except Exception as e:
        return error_response(5003, "查询任务失败", str(e), f"/api/v1/tasks/{task_id}")

@app.delete("/api/v1/tasks/{task_id}", response_model=Dict[str, Any])
async def cancel_task(task_id: str = Path(..., description="任务 ID")):
    """
    取消任务
    
    - **task_id**: 任务 ID
    """
    try:
        result = await task_service.cancel_task(task_id)
        
        if not result["success"]:
            if result.get("code") == 3001:
                return error_response(3001, "任务不存在", path=f"/api/v1/tasks/{task_id}")
            elif result.get("code") == 3002:
                return error_response(3002, "任务已完成，无法取消", path=f"/api/v1/tasks/{task_id}")
        
        return {
            "code": 200,
            "message": "任务已取消"
        }
        
    except Exception as e:
        return error_response(5003, "取消任务失败", str(e), f"/api/v1/tasks/{task_id}")

@app.post("/api/v1/tasks/batch-query", response_model=Dict[str, Any])
async def batch_query_tasks(request: BatchQueryRequest):
    """
    批量查询任务
    
    - **taskIds**: 任务 ID 列表
    """
    try:
        tasks = await task_service.batch_get_tasks(request.taskIds)
        
        # 简化返回格式
        simplified_tasks = []
        for task in tasks:
            simplified_tasks.append({
                "taskId": task["taskId"],
                "status": task["status"],
                "progress": task["progress"],
                "message": task.get("message"),
                "type": task["type"]
            })
        
        return {
            "code": 200,
            "data": {
                "tasks": simplified_tasks
            }
        }
        
    except Exception as e:
        return error_response(5003, "批量查询失败", str(e), "/api/v1/tasks/batch-query")

# ==================== 音频处理接口 ====================

@app.post("/api/v1/audio/voiceover", response_model=Dict[str, Any])
async def generate_voiceover(request: VoiceoverRequest):
    """
    AI 配音生成（Edge TTS）
    
    - **text**: 配音文本，最大 10000 字
    - **voice**: 音色，默认 zh-CN-XiaoxiaoNeural
    - **speed**: 语速，0.5-2.0，默认 1.0
    - **volume**: 音量，0.0-1.0，默认 1.0
    """
    try:
        # 验证文本长度
        if len(request.text) > 10000:
            return error_response(2010, "文本过长，最大支持 10000 字", path="/api/v1/audio/voiceover")
        
        # 生成配音
        result = await audio_service.generate_voiceover(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            volume=request.volume,
            output_name=request.outputName
        )
        
        # 保存文件元数据到文件服务
        if file_service:
            file_id = result["audioId"]
            with open(result["filePath"], 'rb') as f:
                content = f.read()
            await file_service.save_file(file_id, content, result["fileName"], "audio")
        
        return {
            "code": 200,
            "data": {
                "audioId": result["audioId"],
                "duration": result["duration"],
                "downloadUrl": f"/api/v1/files/{result['audioId']}/download"
            },
            "message": "配音生成成功"
        }
        
    except ValueError as e:
        error_msg = str(e)
        if "音色" in error_msg:
            return error_response(2011, error_msg, path="/api/v1/audio/voiceover")
        elif "文本" in error_msg:
            return error_response(2010, error_msg, path="/api/v1/audio/voiceover")
        return error_response(400, error_msg, path="/api/v1/audio/voiceover")
        
    except RuntimeError as e:
        return error_response(2012, str(e), path="/api/v1/audio/voiceover")
        
    except Exception as e:
        return error_response(5003, "配音生成失败", str(e), path="/api/v1/audio/voiceover")

@app.post("/api/v1/audio/asr", response_model=Dict[str, Any])
async def generate_asr(request: ASRRequest):
    """
    ASR 字幕生成（阿里云）
    
    - **audioId**: 音频文件 ID
    - **language**: 语言，默认 zh-CN
    - **outputFormat**: 输出格式，默认 srt
    """
    try:
        # 获取音频文件路径
        file_path = await file_service.get_file_path(request.audioId)
        if not file_path or not os.path.exists(file_path):
            return error_response(1005, "音频文件不存在", path="/api/v1/audio/asr")
        
        # 验证音频文件格式
        allowed_extensions = [".mp3", ".wav", ".aac", ".m4a", ".flac"]
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in allowed_extensions:
            return error_response(2021, f"音频格式不支持，仅支持 {', '.join(allowed_extensions).upper()}", 
                                 path="/api/v1/audio/asr")
        
        # 创建 ASR 任务
        task_id = str(uuid.uuid4())
        await task_service.create_task(
            task_id=task_id,
            task_type="audio/asr",
            input_data={
                "audioId": request.audioId,
                "language": request.language,
                "outputFormat": request.outputFormat
            }
        )
        
        # 异步处理 ASR
        async def process_asr():
            try:
                await task_service.update_task(
                    task_id, 
                    status=TaskStatus.PROCESSING, 
                    progress=10,
                    message="正在识别音频..."
                )
                
                result = await audio_service.generate_asr(
                    audio_id=request.audioId,
                    audio_path=file_path,
                    language=request.language,
                    output_format=request.outputFormat
                )
                
                # 保存字幕文件到文件服务
                subtitle_id = str(uuid.uuid4())
                with open(result["filePath"], 'r', encoding='utf-8') as f:
                    content = f.read().encode('utf-8')
                await file_service.save_file(subtitle_id, content, result["fileName"], "audio")
                
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="ASR 识别完成",
                    result_data={
                        "subtitleId": subtitle_id,
                        "outputId": subtitle_id
                    }
                )
                
            except Exception as e:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error_code=2020,
                    error_message=str(e)
                )
        
        # 启动后台任务
        asyncio.create_task(process_asr())
        
        return {
            "code": 202,
            "data": {
                "taskId": task_id,
                "status": "pending"
            },
            "message": "ASR 任务已提交"
        }
        
    except Exception as e:
        return error_response(5003, "ASR 任务提交失败", str(e), path="/api/v1/audio/asr")

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
