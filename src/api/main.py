"""
Video Generator API - FastAPI Application
版本：v2.0
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
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
from src.services.video_service import VideoService
from src.services.batch_service import BatchService
from src.services.script_service import ScriptService
from src.services.storyboard_service import StoryboardService
from src.services.ai_video_service import AIVideoService
from src.services.quota_service import QuotaService
from src.services.dashboard_service import DashboardService
from src.services.template_service import TemplateService
from src.services.system_service import SystemService
from src.services.material_service import MaterialService
from src.services.effect_service import EffectService

# 速率限制器初始化
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Video Generator API",
    version="2.0",
    description="视频生成处理 API 服务"
)

# 注册速率限制中间件
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 配置 - 限制为特定域名
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
file_service = FileService()
task_service = TaskService()
audio_service = AudioService(file_service=file_service)
video_service = VideoService(file_service=file_service, task_service=task_service)
batch_service = BatchService()
script_service = ScriptService()
storyboard_service = StoryboardService(file_service=file_service)
ai_video_service = AIVideoService()
quota_service = QuotaService()
dashboard_service = DashboardService()
template_service = TemplateService(file_service=file_service)
system_service = SystemService()
material_service = MaterialService(file_service=file_service)
effect_service = EffectService()

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

class ASRStatusResponse(BaseModel):
    taskId: str
    status: str
    progress: int
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

# ==================== 视频处理数据模型 ====================

class VideoConcatRequest(BaseModel):
    videos: List[str] = Field(..., min_length=2, description="视频 fileId 列表")
    outputName: Optional[str] = Field(None, description="输出文件名")
    transition: Optional[str] = Field("none", description="转场效果：none/fade/dissolve")

class TextOverlayRequest(BaseModel):
    videoId: str
    text: str
    position: Dict[str, int] = Field(default_factory=lambda: {"x": 100, "y": 200})
    style: Optional[Dict[str, Any]] = Field(default_factory=dict)
    duration: Optional[Dict[str, float]] = Field(default_factory=lambda: {"start": 0, "end": -1})
    outputName: Optional[str] = Field(None, description="输出文件名")

class ImageOverlayRequest(BaseModel):
    videoId: str
    imageId: str
    position: Dict[str, int] = Field(default_factory=lambda: {"x": 50, "y": 50})
    opacity: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    duration: Optional[Dict[str, float]] = Field(default_factory=dict)
    outputName: Optional[str] = Field(None, description="输出文件名")

class AddMusicRequest(BaseModel):
    videoId: str
    musicId: str
    startTime: Optional[float] = Field(0, ge=0)
    endTime: Optional[float] = Field(-1)
    volume: Optional[float] = Field(0.3, ge=0.0, le=1.0)
    fade: Optional[Dict[str, float]] = Field(default_factory=dict)
    loop: Optional[bool] = Field(True)
    outputName: Optional[str] = Field(None, description="输出文件名")

class AddVoiceoverRequest(BaseModel):
    videoId: str
    voiceoverId: str
    alignMode: Optional[str] = Field("start", description="start/center/end/custom")
    startTime: Optional[float] = Field(0, ge=0)
    volume: Optional[float] = Field(0.8, ge=0.0, le=1.0)
    outputName: Optional[str] = Field(None, description="输出文件名")

class AddSubtitlesRequest(BaseModel):
    videoId: str
    subtitleId: str
    offset: Optional[float] = Field(0, description="时间偏移（秒）")
    style: Optional[Dict[str, Any]] = Field(default_factory=dict)
    outputName: Optional[str] = Field(None, description="输出文件名")

class TransitionRequest(BaseModel):
    videos: List[str] = Field(..., min_length=2, description="视频 fileId 列表")
    transition: str = Field(..., description="转场类型：fade/dissolve/wipe/slide")
    duration: Optional[float] = Field(1.0, ge=0.1)
    outputName: Optional[str] = Field(None, description="输出文件名")

class ProcessStep(BaseModel):
    type: str = Field(..., description="步骤类型：add_music/add_voiceover/add_subtitles/text_overlay/image_overlay")
    params: Dict[str, Any] = Field(default_factory=dict)

class ProcessPipelineRequest(BaseModel):
    videoId: str
    steps: List[ProcessStep] = Field(..., min_length=1, description="处理步骤列表")
    outputName: Optional[str] = Field(None, description="输出文件名")

# ==================== 批量生成数据模型 ====================

class EpisodeRange(BaseModel):
    start: int = Field(..., ge=1, description="起始集数")
    end: int = Field(..., ge=1, description="结束集数")

class BatchGenerateRequest(BaseModel):
    scriptId: str = Field(..., description="剧本 ID")
    episodeRange: EpisodeRange = Field(..., description="集数范围")
    parallelism: Optional[int] = Field(4, ge=1, le=10, description="并行度，默认 4")

class BatchEpisodeProgress(BaseModel):
    episode: int
    totalShots: int
    completedShots: int
    failedShots: int
    status: str
    error: Optional[str] = None

class BatchStatusResponse(BaseModel):
    batchId: str
    scriptId: str
    status: str
    totalEpisodes: int
    totalShots: int
    completedEpisodes: int
    completedShots: int
    failedEpisodes: int
    progress: int
    parallelism: int
    episodeRange: Dict[str, int]
    episodeProgress: Optional[List[Dict[str, Any]]] = None
    createdAt: str
    updatedAt: Optional[str] = None
    completedAt: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

# ==================== 分镜设计数据模型 ====================

class StoryboardGenerateRequest(BaseModel):
    scriptId: str = Field(..., description="剧本 ID")
    title: Optional[str] = Field(None, description="剧本标题（可选，不填则从剧本读取）")

class StoryboardResponse(BaseModel):
    storyboardId: str
    scriptId: str
    title: str
    createdAt: str
    scenes: List[Dict[str, Any]]

class StoryboardListResponse(BaseModel):
    total: int
    page: int
    pageSize: int
    storyboards: List[Dict[str, Any]]

# ==================== AI 视频生成数据模型 ====================

class AIVideoGenerateRequest(BaseModel):
    prompt: str = Field(..., max_length=5000, description="视频描述提示词")
    duration: Optional[int] = Field(5, ge=5, le=30, description="视频时长 (秒)，支持 5/10/15/30")
    resolution: Optional[str] = Field("1080p", description="分辨率，支持 720p/1080p/4k")

class AIVideoGenerateResponse(BaseModel):
    taskId: str
    status: str
    estimatedTime: int

class AIVideoStatusResponse(BaseModel):
    taskId: str
    status: str
    progress: int
    message: Optional[str] = None
    videoUrl: Optional[str] = None
    videoId: Optional[str] = None

class AIVideoDownloadResponse(BaseModel):
    videoId: str
    fileName: str
    fileSize: int
    downloadUrl: str

# ==================== 模板管理数据模型 ====================

class TemplateStep(BaseModel):
    stepType: str = Field(..., description="步骤类型：script/storyboard/audio/video/etc")
    config: Dict[str, Any] = Field(default_factory=dict, description="步骤配置参数")
    order: int = Field(0, description="步骤顺序")

class TemplateCreateRequest(BaseModel):
    name: str = Field(..., max_length=100, description="模板名称")
    description: str = Field("", max_length=500, description="模板描述")
    steps: List[TemplateStep] = Field(..., min_length=1, description="模板步骤列表")
    isPublic: bool = Field(False, description="是否公开")

class TemplateInfo(BaseModel):
    templateId: str
    name: str
    description: str
    isPublic: bool
    createdAt: str
    updatedAt: str
    version: str
    stepCount: int

class TemplateListResponse(BaseModel):
    total: int
    page: int
    pageSize: int
    totalPages: int
    templates: List[TemplateInfo]

class TemplateDetailResponse(BaseModel):
    templateId: str
    name: str
    description: str
    steps: List[TemplateStep]
    isPublic: bool
    createdAt: str
    updatedAt: str
    version: str

class TemplateApplyRequest(BaseModel):
    videoId: Optional[str] = Field(None, description="视频 ID（可选）")

class TemplateApplyResponse(BaseModel):
    applyId: str
    templateId: str
    templateName: str
    videoId: Optional[str]
    appliedAt: str
    steps: List[TemplateStep]
    status: str
    currentStep: int

# ==================== 错误码 ====================

ERROR_CODES = {
    # 文件管理 (1000-1999)
    1001: "文件格式不支持",
    1002: "文件大小超限",
    1003: "文件损坏",
    1004: "文件类型不匹配",
    1005: "文件不存在",
    # 视频处理 (2000-2999)
    2001: "视频数量不足",
    2002: "视频格式不一致",
    2003: "时间范围超出视频长度",
    # 音频处理 (2000-2999)
    2010: "文本过长",
    2011: "音色不支持",
    2012: "配音生成失败",
    2020: "ASR 识别失败",
    2021: "音频格式不支持",
    # 任务管理 (3000-3999)
    3001: "任务不存在",
    3002: "任务已完成，无法取消",
    # AI 视频生成 (4000-4999)
    4001: "提示词不能为空",
    4002: "不支持的时长",
    4003: "不支持的分辨率",
    4004: "视频生成失败",
    4005: "视频尚未完成",
    5001: "Sora API 调用失败",
    5002: "Sora API 超时",
    5003: "视频下载失败",
    5004: "服务内部错误",
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
@limiter.limit("10/minute")  # 文件上传：每分钟 10 次
async def upload_file(
    request: Request,
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

@app.get("/api/v1/tasks", response_model=Dict[str, Any])
async def get_tasks(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    orderBy: str = Query("createdAt", description="排序字段"),
    order: str = Query("desc", description="排序顺序")
):
    """
    获取任务列表

    - **limit**: 返回数量限制，默认 20
    - **orderBy**: 排序字段，默认 createdAt
    - **order**: 排序顺序，默认 desc
    """
    try:
        # 调用 task_service 的 list_tasks 方法
        tasks_list = await task_service.list_tasks(limit=limit)

        # 添加下载 URL
        for task in tasks_list:
            if "result" in task and task["result"] and "outputId" in task["result"]:
                task["result"]["downloadUrl"] = f"/api/v1/files/{task['result']['outputId']}/download"

        return {
            "code": 200,
            "data": tasks_list,
            "message": "获取成功"
        }

    except Exception as e:
        return error_response(5003, "获取任务列表失败", str(e), "/api/v1/tasks")


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
@limiter.limit("20/minute")  # 语音生成：每分钟 20 次
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

@app.get("/api/v1/asr/{task_id}", response_model=Dict[str, Any])
async def get_asr_status(task_id: str = Path(..., description="ASR 任务 ID")):
    """
    查询 ASR 识别进度
    
    - **task_id**: ASR 任务 ID
    """
    try:
        # 查询任务状态
        task = await task_service.get_task(task_id)
        
        if not task:
            return error_response(3001, "ASR 任务不存在", path=f"/api/v1/asr/{task_id}")
        
        # 构建响应
        response_data = {
            "taskId": task["taskId"],
            "status": task["status"],
            "progress": task["progress"],
            "message": task.get("message")
        }
        
        # 如果任务完成，添加结果信息
        if task["status"] == TaskStatus.COMPLETED.value and "result" in task:
            result = task["result"]
            response_data["result"] = {
                "subtitleId": result.get("subtitleId"),
                "outputId": result.get("outputId"),
                "downloadUrl": f"/api/v1/files/{result.get('outputId')}/download"
            }
        
        # 如果任务失败，添加错误信息
        if task["status"] == TaskStatus.FAILED.value and "error" in task:
            response_data["error"] = task["error"]
        
        return {
            "code": 200,
            "data": response_data
        }
        
    except Exception as e:
        return error_response(5003, "查询 ASR 进度失败", str(e), path=f"/api/v1/asr/{task_id}")

# ==================== 视频处理接口 ====================

@app.post("/api/v1/video/concat", response_model=Dict[str, Any])
async def video_concat(request: VideoConcatRequest):
    """
    视频拼接
    
    - **videos**: 视频 fileId 列表，至少 2 个
    - **outputName**: 输出文件名
    - **transition**: 转场效果：none/fade/dissolve，默认 none
    """
    try:
        # 验证视频数量
        if len(request.videos) < 2:
            return error_response(2001, "至少需要 2 个视频进行拼接", path="/api/v1/video/concat")
        
        # 创建任务
        task_id = str(uuid.uuid4())
        await task_service.create_task(
            task_id=task_id,
            task_type="video/concat",
            input_data={
                "videos": request.videos,
                "transition": request.transition
            }
        )
        
        # 异步处理
        async def process_concat():
            try:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=10,
                    message="正在加载视频..."
                )
                
                result = await video_service.concat_videos(
                    video_ids=request.videos,
                    output_name=request.outputName,
                    transition=request.transition
                )
                
                # 保存输出文件到文件服务
                with open(result["filePath"], 'rb') as f:
                    content = f.read()
                await file_service.save_file(
                    result["outputId"],
                    content,
                    result["fileName"],
                    "video"
                )
                
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="视频拼接完成",
                    result_data={"outputId": result["outputId"]}
                )
                
            except Exception as e:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error_code=5003,
                    error_message=str(e)
                )
        
        asyncio.create_task(process_concat())
        
        return {
            "code": 202,
            "data": {
                "taskId": task_id,
                "status": "pending",
                "estimatedTime": 60
            },
            "message": "任务已提交"
        }
        
    except ValueError as e:
        return error_response(400, str(e), path="/api/v1/video/concat")
    except Exception as e:
        return error_response(5003, str(e), path="/api/v1/video/concat")


@app.post("/api/v1/video/text-overlay", response_model=Dict[str, Any])
async def video_text_overlay(request: TextOverlayRequest):
    """
    添加文字特效
    
    - **videoId**: 视频文件 ID
    - **text**: 文字内容
    - **position**: 位置 {"x": 100, "y": 200}
    - **style**: 样式 {"fontSize": 24, "fontFamily": "Arial", "color": "#FFFFFF", ...}
    - **duration**: 时长 {"start": 0, "end": 5}
    """
    try:
        # 创建任务
        task_id = str(uuid.uuid4())
        await task_service.create_task(
            task_id=task_id,
            task_type="video/text-overlay",
            input_data=request.dict()
        )
        
        # 异步处理
        async def process_text_overlay():
            try:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=10,
                    message="正在添加文字特效..."
                )
                
                result = await video_service.add_text_overlay(
                    video_id=request.videoId,
                    text=request.text,
                    position=request.position,
                    style=request.style,
                    duration=request.duration,
                    output_name=request.outputName
                )
                
                # 保存输出文件
                with open(result["filePath"], 'rb') as f:
                    content = f.read()
                await file_service.save_file(
                    result["outputId"],
                    content,
                    result["fileName"],
                    "video"
                )
                
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="文字特效添加完成",
                    result_data={"outputId": result["outputId"]}
                )
                
            except Exception as e:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error_code=5003,
                    error_message=str(e)
                )
        
        asyncio.create_task(process_text_overlay())
        
        return {
            "code": 202,
            "data": {
                "taskId": task_id,
                "status": "pending"
            },
            "message": "任务已提交"
        }
        
    except ValueError as e:
        if "时间范围超出" in str(e):
            return error_response(2003, str(e), path="/api/v1/video/text-overlay")
        return error_response(400, str(e), path="/api/v1/video/text-overlay")
    except Exception as e:
        return error_response(5003, str(e), path="/api/v1/video/text-overlay")


@app.post("/api/v1/video/image-overlay", response_model=Dict[str, Any])
async def video_image_overlay(request: ImageOverlayRequest):
    """
    添加图片/动图水印
    
    - **videoId**: 视频文件 ID
    - **imageId**: 图片文件 ID
    - **position**: 位置 {"x": 50, "y": 50}
    - **opacity**: 透明度 (0.0-1.0)
    - **duration**: 时长 {"start": 0, "end": -1}
    """
    try:
        # 创建任务
        task_id = str(uuid.uuid4())
        await task_service.create_task(
            task_id=task_id,
            task_type="video/image-overlay",
            input_data=request.dict()
        )
        
        # 异步处理
        async def process_image_overlay():
            try:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=10,
                    message="正在添加图片水印..."
                )
                
                result = await video_service.add_image_overlay(
                    video_id=request.videoId,
                    image_id=request.imageId,
                    position=request.position,
                    opacity=request.opacity,
                    duration=request.duration,
                    output_name=request.outputName
                )
                
                # 保存输出文件
                with open(result["filePath"], 'rb') as f:
                    content = f.read()
                await file_service.save_file(
                    result["outputId"],
                    content,
                    result["fileName"],
                    "video"
                )
                
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="图片水印添加完成",
                    result_data={"outputId": result["outputId"]}
                )
                
            except Exception as e:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error_code=5003,
                    error_message=str(e)
                )
        
        asyncio.create_task(process_image_overlay())
        
        return {
            "code": 202,
            "data": {
                "taskId": task_id,
                "status": "pending"
            },
            "message": "任务已提交"
        }
        
    except Exception as e:
        return error_response(5003, str(e), path="/api/v1/video/image-overlay")


@app.post("/api/v1/video/add-music", response_model=Dict[str, Any])
async def video_add_music(request: AddMusicRequest):
    """
    添加背景音乐
    
    - **videoId**: 视频文件 ID
    - **musicId**: 音频文件 ID
    - **startTime**: 从视频的第几秒开始播放
    - **endTime**: 结束时间 (-1 表示直到视频结束)
    - **volume**: 音量 (0.0-1.0)
    - **fade**: 淡入淡出 {"in": 2.0, "out": 2.0}
    - **loop**: 是否循环
    """
    try:
        # 创建任务
        task_id = str(uuid.uuid4())
        await task_service.create_task(
            task_id=task_id,
            task_type="video/add-music",
            input_data=request.dict()
        )
        
        # 异步处理
        async def process_add_music():
            try:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=10,
                    message="正在添加背景音乐..."
                )
                
                result = await video_service.add_background_music(
                    video_id=request.videoId,
                    music_id=request.musicId,
                    start_time=request.startTime,
                    end_time=request.endTime,
                    volume=request.volume,
                    fade=request.fade if request.fade else None,
                    loop=request.loop,
                    output_name=request.outputName
                )
                
                # 保存输出文件
                with open(result["filePath"], 'rb') as f:
                    content = f.read()
                await file_service.save_file(
                    result["outputId"],
                    content,
                    result["fileName"],
                    "video"
                )
                
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="背景音乐添加完成",
                    result_data={"outputId": result["outputId"]}
                )
                
            except Exception as e:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error_code=5003,
                    error_message=str(e)
                )
        
        asyncio.create_task(process_add_music())
        
        return {
            "code": 202,
            "data": {
                "taskId": task_id,
                "status": "pending"
            },
            "message": "任务已提交"
        }
        
    except Exception as e:
        return error_response(5003, str(e), path="/api/v1/video/add-music")


@app.post("/api/v1/video/add-voiceover", response_model=Dict[str, Any])
async def video_add_voiceover(request: AddVoiceoverRequest):
    """
    添加配音
    
    - **videoId**: 视频文件 ID
    - **voiceoverId**: 配音音频文件 ID
    - **alignMode**: 对齐模式 (start/center/end/custom)
    - **startTime**: 自定义开始时间
    - **volume**: 音量 (0.0-1.0)
    """
    try:
        # 创建任务
        task_id = str(uuid.uuid4())
        await task_service.create_task(
            task_id=task_id,
            task_type="video/add-voiceover",
            input_data=request.dict()
        )
        
        # 异步处理
        async def process_add_voiceover():
            try:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=10,
                    message="正在添加配音..."
                )
                
                result = await video_service.add_voiceover(
                    video_id=request.videoId,
                    voiceover_id=request.voiceoverId,
                    align_mode=request.alignMode,
                    start_time=request.startTime,
                    volume=request.volume,
                    output_name=request.outputName
                )
                
                # 保存输出文件
                with open(result["filePath"], 'rb') as f:
                    content = f.read()
                await file_service.save_file(
                    result["outputId"],
                    content,
                    result["fileName"],
                    "video"
                )
                
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="配音添加完成",
                    result_data={"outputId": result["outputId"]}
                )
                
            except Exception as e:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error_code=5003,
                    error_message=str(e)
                )
        
        asyncio.create_task(process_add_voiceover())
        
        return {
            "code": 202,
            "data": {
                "taskId": task_id,
                "status": "pending"
            },
            "message": "任务已提交"
        }
        
    except Exception as e:
        return error_response(5003, str(e), path="/api/v1/video/add-voiceover")


@app.post("/api/v1/video/transition", response_model=Dict[str, Any])
async def video_transition(request: TransitionRequest):
    """
    添加转场特效
    
    - **videos**: 视频 fileId 列表，至少 2 个
    - **transition**: 转场类型：fade/dissolve/wipe/slide
    - **duration**: 转场时长（秒）
    """
    try:
        # 验证视频数量
        if len(request.videos) < 2:
            return error_response(2001, "至少需要 2 个视频", path="/api/v1/video/transition")
        
        # 创建任务
        task_id = str(uuid.uuid4())
        await task_service.create_task(
            task_id=task_id,
            task_type="video/transition",
            input_data=request.dict()
        )
        
        # 异步处理
        async def process_transition():
            try:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=10,
                    message="正在添加转场特效..."
                )
                
                result = await video_service.add_transition(
                    video_ids=request.videos,
                    transition=request.transition,
                    duration=request.duration,
                    output_name=request.outputName
                )
                
                # 保存输出文件
                with open(result["filePath"], 'rb') as f:
                    content = f.read()
                await file_service.save_file(
                    result["outputId"],
                    content,
                    result["fileName"],
                    "video"
                )
                
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="转场特效添加完成",
                    result_data={"outputId": result["outputId"]}
                )
                
            except Exception as e:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error_code=5003,
                    error_message=str(e)
                )
        
        asyncio.create_task(process_transition())
        
        return {
            "code": 202,
            "data": {
                "taskId": task_id,
                "status": "pending"
            },
            "message": "任务已提交"
        }
        
    except ValueError as e:
        return error_response(400, str(e), path="/api/v1/video/transition")
    except Exception as e:
        return error_response(5003, str(e), path="/api/v1/video/transition")


@app.post("/api/v1/video/add-subtitles", response_model=Dict[str, Any])
async def video_add_subtitles(request: AddSubtitlesRequest):
    """
    添加字幕
    
    - **videoId**: 视频文件 ID
    - **subtitleId**: SRT 字幕文件 ID
    - **offset**: 时间偏移（秒）
    - **style**: 样式 {"fontSize": 20, "fontFamily": "思源黑体", "color": "#FFFFFF", ...}
    """
    try:
        # 创建任务
        task_id = str(uuid.uuid4())
        await task_service.create_task(
            task_id=task_id,
            task_type="video/add-subtitles",
            input_data=request.dict()
        )
        
        # 异步处理
        async def process_add_subtitles():
            try:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=10,
                    message="正在添加字幕..."
                )
                
                result = await video_service.add_subtitles(
                    video_id=request.videoId,
                    subtitle_id=request.subtitleId,
                    offset=request.offset,
                    style=request.style,
                    output_name=request.outputName
                )
                
                # 保存输出文件
                with open(result["filePath"], 'rb') as f:
                    content = f.read()
                await file_service.save_file(
                    result["outputId"],
                    content,
                    result["fileName"],
                    "video"
                )
                
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="字幕添加完成",
                    result_data={"outputId": result["outputId"]}
                )
                
            except Exception as e:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error_code=5003,
                    error_message=str(e)
                )
        
        asyncio.create_task(process_add_subtitles())
        
        return {
            "code": 202,
            "data": {
                "taskId": task_id,
                "status": "pending"
            },
            "message": "任务已提交"
        }
        
    except Exception as e:
        return error_response(5003, str(e), path="/api/v1/video/add-subtitles")


@app.post("/api/v1/video/process", response_model=Dict[str, Any])
async def video_process_pipeline(request: ProcessPipelineRequest):
    """
    一站式处理（流水线）
    
    - **videoId**: 视频文件 ID
    - **steps**: 处理步骤列表
    - **outputName**: 输出文件名
    
    支持的步骤类型:
    - add_music - 添加背景音乐
    - add_voiceover - 添加配音
    - add_subtitles - 添加字幕
    - text_overlay - 添加文字
    - image_overlay - 添加图片水印
    """
    try:
        # 验证步骤
        if not request.steps:
            return error_response(400, "处理步骤不能为空", path="/api/v1/video/process")
        
        # 创建任务
        task_id = str(uuid.uuid4())
        await task_service.create_task(
            task_id=task_id,
            task_type="video/process",
            input_data={
                "videoId": request.videoId,
                "steps": [s.dict() for s in request.steps],
                "outputName": request.outputName
            }
        )
        
        # 异步处理
        async def process_pipeline():
            try:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=10,
                    message="正在处理流水线...",
                    result_data={"totalSteps": len(request.steps), "currentStep": 0}
                )
                
                # 转换步骤为字典格式
                steps_dict = [s.dict() for s in request.steps]
                
                result = await video_service.process_pipeline(
                    video_id=request.videoId,
                    steps=steps_dict,
                    output_name=request.outputName
                )
                
                # 保存最终输出文件
                with open(result["filePath"], 'rb') as f:
                    content = f.read()
                await file_service.save_file(
                    result["outputId"],
                    content,
                    result["fileName"],
                    "video"
                )
                
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="一站式处理完成",
                    result_data={
                        "outputId": result["outputId"],
                        "totalSteps": result.get("totalSteps", len(request.steps)),
                        "stepResults": result.get("stepResults", [])
                    }
                )
                
            except Exception as e:
                await task_service.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error_code=5003,
                    error_message=str(e)
                )
        
        asyncio.create_task(process_pipeline())
        
        return {
            "code": 202,
            "data": {
                "taskId": task_id,
                "status": "pending",
                "totalSteps": len(request.steps),
                "currentStep": 0
            },
            "message": "任务已提交"
        }
        
    except ValueError as e:
        return error_response(400, str(e), path="/api/v1/video/process")
    except Exception as e:
        return error_response(5003, str(e), path="/api/v1/video/process")

# ==================== AI 剧本生成数据模型 ====================

class ScriptGenerateRequest(BaseModel):
    theme: str = Field(..., max_length=500, description="剧本主题/梗概")
    episodes: Optional[int] = Field(80, ge=1, le=200, description="集数")
    genre: Optional[str] = Field("言情", description="题材类型")

class ScriptGenerateResponse(BaseModel):
    scriptId: str
    title: str
    episodes: int
    genre: str
    createdAt: str

class ScriptExpandRequest(BaseModel):
    scriptId: str
    targetEpisodes: Optional[int] = Field(None, ge=1, le=200, description="目标集数")

class ScriptListResponse(BaseModel):
    total: int
    scripts: List[Dict[str, Any]]

# ==================== AI 剧本生成接口 ====================

@app.post("/api/v1/ai/script/generate", response_model=Dict[str, Any])
async def generate_script(request: ScriptGenerateRequest):
    """
    根据主题生成剧本
    
    - **theme**: 剧本主题/梗概
    - **episodes**: 集数，默认 80 集
    - **genre**: 题材类型（言情/悬疑/喜剧/动作/科幻/古装/都市/奇幻等）
    """
    try:
        # 生成剧本
        script_data = await script_service.generate_script(
            theme=request.theme,
            episodes=request.episodes,
            genre=request.genre
        )
        
        return {
            "code": 200,
            "data": {
                "scriptId": script_data["scriptId"],
                "title": script_data["title"],
                "episodes": script_data["episodes"],
                "genre": script_data["genre"],
                "createdAt": script_data["createdAt"],
                "sceneCount": len(script_data.get("scenes", []))
            },
            "message": "剧本生成成功"
        }
        
    except Exception as e:
        return error_response(5004, str(e), path="/api/v1/ai/script/generate")


@app.get("/api/v1/ai/script/{script_id}", response_model=Dict[str, Any])
async def get_script(script_id: str = Path(..., description="剧本 ID")):
    """
    获取剧本详情
    
    - **script_id**: 剧本 ID
    """
    try:
        script_data = script_service.get_script(script_id)
        
        if not script_data:
            return error_response(404, "剧本不存在", path=f"/api/v1/ai/script/{script_id}")
        
        return {
            "code": 200,
            "data": script_data,
            "message": "获取成功"
        }
        
    except Exception as e:
        return error_response(5004, str(e), path=f"/api/v1/ai/script/{script_id}")


@app.post("/api/v1/ai/script/expand", response_model=Dict[str, Any])
async def expand_script(request: ScriptExpandRequest):
    """
    扩展剧本为更多集
    
    - **scriptId**: 剧本 ID
    - **targetEpisodes**: 目标集数（可选，默认增加 20 集）
    """
    try:
        script_data = await script_service.expand_script(
            script_id=request.scriptId,
            target_episodes=request.targetEpisodes
        )
        
        return {
            "code": 200,
            "data": {
                "scriptId": script_data["scriptId"],
                "title": script_data["title"],
                "episodes": script_data["episodes"],
                "genre": script_data["genre"],
                "sceneCount": len(script_data.get("scenes", []))
            },
            "message": "剧本扩展成功"
        }
        
    except ValueError as e:
        return error_response(400, str(e), path="/api/v1/ai/script/expand")
    except Exception as e:
        return error_response(5004, str(e), path="/api/v1/ai/script/expand")


@app.get("/api/v1/ai/scripts", response_model=Dict[str, Any])
async def list_scripts(limit: int = Query(20, ge=1, le=100, description="返回数量限制")):
    """
    获取剧本列表
    
    - **limit**: 返回数量限制，默认 20
    """
    try:
        scripts = script_service.list_scripts(limit=limit)
        
        return {
            "code": 200,
            "data": {
                "total": len(scripts),
                "scripts": scripts
            },
            "message": "获取成功"
        }
        
    except Exception as e:
        return error_response(5004, str(e), path="/api/v1/ai/scripts")


@app.delete("/api/v1/ai/script/{script_id}", response_model=Dict[str, Any])
async def delete_script(script_id: str = Path(..., description="剧本 ID")):
    """
    删除剧本
    
    - **script_id**: 剧本 ID
    """
    try:
        success = script_service.delete_script(script_id)
        
        if not success:
            return error_response(404, "剧本不存在", path=f"/api/v1/ai/script/{script_id}")
        
        return {
            "code": 200,
            "data": None,
            "message": "删除成功"
        }
        
    except Exception as e:
        return error_response(5004, str(e), path=f"/api/v1/ai/script/{script_id}")


# ==================== 分镜设计接口 ====================

@app.post("/ai/storyboard/generate", response_model=Dict[str, Any])
async def generate_storyboard(request: StoryboardGenerateRequest):
    """
    将剧本转换为分镜 JSON
    
    - **scriptId**: 剧本 ID
    - **title**: 剧本标题（可选，不填则从剧本读取）
    
    返回分镜数据，包含：
    - storyboardId: 分镜 ID
    - scriptId: 剧本 ID
    - title: 标题
    - scenes: 场景列表，每个场景包含多个镜头
    - 每个镜头包含：shotId, type, description, duration, prompt（AI 绘画提示词）
    
    支持的镜头类型：wide（广角）, closeup（特写）, medium（中景）, extreme（极特写）
    """
    try:
        # 生成分镜
        storyboard = await storyboard_service.generate_storyboard(
            script_id=request.scriptId,
            title=request.title
        )
        
        return {
            "code": 200,
            "data": {
                "storyboardId": storyboard["storyboardId"],
                "scriptId": storyboard["scriptId"],
                "title": storyboard["title"],
                "createdAt": storyboard["createdAt"],
                "scenes": storyboard["scenes"],
                "sceneCount": len(storyboard.get("scenes", [])),
                "totalShots": sum(len(scene.get("shots", [])) for scene in storyboard.get("scenes", []))
            },
            "message": "分镜生成成功"
        }
        
    except FileNotFoundError as e:
        return error_response(404, str(e), path="/ai/storyboard/generate")
    except ValueError as e:
        return error_response(400, str(e), path="/ai/storyboard/generate")
    except Exception as e:
        return error_response(5004, str(e), path="/ai/storyboard/generate")


@app.get("/ai/storyboard/{storyboard_id}", response_model=Dict[str, Any])
async def get_storyboard(storyboard_id: str = Path(..., description="分镜 ID")):
    """
    获取分镜详情
    
    - **storyboard_id**: 分镜 ID
    
    返回完整的分镜数据，包含所有场景和镜头信息
    """
    try:
        storyboard = await storyboard_service.get_storyboard(storyboard_id)
        
        return {
            "code": 200,
            "data": storyboard,
            "message": "获取成功"
        }
        
    except FileNotFoundError as e:
        return error_response(404, str(e), path=f"/ai/storyboard/{storyboard_id}")
    except ValueError as e:
        return error_response(400, str(e), path=f"/ai/storyboard/{storyboard_id}")
    except Exception as e:
        return error_response(5004, str(e), path=f"/ai/storyboard/{storyboard_id}")


@app.get("/ai/storyboards", response_model=Dict[str, Any])
async def list_storyboards(
    scriptId: Optional[str] = Query(None, description="剧本 ID（可选，用于过滤）"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取分镜列表
    
    - **scriptId**: 剧本 ID（可选，用于过滤）
    - **page**: 页码，默认 1
    - **pageSize**: 每页数量，默认 20
    """
    try:
        result = await storyboard_service.list_storyboards(
            script_id=scriptId,
            page=page,
            page_size=pageSize
        )
        
        return {
            "code": 200,
            "data": result,
            "message": "获取成功"
        }
        
    except Exception as e:
        return error_response(5004, str(e), path="/ai/storyboards")


@app.delete("/ai/storyboard/{storyboard_id}", response_model=Dict[str, Any])
async def delete_storyboard(storyboard_id: str = Path(..., description="分镜 ID")):
    """
    删除分镜
    
    - **storyboard_id**: 分镜 ID
    """
    try:
        success = await storyboard_service.delete_storyboard(storyboard_id)
        
        if not success:
            return error_response(404, "分镜不存在", path=f"/ai/storyboard/{storyboard_id}")
        
        return {
            "code": 200,
            "data": None,
            "message": "删除成功"
        }
        
    except Exception as e:
        return error_response(5004, str(e), path=f"/ai/storyboard/{storyboard_id}")


# ==================== AI 视频生成接口 ====================

@app.post("/api/v1/ai/video/generate", response_model=Dict[str, Any])
@limiter.limit("5/minute")  # AI 视频生成：每分钟 5 次
async def generate_ai_video(request: AIVideoGenerateRequest):
    """
    调用 Sora API 生成 AI 视频
    
    - **prompt**: 视频描述提示词（必填）
    - **duration**: 视频时长 (秒)，支持 5/10/15/30（可选，默认 5）
    - **resolution**: 分辨率，支持 720p/1080p/4k（可选，默认 1080p）
    
    异步任务模式，返回 taskId 用于查询进度
    """
    try:
        # 参数验证
        if not request.prompt or not request.prompt.strip():
            return error_response(4001, "提示词不能为空", path="/api/v1/ai/video/generate")
        
        if request.duration and request.duration not in [5, 10, 15, 30]:
            return error_response(4002, f"不支持的时长：{request.duration}，仅支持 5/10/15/30 秒", path="/api/v1/ai/video/generate")
        
        if request.resolution and request.resolution not in ["720p", "1080p", "4k"]:
            return error_response(4003, f"不支持的分辨率：{request.resolution}，仅支持 720p/1080p/4k", path="/api/v1/ai/video/generate")
        
        # 调用服务生成视频
        result = await ai_video_service.generate_video(
            prompt=request.prompt,
            duration=request.duration,
            resolution=request.resolution
        )
        
        return {
            "code": 202,
            "data": {
                "taskId": result["taskId"],
                "status": result["status"],
                "estimatedTime": result["estimatedTime"]
            },
            "message": "视频生成任务已提交"
        }
        
    except ValueError as e:
        return error_response(4001, str(e), path="/api/v1/ai/video/generate")
    except Exception as e:
        return error_response(5001, str(e), path="/api/v1/ai/video/generate")


@app.get("/api/v1/ai/video/{video_id}", response_model=Dict[str, Any])
async def get_ai_video_status(video_id: str = Path(..., description="视频任务 ID")):
    """
    查询 AI 视频生成进度
    
    - **video_id**: 视频任务 ID
    """
    try:
        result = await ai_video_service.query_video_status(video_id)
        
        return {
            "code": 200,
            "data": {
                "taskId": result["taskId"],
                "status": result["status"],
                "progress": result["progress"],
                "message": result.get("message"),
                "videoUrl": result.get("video_url"),
                "videoId": result.get("video_id")
            },
            "message": "查询成功"
        }
        
    except ValueError as e:
        return error_response(4001, str(e), path=f"/api/v1/ai/video/{video_id}")
    except Exception as e:
        return error_response(5001, str(e), path=f"/api/v1/ai/video/{video_id}")


@app.post("/api/v1/ai/video/{video_id}/download", response_model=Dict[str, Any])
async def download_ai_video(video_id: str = Path(..., description="视频 ID")):
    """
    下载已生成的 AI 视频
    
    - **video_id**: 视频 ID（任务完成后使用）
    """
    try:
        result = await ai_video_service.download_video(video_id)
        
        return {
            "code": 200,
            "data": {
                "videoId": result["videoId"],
                "fileName": result["fileName"],
                "fileSize": result["fileSize"],
                "downloadUrl": result["downloadUrl"]
            },
            "message": "下载成功"
        }
        
    except ValueError as e:
        return error_response(4005, str(e), path=f"/api/v1/ai/video/{video_id}/download")
    except Exception as e:
        return error_response(5003, str(e), path=f"/api/v1/ai/video/{video_id}/download")


@app.get("/api/v1/ai/video/config", response_model=Dict[str, Any])
async def get_ai_video_config():
    """
    获取 AI 视频生成配置信息
    
    返回支持的分辨率和时长列表
    """
    try:
        return {
            "code": 200,
            "data": {
                "supportedResolutions": ai_video_service.get_supported_resolutions(),
                "supportedDurations": ai_video_service.get_supported_durations(),
                "defaultResolution": ai_video_service.default_resolution,
                "defaultDuration": ai_video_service.default_duration
            },
            "message": "获取成功"
        }
        
    except Exception as e:
        return error_response(5004, str(e), path="/api/v1/ai/video/config")


# ==================== 配额管理数据模型 ====================

class QuotaQueryResponse(BaseModel):
    """配额查询响应"""
    userId: str
    quotaTotal: int
    quotaUsed: int
    quotaRemaining: int
    quotaExpire: Optional[str]
    dailyFreeQuota: int
    dailyQuotaUsed: int
    dailyQuotaRemaining: int


class QuotaDeductRequest(BaseModel):
    """配额扣费请求"""
    amount: int = Field(..., gt=0, description="扣费配额量（秒）")
    taskType: str = Field(..., description="任务类型：ai_video/asr_subtitle/voiceover")
    taskId: Optional[str] = Field(None, description="任务 ID")


class QuotaTopupRequest(BaseModel):
    """配额充值请求"""
    amount: int = Field(..., gt=0, description="充值配额量（秒）")
    expireDays: Optional[int] = Field(30, ge=1, le=365, description="过期天数，默认 30 天")


class QuotaTransactionResponse(BaseModel):
    """配额交易记录"""
    id: int
    userId: str
    amount: int
    taskType: str
    taskId: Optional[str]
    transactionType: str  # deduct/topup/reset
    createdAt: str


# ==================== 配额管理接口 ====================

@app.get("/api/v1/quota", response_model=Dict[str, Any])
async def get_quota(
    user_id: str = Query(..., description="用户 ID")
):
    """
    查询用户配额
    
    - **user_id**: 用户 ID
    
    返回配额详情，包括：
    - quotaTotal: 总额度（秒）
    - quotaUsed: 已用额度（秒）
    - quotaRemaining: 剩余额度（秒）
    - quotaExpire: 过期时间
    - dailyFreeQuota: 每日免费配额（60 秒/日）
    - dailyQuotaUsed: 今日已用配额
    - dailyQuotaRemaining: 今日剩余配额
    """
    try:
        quota = await quota_service.get_quota(user_id)
        
        return {
            "code": 200,
            "data": quota.to_dict(),
            "message": "查询成功"
        }
        
    except Exception as e:
        return error_response(5005, "查询配额失败", str(e), "/api/v1/quota")


@app.post("/api/v1/quota/deduct", response_model=Dict[str, Any])
async def deduct_quota(request: QuotaDeductRequest):
    """
    扣除用户配额
    
    - **amount**: 扣费配额量（秒）
    - **taskType**: 任务类型（ai_video/asr_subtitle/voiceover）
    - **taskId**: 任务 ID（可选）
    
    计费规则：
    - AI 配音：免费
    - ASR 字幕：¥0.02/分钟（10 分钟/日免费）
    - AI 视频生成：1 秒配额/秒视频（60 秒/日免费）
    - 批量生成：同 AI 视频
    """
    try:
        result = await quota_service.deduct_quota(
            user_id=request.taskId.split("-")[0] if request.taskId else "default",
            amount=request.amount,
            task_type=request.taskType,
            task_id=request.taskId
        )
        
        if not result["success"]:
            return error_response(4002, result.get("error", "扣费失败"), path="/api/v1/quota/deduct")
        
        return {
            "code": 200,
            "data": {
                "deducted": result["deducted"],
                "dailyDeducted": result.get("daily_deducted", 0),
                "paidDeducted": result.get("paid_deducted", 0),
                "remaining": result["remaining"]
            },
            "message": result.get("message", "扣费成功")
        }
        
    except Exception as e:
        return error_response(5005, "扣费失败", str(e), "/api/v1/quota/deduct")


@app.post("/api/v1/quota/topup", response_model=Dict[str, Any])
async def topup_quota(
    request: QuotaTopupRequest,
    user_id: str = Query(..., description="用户 ID")
):
    """
    充值用户配额
    
    - **user_id**: 用户 ID
    - **amount**: 充值配额量（秒）
    - **expireDays**: 过期天数，默认 30 天（1-365）
    """
    try:
        result = await quota_service.add_quota(
            user_id=user_id,
            amount=request.amount,
            expire_days=request.expireDays
        )
        
        return {
            "code": 200,
            "data": {
                "added": result["added"],
                "total": result["total"],
                "expire": result["expire"]
            },
            "message": result.get("message", "充值成功")
        }
        
    except Exception as e:
        return error_response(5005, "充值失败", str(e), "/api/v1/quota/topup")


@app.get("/api/v1/quota/transactions", response_model=Dict[str, Any])
async def get_quota_transactions(
    user_id: str = Query(..., description="用户 ID"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    查询用户配额交易历史
    
    - **user_id**: 用户 ID
    - **limit**: 返回数量限制，默认 50
    - **offset**: 偏移量，默认 0
    """
    try:
        transactions = await quota_service.get_transaction_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "code": 200,
            "data": {
                "total": len(transactions),
                "transactions": transactions
            },
            "message": "查询成功"
        }
        
    except Exception as e:
        return error_response(5005, "查询交易历史失败", str(e), "/api/v1/quota/transactions")


@app.get("/api/v1/quota/check", response_model=Dict[str, Any])
async def check_quota(
    user_id: str = Query(..., description="用户 ID"),
    amount: int = Query(..., gt=0, description="需要的配额量（秒）"),
    task_type: str = Query("ai_video", description="任务类型")
):
    """
    检查用户配额是否充足
    
    - **user_id**: 用户 ID
    - **amount**: 需要的配额量（秒）
    - **task_type**: 任务类型（ai_video/asr_subtitle/voiceover）
    """
    try:
        result = await quota_service.check_quota(
            user_id=user_id,
            required_amount=amount,
            task_type=task_type
        )
        
        return {
            "code": 200,
            "data": result,
            "message": "检查完成"
        }
        
    except Exception as e:
        return error_response(5005, "检查配额失败", str(e), "/api/v1/quota/check")


# ==================== 仪表盘接口 ====================

@app.get("/api/v1/dashboard/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    useCache: bool = Query(True, description="是否使用缓存，默认 true")
):
    """
    获取仪表盘统计数据
    
    - **useCache**: 是否使用缓存，默认 true（缓存 5 分钟过期）
    
    返回统计信息：
    - tasks: 任务统计（total/pending/completed）
    - files: 文件统计（total/videos/storageUsed）
    - scripts: 剧本统计（total）
    - batches: 批量任务统计（total）
    - usage: 配额使用（todayQuota/todayUsed）
    """
    try:
        stats = await dashboard_service.get_stats(use_cache=useCache)
        
        return {
            "code": 200,
            "data": stats,
            "message": "获取成功"
        }
        
    except Exception as e:
        return error_response(5004, "获取统计数据失败", str(e), "/api/v1/dashboard/stats")


@app.get("/api/v1/dashboard/recent", response_model=Dict[str, Any])
async def get_dashboard_recent(
    type: Optional[str] = Query(None, description="类型过滤：tasks/files/scripts/batches，不填则返回全部"),
    limit: int = Query(10, ge=1, le=100, description="每种类型返回数量限制，默认 10")
):
    """
    获取最近使用记录
    
    - **type**: 类型过滤（tasks/files/scripts/batches），不填则返回全部
    - **limit**: 每种类型返回数量限制，默认 10
    
    返回最近使用的任务、文件、剧本、批量任务列表
    """
    try:
        recent = await dashboard_service.get_recent(type=type, limit=limit)
        
        return {
            "code": 200,
            "data": recent,
            "message": "获取成功"
        }
        
    except Exception as e:
        return error_response(5004, "获取最近使用记录失败", str(e), "/api/v1/dashboard/recent")


# ==================== 模板管理接口 ====================

@app.post("/api/v1/templates", response_model=Dict[str, Any])
async def create_template(request: TemplateCreateRequest):
    """
    创建模板
    
    - **name**: 模板名称
    - **description**: 模板描述
    - **steps**: 模板步骤列表
    - **isPublic**: 是否公开
    """
    try:
        # 参数验证
        if not request.name or not request.name.strip():
            return error_response(4001, "模板名称不能为空", path="/api/v1/templates")
        
        if not request.steps or len(request.steps) == 0:
            return error_response(4002, "模板步骤不能为空", path="/api/v1/templates")
        
        # 调用服务创建模板
        steps_data = [step.dict() for step in request.steps]
        template = template_service.create_template(
            name=request.name,
            description=request.description,
            steps=steps_data,
            is_public=request.isPublic
        )
        
        return {
            "code": 201,
            "data": {
                "templateId": template["templateId"],
                "name": template["name"],
                "description": template["description"],
                "stepCount": len(template["steps"]),
                "isPublic": template["isPublic"],
                "createdAt": template["createdAt"]
            },
            "message": "模板创建成功"
        }
        
    except ValueError as e:
        return error_response(4001, str(e), path="/api/v1/templates")
    except Exception as e:
        return error_response(5001, str(e), path="/api/v1/templates")


@app.get("/api/v1/templates", response_model=Dict[str, Any])
async def get_templates(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    isPublic: Optional[bool] = Query(None, description="筛选公开/私有模板")
):
    """
    获取模板列表
    
    - **page**: 页码
    - **pageSize**: 每页数量
    - **isPublic**: 筛选公开/私有模板，不填表示全部
    """
    try:
        result = template_service.get_templates(
            page=page,
            page_size=pageSize,
            is_public=isPublic
        )
        
        return {
            "code": 200,
            "data": {
                "total": result["total"],
                "page": result["page"],
                "pageSize": result["pageSize"],
                "totalPages": result["totalPages"],
                "templates": result["templates"]
            },
            "message": "获取成功"
        }
        
    except Exception as e:
        return error_response(5001, str(e), path="/api/v1/templates")


@app.get("/api/v1/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(template_id: str = Path(..., description="模板 ID")):
    """
    获取模板详情
    
    - **template_id**: 模板 ID
    """
    try:
        template = template_service.get_template(template_id)
        
        return {
            "code": 200,
            "data": template,
            "message": "获取成功"
        }
        
    except ValueError as e:
        return error_response(4001, str(e), path=f"/api/v1/templates/{template_id}")
    except FileNotFoundError as e:
        return error_response(4004, str(e), path=f"/api/v1/templates/{template_id}")
    except Exception as e:
        return error_response(5001, str(e), path=f"/api/v1/templates/{template_id}")


@app.delete("/api/v1/templates/{template_id}", response_model=Dict[str, Any])
async def delete_template(template_id: str = Path(..., description="模板 ID")):
    """
    删除模板
    
    - **template_id**: 模板 ID
    """
    try:
        template_service.delete_template(template_id)
        
        return {
            "code": 200,
            "message": "模板删除成功"
        }
        
    except ValueError as e:
        return error_response(4001, str(e), path=f"/api/v1/templates/{template_id}")
    except FileNotFoundError as e:
        return error_response(4004, str(e), path=f"/api/v1/templates/{template_id}")
    except Exception as e:
        return error_response(5001, str(e), path=f"/api/v1/templates/{template_id}")


@app.post("/api/v1/templates/{template_id}/apply", response_model=Dict[str, Any])
async def apply_template(template_id: str = Path(..., description="模板 ID"),
                        request: TemplateApplyRequest = None):
    """
    应用模板到视频生成任务
    
    - **template_id**: 模板 ID
    - **videoId**: 视频 ID（可选）
    """
    try:
        video_id = request.videoId if request else None
        result = template_service.apply_template(template_id, video_id)
        
        return {
            "code": 200,
            "data": result,
            "message": "模板应用成功"
        }
        
    except ValueError as e:
        return error_response(4001, str(e), path=f"/api/v1/templates/{template_id}/apply")
    except FileNotFoundError as e:
        return error_response(4004, str(e), path=f"/api/v1/templates/{template_id}/apply")
    except Exception as e:
        return error_response(5001, str(e), path=f"/api/v1/templates/{template_id}/apply")


# ==================== 健康检查 ====================

# ==================== 批量生成接口 ====================

@app.post("/api/v1/ai/batch/generate", response_model=Dict[str, Any])
async def batch_generate(request: BatchGenerateRequest):
    """
    批量生成多集短剧
    
    - **scriptId**: 剧本 ID
    - **episodeRange**: 集数范围 {"start": 1, "end": 80}
    - **parallelism**: 并行度，默认 4（1-10）
    """
    try:
        # 验证集数范围
        if request.episodeRange.start > request.episodeRange.end:
            return error_response(400, "起始集数不能大于结束集数", 
                                 path="/api/v1/ai/batch/generate")
        
        # 创建批量任务
        batch_info = await batch_service.create_batch_job(
            script_id=request.scriptId,
            episode_range=request.episodeRange.dict(),
            parallelism=request.parallelism
        )
        
        return {
            "code": 202,
            "data": {
                "batchId": batch_info["batchId"],
                "totalEpisodes": batch_info["totalEpisodes"],
                "totalShots": batch_info["totalShots"],
                "status": batch_info["status"],
                "progress": batch_info["progress"]
            },
            "message": "批量任务已创建"
        }
        
    except Exception as e:
        return error_response(5003, "批量任务创建失败", str(e), 
                             path="/api/v1/ai/batch/generate")


@app.get("/api/v1/ai/batch/{batch_id}", response_model=Dict[str, Any])
async def get_batch_status(batch_id: str = Path(..., description="批量任务 ID")):
    """
    查询批量任务进度
    
    - **batch_id**: 批量任务 ID
    """
    try:
        batch_info = await batch_service.query_batch_status(batch_id)
        
        if not batch_info:
            return error_response(4001, "批量任务不存在", 
                                 path=f"/api/v1/ai/batch/{batch_id}")
        
        return {
            "code": 200,
            "data": batch_info
        }
        
    except Exception as e:
        return error_response(5003, "查询批量任务失败", str(e), 
                             path=f"/api/v1/ai/batch/{batch_id}")


@app.delete("/api/v1/ai/batch/{batch_id}", response_model=Dict[str, Any])
async def cancel_batch(batch_id: str = Path(..., description="批量任务 ID")):
    """
    取消批量任务
    
    - **batch_id**: 批量任务 ID
    """
    try:
        result = await batch_service.cancel_batch(batch_id)
        
        if not result["success"]:
            if result.get("code") == 4001:
                return error_response(4001, "批量任务不存在", 
                                     path=f"/api/v1/ai/batch/{batch_id}")
            elif result.get("code") == 4002:
                return error_response(4002, "任务已完成，无法取消", 
                                     path=f"/api/v1/ai/batch/{batch_id}")
        
        return {
            "code": 200,
            "message": "批量任务已取消"
        }
        
    except Exception as e:
        return error_response(5003, "取消批量任务失败", str(e), 
                             path=f"/api/v1/ai/batch/{batch_id}")


@app.get("/api/v1/ai/batches", response_model=Dict[str, Any])
async def list_batches(
    scriptId: Optional[str] = Query(None, description="剧本 ID 过滤"),
    status: Optional[str] = Query(None, description="状态过滤：pending/processing/completed/failed/cancelled"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取批量任务列表
    
    - **scriptId**: 剧本 ID 过滤
    - **status**: 状态过滤
    - **page**: 页码
    - **pageSize**: 每页数量
    """
    try:
        offset = (page - 1) * pageSize
        batches = await batch_service.list_batches(
            script_id=scriptId,
            status=status,
            limit=pageSize,
            offset=offset
        )
        
        return {
            "code": 200,
            "data": {
                "total": len(batches),
                "page": page,
                "pageSize": pageSize,
                "batches": batches
            }
        }
        
    except Exception as e:
        return error_response(5003, "获取批量任务列表失败", str(e), 
                             path="/api/v1/ai/batches")


# ==================== 素材管理模块接口 ====================

class MusicListResponse(BaseModel):
    total: int
    page: int
    pageSize: int
    totalPages: int
    musicList: List[Dict[str, Any]]
    genres: List[str]
    moods: List[str]

class TemplateListResponse(BaseModel):
    total: int
    templates: List[Dict[str, Any]]
    types: List[str]

class MaterialUploadResponse(BaseModel):
    materialId: str
    fileName: str
    fileSize: int
    materialType: str
    category: str
    uploadTime: str
    filePath: str

class MaterialPreviewResponse(BaseModel):
    materialId: str
    fileName: str
    fileSize: int
    materialType: str
    category: str
    tags: List[str]
    description: str
    uploadTime: str
    filePath: str
    previewUrl: str
    status: str

class MaterialUploadRequest(BaseModel):
    materialType: str = Field(..., description="素材类型：music/template/other")
    category: str = Field(..., description="分类")
    tags: List[str] = Field(default=[], description="标签列表")
    description: str = Field(default="", description="描述")


@app.get("/api/v1/materials/music", response_model=Dict[str, Any])
async def get_music_list(
    genre: Optional[str] = Query(None, description="音乐类型"),
    mood: Optional[str] = Query(None, description="情绪"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取音乐列表
    
    - **genre**: 音乐类型筛选（流行/摇滚/电子/古典/爵士/民谣/说唱/轻音乐）
    - **mood**: 情绪筛选（欢快/悲伤/激昂/平静/浪漫/紧张/温馨/励志）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        result = material_service.get_music_list(
            genre=genre,
            mood=mood,
            page=page,
            page_size=page_size
        )
        return {
            "code": 200,
            "data": result,
            "message": "获取音乐列表成功"
        }
    except Exception as e:
        return error_response(5001, str(e), path="/api/v1/materials/music")


@app.get("/api/v1/materials/templates", response_model=Dict[str, Any])
async def get_templates_list(
    type: Optional[str] = Query(None, description="模板类型")
):
    """
    获取模板列表
    
    - **type**: 模板类型筛选（片头/片尾/转场/字幕/特效/滤镜）
    """
    try:
        result = material_service.get_templates_list(type=type)
        return {
            "code": 200,
            "data": result,
            "message": "获取模板列表成功"
        }
    except Exception as e:
        return error_response(5001, str(e), path="/api/v1/materials/templates")


@app.post("/api/v1/materials/upload", response_model=Dict[str, Any])
async def upload_material(
    file: UploadFile = File(..., description="素材文件"),
    material_type: str = Form(..., description="素材类型：music/template/other"),
    category: str = Form(..., description="分类"),
    tags: str = Form(default="[]", description="标签列表（JSON 格式）"),
    description: str = Form(default="", description="描述")
):
    """
    上传素材
    
    - **file**: 素材文件
    - **material_type**: 素材类型（music/template/other）
    - **category**: 分类
    - **tags**: 标签列表（JSON 格式）
    - **description**: 描述
    """
    import json as json_module
    
    try:
        # 保存上传的文件
        temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 解析 tags
        try:
            tags_list = json_module.loads(tags) if tags else []
            if not isinstance(tags_list, list):
                tags_list = [tags_list]
        except:
            tags_list = [tags] if tags else []
        
        # 上传素材
        result = material_service.upload_material(
            file_path=temp_path,
            material_type=material_type,
            category=category,
            tags=tags_list,
            description=description
        )
        
        return {
            "code": 200,
            "data": result,
            "message": "素材上传成功"
        }
    except FileNotFoundError as e:
        return error_response(4004, str(e), path="/api/v1/materials/upload")
    except ValueError as e:
        return error_response(4001, str(e), path="/api/v1/materials/upload")
    except Exception as e:
        return error_response(5001, str(e), path="/api/v1/materials/upload")


@app.get("/api/v1/materials/preview/{file_id}", response_model=Dict[str, Any])
async def preview_material(file_id: str = Path(..., description="素材 ID")):
    """
    预览素材
    
    - **file_id**: 素材 ID
    """
    try:
        result = material_service.preview_material(file_id)
        return {
            "code": 200,
            "data": result,
            "message": "获取素材预览成功"
        }
    except FileNotFoundError as e:
        return error_response(4004, str(e), path=f"/api/v1/materials/preview/{file_id}")
    except ValueError as e:
        return error_response(4001, str(e), path=f"/api/v1/materials/preview/{file_id}")
    except Exception as e:
        return error_response(5001, str(e), path=f"/api/v1/materials/preview/{file_id}")


@app.get("/api/v1/materials/stats", response_model=Dict[str, Any])
async def get_material_stats():
    """
    获取素材统计信息
    
    返回素材库的统计信息，包括音乐数量、模板数量、存储使用等
    """
    try:
        result = material_service.get_material_stats()
        return {
            "code": 200,
            "data": result,
            "message": "获取素材统计成功"
        }
    except Exception as e:
        return error_response(5001, str(e), path="/api/v1/materials/stats")


# ==================== 系统模块接口 ====================

@app.get("/api/v1/health")
async def health_check():
    """
    健康检查
    
    返回服务健康状态，包括：
    - status: 整体状态 (healthy/degraded/unhealthy)
    - version: 服务版本
    - uptime: 运行时间（秒）
    - timestamp: 检查时间戳
    - checks: 各项检查详情 (api/storage/database/memory/disk)
    """
    result = system_service.health_check()
    return {
        "code": 200,
        "data": result,
        "message": "健康检查完成"
    }


@app.get("/api/v1/system/info")
async def get_system_info():
    """
    获取系统信息
    
    返回详细系统信息，包括：
    - os: 操作系统信息
    - cpu: CPU 信息
    - memory: 内存信息
    - disk: 磁盘信息
    - network: 网络信息
    - python: Python 环境信息
    """
    result = system_service.get_system_info()
    return {
        "code": 200,
        "data": result,
        "message": "获取成功"
    }


# ==================== 特效管理 ====================

class TextEffectRequest(BaseModel):
    videoId: str
    text: str
    outputName: Optional[str] = None
    style: Optional[Dict[str, Any]] = Field(default_factory=dict)

class FollowEffectRequest(BaseModel):
    videoId: str
    outputName: Optional[str] = None
    startTime: float = Field(0, ge=0)
    duration: float = Field(5.0, gt=0)
    style: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PIPEffectRequest(BaseModel):
    mainVideoId: str
    pipVideoId: str
    outputName: Optional[str] = None
    layout: str = Field("bottom-right", description="布局：bottom-right/bottom-left/center")
    style: Optional[Dict[str, Any]] = Field(default_factory=dict)

class EffectTaskResponse(BaseModel):
    taskId: str
    status: str
    outputUrl: Optional[str] = None


@app.post("/api/v1/effects/text", response_model=Dict[str, Any])
async def apply_text_effect(request: TextEffectRequest):
    """
    应用文字特效到视频
    
    - **videoId**: 视频文件 ID
    - **text**: 文字内容
    - **outputName**: 输出文件名
    - **style**: 样式配置（fontSize, color, effect, position 等）
    """
    try:
        video_path = file_service.get_file_path(request.videoId)
        output_name = request.outputName or f"effect_text_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(file_service.base_dir, "output", output_name)
        
        effect_service.apply_text_effect(video_path, request.text, output_path, request.style)
        
        return {
            "code": 200,
            "data": {"outputName": output_name, "downloadUrl": f"/api/v1/files/output/{output_name}"},
            "message": "文字特效应用成功"
        }
    except Exception as e:
        return error_response(5002, str(e), path="/api/v1/effects/text")


@app.post("/api/v1/effects/follow", response_model=Dict[str, Any])
async def apply_follow_effect(request: FollowEffectRequest):
    """
    应用点关注特效到视频
    
    - **videoId**: 视频文件 ID
    - **outputName**: 输出文件名
    - **startTime**: 开始时间（秒）
    - **duration**: 持续时长（秒）
    - **style**: 样式配置（buttonType, animation, text, position 等）
    """
    try:
        video_path = file_service.get_file_path(request.videoId)
        output_name = request.outputName or f"effect_follow_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(file_service.base_dir, "output", output_name)
        
        effect_service.apply_follow_effect(video_path, output_path, request.startTime, request.duration, request.style)
        
        return {
            "code": 200,
            "data": {"outputName": output_name, "downloadUrl": f"/api/v1/files/output/{output_name}"},
            "message": "点关注特效应用成功"
        }
    except Exception as e:
        return error_response(5002, str(e), path="/api/v1/effects/follow")


@app.post("/api/v1/effects/pip", response_model=Dict[str, Any])
async def apply_pip_effect(request: PIPEffectRequest):
    """
    应用画中画特效
    
    - **mainVideoId**: 主视频文件 ID
    - **pipVideoId**: 画中画视频文件 ID
    - **outputName**: 输出文件名
    - **layout**: 布局模式（bottom-right/bottom-left/center）
    - **style**: 样式配置（size, border, shadow, transition 等）
    """
    try:
        main_path = file_service.get_file_path(request.mainVideoId)
        pip_path = file_service.get_file_path(request.pipVideoId)
        output_name = request.outputName or f"effect_pip_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(file_service.base_dir, "output", output_name)
        
        effect_service.apply_pip_effect(main_path, pip_path, output_path, request.layout, request.style)
        
        return {
            "code": 200,
            "data": {"outputName": output_name, "downloadUrl": f"/api/v1/files/output/{output_name}"},
            "message": "画中画特效应用成功"
        }
    except Exception as e:
        return error_response(5002, str(e), path="/api/v1/effects/pip")


# ==================== 启动服务器 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
