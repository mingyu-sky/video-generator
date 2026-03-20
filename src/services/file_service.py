"""
文件管理服务
处理文件上传、存储、查询、删除等操作
"""
import os
import json
import shutil
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid

class FileService:
    """文件管理服务"""
    
    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
        self.videos_dir = os.path.join(self.base_dir, "videos")
        self.audio_dir = os.path.join(self.base_dir, "audio")
        self.images_dir = os.path.join(self.base_dir, "images")
        self.subtitles_dir = os.path.join(self.base_dir, "subtitles")
        self.meta_dir = os.path.join(self.base_dir, "metadata")
        
        # 确保目录存在
        for dir_path in [self.videos_dir, self.audio_dir, self.images_dir, self.subtitles_dir, self.meta_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def _get_type_dir(self, file_type: str) -> str:
        """根据文件类型获取存储目录"""
        type_dirs = {
            "video": self.videos_dir,
            "audio": self.audio_dir,
            "image": self.images_dir
        }
        return type_dirs.get(file_type, self.videos_dir)
    
    def _get_meta_path(self, file_id: str) -> str:
        """获取元数据文件路径"""
        return os.path.join(self.meta_dir, f"{file_id}.json")
    
    async def save_file(self, file_id: str, content: bytes, filename: str, file_type: str) -> str:
        """
        保存文件
        
        Args:
            file_id: 文件 ID
            content: 文件内容
            filename: 原始文件名
            file_type: 文件类型
            
        Returns:
            保存路径
        """
        # 获取存储目录
        save_dir = self._get_type_dir(file_type)
        
        # 生成保存路径
        file_ext = os.path.splitext(filename)[1]
        save_path = os.path.join(save_dir, f"{file_id}{file_ext}")
        
        # 保存文件
        with open(save_path, 'wb') as f:
            f.write(content)
        
        # 保存元数据
        metadata = {
            "fileId": file_id,
            "fileName": filename,
            "fileType": file_type,
            "filePath": save_path,
            "uploadTime": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        
        meta_path = self._get_meta_path(file_id)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return save_path
    
    async def get_file_metadata(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        获取文件元数据（时长、格式、分辨率等）
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            元数据字典
        """
        metadata = {
            "format": os.path.splitext(file_path)[1][1:].lower(),
            "duration": None,
            "resolution": None
        }
        
        # 对于视频和音频，尝试获取时长和分辨率
        if file_type in ["video", "audio"]:
            try:
                # 使用 ffmpeg-python 获取媒体信息
                import ffmpeg
                probe = ffmpeg.probe(file_path)
                
                if file_type == "video":
                    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                    if video_stream:
                        metadata["resolution"] = f"{video_stream.get('width', 'N/A')}x{video_stream.get('height', 'N/A')}"
                
                audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
                if audio_stream and 'duration' in audio_stream:
                    metadata["duration"] = float(audio_stream['duration'])
                elif 'format' in probe and 'duration' in probe['format']:
                    metadata["duration"] = float(probe['format']['duration'])
                    
            except Exception as e:
                # 如果无法获取元数据，返回默认值
                pass
        
        return metadata
    
    async def list_files(self, type: Optional[str] = None, page: int = 1, page_size: int = 20, 
                        sort_by: str = "uploadTime", order: str = "desc") -> List[Dict[str, Any]]:
        """
        获取文件列表
        
        Args:
            type: 文件类型过滤
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            order: 排序顺序
            
        Returns:
            文件列表
        """
        files = []
        
        # 确定要扫描的目录
        if type:
            dirs_to_scan = [self._get_type_dir(type)]
        else:
            dirs_to_scan = [self.videos_dir, self.audio_dir, self.images_dir]
        
        # 扫描文件
        for scan_dir in dirs_to_scan:
            if not os.path.exists(scan_dir):
                continue
                
            for filename in os.listdir(scan_dir):
                if filename.endswith('.json'):
                    continue
                    
                file_id = os.path.splitext(filename)[0]
                meta_path = self._get_meta_path(file_id)
                
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        files.append({
                            "fileId": metadata["fileId"],
                            "fileName": metadata["fileName"],
                            "fileSize": os.path.getsize(metadata["filePath"]),
                            "fileType": metadata["fileType"],
                            "uploadTime": metadata["uploadTime"]
                        })
                    except:
                        pass
        
        # 排序
        reverse = (order.lower() == "desc")
        if sort_by == "fileName":
            files.sort(key=lambda x: x["fileName"], reverse=reverse)
        else:  # uploadTime
            files.sort(key=lambda x: x["uploadTime"], reverse=reverse)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        
        return files[start:end]
    
    async def count_files(self, type: Optional[str] = None) -> int:
        """
        统计文件数量
        
        Args:
            type: 文件类型过滤
            
        Returns:
            文件数量
        """
        count = 0
        
        if type:
            dirs_to_scan = [self._get_type_dir(type)]
        else:
            dirs_to_scan = [self.videos_dir, self.audio_dir, self.images_dir]
        
        for scan_dir in dirs_to_scan:
            if os.path.exists(scan_dir):
                for filename in os.listdir(scan_dir):
                    if not filename.endswith('.json'):
                        count += 1
        
        return count
    
    async def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文件详情
        
        Args:
            file_id: 文件 ID
            
        Returns:
            文件信息字典，不存在则返回 None
        """
        meta_path = self._get_meta_path(file_id)
        
        if not os.path.exists(meta_path):
            return None
        
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            file_path = metadata["filePath"]
            if not os.path.exists(file_path):
                return None
            
            return {
                "fileId": metadata["fileId"],
                "fileName": metadata["fileName"],
                "fileSize": os.path.getsize(file_path),
                "fileType": metadata["fileType"],
                "uploadTime": metadata["uploadTime"],
                "format": os.path.splitext(file_path)[1][1:].lower(),
                "duration": None,  # 可以从元数据中读取或动态获取
                "resolution": None
            }
        except:
            return None
    
    async def get_file_path(self, file_id: str) -> Optional[str]:
        """
        获取文件物理路径
        
        Args:
            file_id: 文件 ID
            
        Returns:
            文件路径，不存在则返回 None
        """
        meta_path = self._get_meta_path(file_id)
        
        if not os.path.exists(meta_path):
            return None
        
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            file_path = metadata["filePath"]
            if os.path.exists(file_path):
                return file_path
        except:
            pass
        
        return None
    
    async def delete_file(self, file_id: str) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件 ID
            
        Returns:
            是否删除成功
        """
        meta_path = self._get_meta_path(file_id)
        
        if not os.path.exists(meta_path):
            return False
        
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            file_path = metadata["filePath"]
            
            # 删除文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 删除元数据
            os.remove(meta_path)
            
            return True
        except:
            return False
