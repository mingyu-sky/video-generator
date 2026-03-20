"""
素材管理服务
用于管理音乐、模板等素材的上传、查询和预览
"""
import os
import json
import uuid
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import hashlib


class MaterialService:
    """素材管理服务"""
    
    def __init__(self, file_service=None):
        self.file_service = file_service
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "materials")
        
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "music"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "templates"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "uploads"), exist_ok=True)
        
        # 音乐类型和情绪分类
        self.music_genres = ["流行", "摇滚", "电子", "古典", "爵士", "民谣", "说唱", "轻音乐"]
        self.music_moods = ["欢快", "悲伤", "激昂", "平静", "浪漫", "紧张", "温馨", "励志"]
        
        # 模板类型
        self.template_types = ["片头", "片尾", "转场", "字幕", "特效", "滤镜"]
    
    def _generate_material_id(self, file_name: str, material_type: str) -> str:
        """生成素材 ID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        unique_str = f"{material_type}-{file_name}-{timestamp}-{uuid.uuid4()}"
        return f"mat-{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"
    
    def _get_music_path(self, material_id: str) -> str:
        """获取音乐文件路径"""
        return os.path.join(self.base_dir, "music", f"{material_id}.json")
    
    def _get_template_path(self, material_id: str) -> str:
        """获取模板文件路径"""
        return os.path.join(self.base_dir, "templates", f"{material_id}.json")
    
    def _get_upload_path(self, material_id: str, file_name: str) -> str:
        """获取上传文件路径"""
        return os.path.join(self.base_dir, "uploads", f"{material_id}_{file_name}")
    
    def get_music_list(self, genre: Optional[str] = None, mood: Optional[str] = None, 
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        获取音乐列表
        
        Args:
            genre: 音乐类型筛选
            mood: 情绪筛选
            page: 页码
            page_size: 每页数量
            
        Returns:
            音乐列表数据
        """
        music_dir = os.path.join(self.base_dir, "music")
        music_list = []
        
        # 读取所有音乐元数据
        if os.path.exists(music_dir):
            for filename in os.listdir(music_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(music_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            music_data = json.load(f)
                            
                            # 筛选条件
                            if genre and music_data.get('genre') != genre:
                                continue
                            if mood and music_data.get('mood') != mood:
                                continue
                                
                            music_list.append(music_data)
                    except (json.JSONDecodeError, IOError):
                        continue
        
        # 分页
        total = len(music_list)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_list = music_list[start_idx:end_idx]
        
        return {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            "musicList": paginated_list,
            "genres": self.music_genres,
            "moods": self.music_moods
        }
    
    def get_templates_list(self, type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取模板列表
        
        Args:
            type: 模板类型筛选
            
        Returns:
            模板列表数据
        """
        template_dir = os.path.join(self.base_dir, "templates")
        template_list = []
        
        # 读取所有模板元数据
        if os.path.exists(template_dir):
            for filename in os.listdir(template_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(template_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                            
                            # 筛选条件
                            if type and template_data.get('type') != type:
                                continue
                                
                            template_list.append(template_data)
                    except (json.JSONDecodeError, IOError):
                        continue
        
        return {
            "total": len(template_list),
            "templates": template_list,
            "types": self.template_types
        }
    
    def upload_material(self, file_path: str, material_type: str, category: str, 
                       tags: List[str] = None, description: str = "") -> Dict[str, Any]:
        """
        上传素材
        
        Args:
            file_path: 文件路径
            material_type: 素材类型 (music/template/other)
            category: 分类 (音乐类型/模板类型等)
            tags: 标签列表
            description: 描述
            
        Returns:
            上传结果
            
        Raises:
            ValueError: 参数错误
            FileNotFoundError: 文件不存在
        """
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在：{file_path}")
        
        if not material_type or material_type not in ["music", "template", "other"]:
            raise ValueError("素材类型必须是 music、template 或 other")
        
        if not category:
            raise ValueError("分类不能为空")
        
        file_name = os.path.basename(file_path)
        material_id = self._generate_material_id(file_name, material_type)
        upload_time = datetime.now(timezone.utc).isoformat()
        
        # 复制文件到上传目录
        dest_path = self._get_upload_path(material_id, file_name)
        shutil.copy2(file_path, dest_path)
        
        # 获取文件大小
        file_size = os.path.getsize(dest_path)
        
        # 创建元数据
        metadata = {
            "materialId": material_id,
            "fileName": file_name,
            "fileSize": file_size,
            "materialType": material_type,
            "category": category,
            "tags": tags or [],
            "description": description,
            "uploadTime": upload_time,
            "filePath": dest_path,
            "status": "active"
        }
        
        # 根据类型添加特定字段
        if material_type == "music":
            metadata["genre"] = category
            metadata["mood"] = tags[0] if tags and len(tags) > 0 else "未知"
            metadata["duration"] = 0  # 后续可通过音频分析获取
            # 保存到音乐元数据目录
            meta_path = self._get_music_path(material_id)
        elif material_type == "template":
            metadata["templateType"] = category
            # 保存到模板元数据目录
            meta_path = self._get_template_path(material_id)
        else:
            # 其他类型保存到通用元数据目录
            meta_path = os.path.join(self.base_dir, "uploads", f"{material_id}.json")
        
        # 保存元数据
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return {
            "materialId": material_id,
            "fileName": file_name,
            "fileSize": file_size,
            "materialType": material_type,
            "category": category,
            "uploadTime": upload_time,
            "filePath": dest_path
        }
    
    def preview_material(self, file_id: str) -> Dict[str, Any]:
        """
        预览素材
        
        Args:
            file_id: 素材 ID
            
        Returns:
            预览信息
            
        Raises:
            ValueError: 素材 ID 无效
            FileNotFoundError: 文件不存在
        """
        if not file_id:
            raise ValueError("素材 ID 不能为空")
        
        # 尝试在不同目录查找素材
        possible_paths = [
            os.path.join(self.base_dir, "music", f"{file_id}.json"),
            os.path.join(self.base_dir, "templates", f"{file_id}.json"),
            os.path.join(self.base_dir, "uploads", f"{file_id}.json"),
        ]
        
        metadata = None
        meta_path = None
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        meta_path = path
                        break
                except (json.JSONDecodeError, IOError):
                    continue
        
        if not metadata:
            # 尝试直接查找文件（不带.json 后缀的）
            upload_dir = os.path.join(self.base_dir, "uploads")
            if os.path.exists(upload_dir):
                for filename in os.listdir(upload_dir):
                    if filename.startswith(f"{file_id}_"):
                        file_path = os.path.join(upload_dir, filename)
                        return {
                            "materialId": file_id,
                            "fileName": filename,
                            "fileSize": os.path.getsize(file_path),
                            "filePath": file_path,
                            "previewUrl": f"/api/v1/materials/preview/{file_id}",
                            "status": "available"
                        }
            
            raise FileNotFoundError(f"素材不存在：{file_id}")
        
        # 返回预览信息
        file_path = metadata.get('filePath', '')
        preview_info = {
            "materialId": metadata.get('materialId', file_id),
            "fileName": metadata.get('fileName', ''),
            "fileSize": metadata.get('fileSize', 0),
            "materialType": metadata.get('materialType', 'unknown'),
            "category": metadata.get('category', ''),
            "tags": metadata.get('tags', []),
            "description": metadata.get('description', ''),
            "uploadTime": metadata.get('uploadTime', ''),
            "filePath": file_path,
            "previewUrl": f"/api/v1/materials/preview/{file_id}",
            "status": metadata.get('status', 'active')
        }
        
        # 如果是音乐或模板，添加特定信息
        if metadata.get('materialType') == 'music':
            preview_info["genre"] = metadata.get('genre', '')
            preview_info["mood"] = metadata.get('mood', '')
            preview_info["duration"] = metadata.get('duration', 0)
        elif metadata.get('materialType') == 'template':
            preview_info["templateType"] = metadata.get('templateType', '')
        
        return preview_info
    
    def delete_material(self, file_id: str) -> Dict[str, Any]:
        """
        删除素材
        
        Args:
            file_id: 素材 ID
            
        Returns:
            删除结果
        """
        # 查找并删除元数据文件
        meta_files = [
            os.path.join(self.base_dir, "music", f"{file_id}.json"),
            os.path.join(self.base_dir, "templates", f"{file_id}.json"),
            os.path.join(self.base_dir, "uploads", f"{file_id}.json"),
        ]
        
        metadata = None
        for meta_path in meta_files:
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    os.remove(meta_path)
                    break
                except:
                    pass
        
        # 删除实际文件
        if metadata and 'filePath' in metadata:
            file_path = metadata['filePath']
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return {"success": True, "message": f"素材 {file_id} 已删除"}
    
    def get_material_stats(self) -> Dict[str, Any]:
        """获取素材统计信息"""
        music_dir = os.path.join(self.base_dir, "music")
        template_dir = os.path.join(self.base_dir, "templates")
        upload_dir = os.path.join(self.base_dir, "uploads")
        
        music_count = len([f for f in os.listdir(music_dir) if f.endswith('.json')]) if os.path.exists(music_dir) else 0
        template_count = len([f for f in os.listdir(template_dir) if f.endswith('.json')]) if os.path.exists(template_dir) else 0
        
        # 计算上传文件总数和总大小
        upload_count = 0
        total_size = 0
        if os.path.exists(upload_dir):
            for f in os.listdir(upload_dir):
                if not f.endswith('.json'):
                    upload_count += 1
                    total_size += os.path.getsize(os.path.join(upload_dir, f))
        
        return {
            "totalMusic": music_count,
            "totalTemplates": template_count,
            "totalUploads": upload_count,
            "totalStorageBytes": total_size,
            "totalStorageMB": round(total_size / (1024 * 1024), 2)
        }
