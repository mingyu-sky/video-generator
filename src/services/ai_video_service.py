"""
AI 视频生成服务 (Sora)
调用 Sora API 生成 AI 视频
支持多种分辨率和时长
"""
import os
import uuid
import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


class VideoResolution(Enum):
    """视频分辨率枚举"""
    P720 = "720p"
    P1080 = "1080p"
    P4K = "4k"


class VideoDuration(Enum):
    """视频时长枚举"""
    S5 = 5
    S10 = 10
    S15 = 15
    S30 = 30


class AIVideoService:
    """AI 视频生成服务 (Sora)"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Sora 服务地址
        self.sora_base_url = os.getenv("SORA_API_URL", "http://8.215.85.59:15321")
        
        # 视频存储目录
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
        self.videos_dir = os.path.join(self.base_dir, "videos", "ai_generated")
        
        # 确保目录存在
        os.makedirs(self.videos_dir, exist_ok=True)
        
        # HTTP 客户端超时配置 (秒)
        self.timeout_seconds = 300  # 5 分钟超时
        
        # 支持的分率列表
        self.supported_resolutions = ["720p", "1080p", "4k"]
        
        # 支持的时长列表 (秒)
        self.supported_durations = [5, 10, 15, 30]
        
        # 默认配置
        self.default_resolution = "1080p"
        self.default_duration = 5
        
        self._initialized = True
    
    async def generate_video(
        self,
        prompt: str,
        duration: int = None,
        resolution: str = None,
        task_id: str = None
    ) -> Dict[str, Any]:
        """
        调用 Sora API 生成视频
        
        Args:
            prompt: 视频描述提示词
            duration: 视频时长 (秒), 支持 5/10/15/30
            resolution: 分辨率，支持 720p/1080p/4k
            task_id: 任务 ID (可选，不传则自动生成)
            
        Returns:
            包含 taskId, status, estimatedTime 等信息的字典
        """
        # 参数验证
        if not prompt or not prompt.strip():
            raise ValueError("提示词不能为空")
        
        # 设置默认值
        duration = duration or self.default_duration
        resolution = resolution or self.default_resolution
        
        # 验证时长
        if duration not in self.supported_durations:
            raise ValueError(f"不支持的时长：{duration}，仅支持 {self.supported_durations}")
        
        # 验证分辨率
        if resolution not in self.supported_resolutions:
            raise ValueError(f"不支持的分辨率：{resolution}，仅支持 {self.supported_resolutions}")
        
        # 生成任务 ID
        if task_id is None:
            task_id = f"video-{uuid.uuid4().hex[:12]}"
        
        # 构建请求参数
        request_data = {
            "prompt": prompt.strip(),
            "duration": duration,
            "resolution": resolution,
            "task_id": task_id
        }
        
        try:
            # 异步调用 Sora API
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.sora_base_url}/api/v1/generate",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "taskId": task_id,
                        "status": "pending",
                        "estimatedTime": result.get("estimated_time", 60),
                        "sora_task_id": result.get("task_id", task_id),
                        "prompt": prompt.strip(),
                        "duration": duration,
                        "resolution": resolution,
                        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    }
                else:
                    raise Exception(f"Sora API 返回错误：{response.status_code} - {response.text}")
                    
        except httpx.TimeoutException:
            raise Exception(f"Sora API 调用超时 (> {self.timeout_seconds}秒)")
        except httpx.RequestError as e:
            raise Exception(f"Sora API 请求失败：{str(e)}")
    
    async def query_video_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询视频生成进度
        
        Args:
            task_id: 任务 ID
            
        Returns:
            包含 status, progress, message 等信息的字典
        """
        if not task_id:
            raise ValueError("任务 ID 不能为空")
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.sora_base_url}/api/v1/task/{task_id}"
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status", "unknown")
                    
                    return {
                        "taskId": task_id,
                        "status": status,
                        "progress": result.get("progress", 0),
                        "message": result.get("message", ""),
                        "video_url": result.get("video_url"),
                        "video_id": result.get("video_id"),
                        "created_at": result.get("created_at"),
                        "completed_at": result.get("completed_at")
                    }
                else:
                    raise Exception(f"Sora API 返回错误：{response.status_code} - {response.text}")
                    
        except httpx.TimeoutException:
            raise Exception(f"查询状态超时 (> 30 秒)")
        except httpx.RequestError as e:
            raise Exception(f"查询状态失败：{str(e)}")
    
    async def download_video(self, video_id: str, output_filename: str = None) -> Dict[str, Any]:
        """
        下载生成的视频
        
        Args:
            video_id: 视频 ID
            output_filename: 输出文件名 (可选)
            
        Returns:
            包含 filePath, fileName, fileSize 等信息的字典
        """
        if not video_id:
            raise ValueError("视频 ID 不能为空")
        
        # 先查询视频信息获取下载 URL
        status_info = await self.query_video_status(video_id)
        
        if status_info["status"] != "completed":
            raise ValueError(f"视频尚未完成，当前状态：{status_info['status']}")
        
        video_url = status_info.get("video_url")
        if not video_url:
            raise ValueError("未找到视频下载 URL")
        
        # 生成文件名
        if output_filename is None:
            output_filename = f"{video_id}.mp4"
        
        # 确保扩展名正确
        if not output_filename.endswith(".mp4"):
            output_filename = output_filename + ".mp4"
        
        file_path = os.path.join(self.videos_dir, output_filename)
        
        try:
            # 下载视频文件
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                async with client.stream("GET", video_url) as response:
                    if response.status_code != 200:
                        raise Exception(f"下载失败：{response.status_code}")
                    
                    # 流式写入文件
                    with open(file_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            return {
                "videoId": video_id,
                "fileName": output_filename,
                "filePath": file_path,
                "fileSize": file_size,
                "downloadUrl": f"/api/v1/videos/ai/{output_filename}",
                "downloadedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
            
        except httpx.TimeoutException:
            raise Exception(f"视频下载超时 (> {self.timeout_seconds}秒)")
        except httpx.RequestError as e:
            raise Exception(f"视频下载失败：{str(e)}")
    
    def get_supported_resolutions(self) -> list:
        """获取支持的分辨率列表"""
        return self.supported_resolutions.copy()
    
    def get_supported_durations(self) -> list:
        """获取支持的时长列表"""
        return self.supported_durations.copy()


# 全局单例
ai_video_service = AIVideoService()
