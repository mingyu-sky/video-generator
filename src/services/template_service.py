"""
模板管理服务
用于创建、管理和应用视频生成模板
"""
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import hashlib


class TemplateService:
    """模板管理服务"""
    
    def __init__(self, file_service=None):
        self.file_service = file_service
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
        
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "public"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "private"), exist_ok=True)
    
    def _generate_template_id(self, name: str) -> str:
        """生成模板 ID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        unique_str = f"{name}-{timestamp}-{uuid.uuid4()}"
        return f"tmpl-{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"
    
    def _get_template_path(self, template_id: str, is_public: bool) -> str:
        """获取模板文件路径"""
        subdir = "public" if is_public else "private"
        return os.path.join(self.base_dir, subdir, f"{template_id}.json")
    
    def create_template(self, name: str, description: str, steps: List[Dict[str, Any]], 
                       is_public: bool = False) -> Dict[str, Any]:
        """
        创建模板
        
        Args:
            name: 模板名称
            description: 模板描述
            steps: 模板步骤列表，每个步骤包含：
                   - stepType: 步骤类型 (script/storyboard/audio/video/etc)
                   - config: 步骤配置参数
                   - order: 步骤顺序
            is_public: 是否公开
            
        Returns:
            创建的模板数据
            
        Raises:
            ValueError: 参数错误
        """
        if not name or not name.strip():
            raise ValueError("模板名称不能为空")
        
        if not steps or not isinstance(steps, list) or len(steps) == 0:
            raise ValueError("模板步骤不能为空")
        
        # 验证步骤结构
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f"步骤 {i+1} 必须是对象")
            if "stepType" not in step:
                raise ValueError(f"步骤 {i+1} 缺少 stepType 字段")
        
        template_id = self._generate_template_id(name)
        created_at = datetime.now(timezone.utc).isoformat()
        
        template = {
            "templateId": template_id,
            "name": name.strip(),
            "description": description.strip() if description else "",
            "steps": steps,
            "isPublic": is_public,
            "createdAt": created_at,
            "updatedAt": created_at,
            "version": "1.0.0"
        }
        
        # 保存模板到文件
        template_path = self._get_template_path(template_id, is_public)
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        return template
    
    def get_templates(self, page: int = 1, page_size: int = 20, 
                     is_public: Optional[bool] = None) -> Dict[str, Any]:
        """
        获取模板列表
        
        Args:
            page: 页码（从 1 开始）
            page_size: 每页数量
            is_public: 筛选公开/私有模板，None 表示全部
            
        Returns:
            模板列表和分页信息
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 1
        if page_size > 100:
            page_size = 100
        
        all_templates = []
        
        # 读取公开模板
        if is_public is None or is_public is True:
            public_dir = os.path.join(self.base_dir, "public")
            if os.path.exists(public_dir):
                for filename in os.listdir(public_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(public_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                template = json.load(f)
                                # 只返回基本信息，不返回详细步骤
                                all_templates.append({
                                    "templateId": template.get("templateId"),
                                    "name": template.get("name"),
                                    "description": template.get("description"),
                                    "isPublic": template.get("isPublic", True),
                                    "createdAt": template.get("createdAt"),
                                    "updatedAt": template.get("updatedAt"),
                                    "version": template.get("version"),
                                    "stepCount": len(template.get("steps", []))
                                })
                        except Exception:
                            continue
        
        # 读取私有模板
        if is_public is None or is_public is False:
            private_dir = os.path.join(self.base_dir, "private")
            if os.path.exists(private_dir):
                for filename in os.listdir(private_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(private_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                template = json.load(f)
                                all_templates.append({
                                    "templateId": template.get("templateId"),
                                    "name": template.get("name"),
                                    "description": template.get("description"),
                                    "isPublic": template.get("isPublic", False),
                                    "createdAt": template.get("createdAt"),
                                    "updatedAt": template.get("updatedAt"),
                                    "version": template.get("version"),
                                    "stepCount": len(template.get("steps", []))
                                })
                        except Exception:
                            continue
        
        # 按创建时间排序（最新的在前）
        all_templates.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        
        # 分页
        total = len(all_templates)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        templates = all_templates[start_idx:end_idx]
        
        return {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": (total + page_size - 1) // page_size,
            "templates": templates
        }
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """
        获取模板详情
        
        Args:
            template_id: 模板 ID
            
        Returns:
            模板完整数据
            
        Raises:
            ValueError: 模板 ID 为空
            FileNotFoundError: 模板不存在
        """
        if not template_id:
            raise ValueError("模板 ID 不能为空")
        
        # 先在公开目录查找
        public_path = self._get_template_path(template_id, True)
        if os.path.exists(public_path):
            with open(public_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 再在私有目录查找
        private_path = self._get_template_path(template_id, False)
        if os.path.exists(private_path):
            with open(private_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        raise FileNotFoundError(f"模板不存在：{template_id}")
    
    def delete_template(self, template_id: str) -> bool:
        """
        删除模板
        
        Args:
            template_id: 模板 ID
            
        Returns:
            是否删除成功
            
        Raises:
            ValueError: 模板 ID 为空
            FileNotFoundError: 模板不存在
        """
        if not template_id:
            raise ValueError("模板 ID 不能为空")
        
        # 尝试删除公开模板
        public_path = self._get_template_path(template_id, True)
        if os.path.exists(public_path):
            os.remove(public_path)
            return True
        
        # 尝试删除私有模板
        private_path = self._get_template_path(template_id, False)
        if os.path.exists(private_path):
            os.remove(private_path)
            return True
        
        raise FileNotFoundError(f"模板不存在：{template_id}")
    
    def apply_template(self, template_id: str, video_id: str = None) -> Dict[str, Any]:
        """
        应用模板到视频生成任务
        
        Args:
            template_id: 模板 ID
            video_id: 视频 ID（可选，用于关联现有视频）
            
        Returns:
            应用结果，包含生成的任务配置
            
        Raises:
            ValueError: 参数错误
            FileNotFoundError: 模板不存在
        """
        if not template_id:
            raise ValueError("模板 ID 不能为空")
        
        # 获取模板详情
        template = self.get_template(template_id)
        
        # 生成应用记录 ID
        apply_id = f"apply-{uuid.uuid4().hex[:12]}"
        applied_at = datetime.now(timezone.utc).isoformat()
        
        # 构建任务配置
        task_config = {
            "applyId": apply_id,
            "templateId": template_id,
            "templateName": template.get("name"),
            "videoId": video_id,
            "appliedAt": applied_at,
            "steps": template.get("steps", []),
            "status": "ready",
            "currentStep": 0
        }
        
        # 保存应用记录
        records_dir = os.path.join(self.base_dir, "records")
        os.makedirs(records_dir, exist_ok=True)
        record_path = os.path.join(records_dir, f"{apply_id}.json")
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(task_config, f, ensure_ascii=False, indent=2)
        
        return task_config
    
    def update_template(self, template_id: str, name: str = None, 
                       description: str = None, steps: List[Dict[str, Any]] = None,
                       is_public: bool = None) -> Dict[str, Any]:
        """
        更新模板
        
        Args:
            template_id: 模板 ID
            name: 新名称（可选）
            description: 新描述（可选）
            steps: 新步骤（可选）
            is_public: 新的公开状态（可选）
            
        Returns:
            更新后的模板数据
            
        Raises:
            ValueError: 参数错误
            FileNotFoundError: 模板不存在
        """
        if not template_id:
            raise ValueError("模板 ID 不能为空")
        
        # 获取现有模板
        template = self.get_template(template_id)
        old_is_public = template.get("isPublic", False)
        
        # 更新字段
        if name is not None:
            if not name.strip():
                raise ValueError("模板名称不能为空")
            template["name"] = name.strip()
        
        if description is not None:
            template["description"] = description.strip() if description else ""
        
        if steps is not None:
            if not steps or not isinstance(steps, list) or len(steps) == 0:
                raise ValueError("模板步骤不能为空")
            
            # 验证步骤结构
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    raise ValueError(f"步骤 {i+1} 必须是对象")
                if "stepType" not in step:
                    raise ValueError(f"步骤 {i+1} 缺少 stepType 字段")
            
            template["steps"] = steps
        
        if is_public is not None:
            template["isPublic"] = is_public
        
        template["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # 如果公开状态改变，需要移动文件
        if is_public is not None and is_public != old_is_public:
            old_path = self._get_template_path(template_id, old_is_public)
            new_path = self._get_template_path(template_id, is_public)
            
            if os.path.exists(old_path):
                os.remove(old_path)
            
            with open(new_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
        else:
            # 保存更新
            template_path = self._get_template_path(template_id, old_is_public)
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
        
        return template
