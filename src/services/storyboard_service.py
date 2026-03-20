"""
分镜设计服务
将 AI 剧本转换为分镜 JSON，并生成 AI 绘画提示词
"""
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import hashlib


class StoryboardService:
    """分镜设计服务"""
    
    def __init__(self, file_service=None):
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storyboards")
        self.file_service = file_service
        
        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 镜头类型
        self.shot_types = ["wide", "closeup", "medium", "extreme"]
        
        # 默认镜头时长（秒）
        self.default_shot_duration = {
            "wide": 5,
            "closeup": 3,
            "medium": 4,
            "extreme": 2
        }
    
    def _generate_storyboard_id(self, script_id: str) -> str:
        """生成分镜 ID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        unique_str = f"{script_id}-{timestamp}-{uuid.uuid4()}"
        return f"storyboard-{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"
    
    def _generate_shot_id(self, scene_id: str, shot_index: int) -> str:
        """生成镜头 ID"""
        return f"SHOT-{shot_index:03d}"
    
    def _generate_scene_id(self, script_id: str, scene_index: int) -> str:
        """生成场景 ID"""
        # 从 script_id 提取剧集信息，如 script-S01E01-xxx
        if "S" in script_id and "E" in script_id:
            parts = script_id.split("-")
            for part in parts:
                if part.startswith("S") and "E" in part:
                    return f"{part}-{scene_index:03d}"
        return f"S01E01-{scene_index:03d}"
    
    async def generate_storyboard(self, script_id: str, script_content: str = None, 
                                  title: str = None) -> Dict[str, Any]:
        """
        将剧本转换为分镜 JSON
        
        Args:
            script_id: 剧本 ID
            script_content: 剧本内容（可选，如果为 None 则从文件读取）
            title: 标题（可选）
            
        Returns:
            分镜 JSON 数据
            
        Raises:
            ValueError: 参数错误
            FileNotFoundError: 剧本文件不存在
        """
        if not script_id:
            raise ValueError("剧本 ID 不能为空")
        
        # 如果没有提供剧本内容，尝试从文件读取
        if not script_content:
            script_path = os.path.join(self.base_dir, "scripts", f"{script_id}.json")
            if not os.path.exists(script_path):
                # 尝试从 uploads 目录读取
                script_path = os.path.join(os.path.dirname(self.base_dir), "uploads", "scripts", f"{script_id}.json")
            
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"剧本文件不存在：{script_id}")
            
            with open(script_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
                script_content = script_data.get("content", "")
                if not title:
                    title = script_data.get("title", "未命名剧本")
        
        # 生成分镜 ID
        storyboard_id = self._generate_storyboard_id(script_id)
        
        # 使用 GPT API 将剧本转换为分镜（模拟实现）
        # 实际实现中需要调用 GPT API
        scenes = await self._convert_script_to_scenes(script_content, script_id)
        
        # 构建分镜数据
        storyboard = {
            "storyboardId": storyboard_id,
            "scriptId": script_id,
            "title": title or "未命名剧本",
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "scenes": scenes
        }
        
        # 为每个镜头生成 AI 绘画提示词
        storyboard = await self.generate_shot_prompts(storyboard)
        
        # 保存到文件
        await self._save_storyboard(storyboard)
        
        return storyboard
    
    async def _convert_script_to_scenes(self, script_content: str, script_id: str) -> List[Dict[str, Any]]:
        """
        将剧本内容转换为场景列表
        
        实际实现中应调用 GPT API 进行智能转换
        这里提供一个基础实现作为示例
        
        Args:
            script_content: 剧本内容
            script_id: 剧本 ID
            
        Returns:
            场景列表
        """
        # TODO: 实际实现中调用 GPT API
        # 这里提供一个示例结构
        
        scenes = []
        
        # 简单按段落分割（示例逻辑）
        paragraphs = [p.strip() for p in script_content.split('\n\n') if p.strip()]
        
        scene_index = 1
        for i, paragraph in enumerate(paragraphs[:5]):  # 限制最多 5 个场景
            scene_id = self._generate_scene_id(script_id, scene_index)
            
            # 根据段落内容智能分配镜头类型（示例逻辑）
            shots = []
            
            # 添加一个广角镜头
            shots.append({
                "shotId": self._generate_shot_id(scene_id, len(shots) + 1),
                "type": "wide",
                "description": f"场景{i+1}：{paragraph[:50]}..." if len(paragraph) > 50 else f"场景{i+1}：{paragraph}",
                "duration": self.default_shot_duration["wide"]
            })
            
            # 添加一个中景镜头
            shots.append({
                "shotId": self._generate_shot_id(scene_id, len(shots) + 1),
                "type": "medium",
                "description": f"中景镜头：{paragraph[:30]}..." if len(paragraph) > 30 else paragraph,
                "duration": self.default_shot_duration["medium"]
            })
            
            # 添加一个特写镜头
            shots.append({
                "shotId": self._generate_shot_id(scene_id, len(shots) + 1),
                "type": "closeup",
                "description": f"特写镜头：关键细节",
                "duration": self.default_shot_duration["closeup"]
            })
            
            scenes.append({
                "sceneId": scene_id,
                "shots": shots
            })
            
            scene_index += 1
        
        return scenes
    
    async def generate_shot_prompts(self, storyboard: Dict[str, Any]) -> Dict[str, Any]:
        """
        为每个镜头生成 AI 绘画提示词（英文）
        
        Args:
            storyboard: 分镜数据
            
        Returns:
            包含提示词的分镜数据
        """
        for scene in storyboard.get("scenes", []):
            for shot in scene.get("shots", []):
                if "prompt" not in shot:
                    shot["prompt"] = await self._generate_prompt_for_shot(shot)
        
        return storyboard
    
    async def _generate_prompt_for_shot(self, shot: Dict[str, Any]) -> str:
        """
        为单个镜头生成 AI 绘画提示词
        
        实际实现中应调用 GPT API 生成高质量的英文提示词
        这里提供基础实现作为示例
        
        Args:
            shot: 镜头数据
            
        Returns:
            英文提示词
        """
        # TODO: 实际实现中调用 GPT API
        shot_type = shot.get("type", "medium")
        description = shot.get("description", "")
        
        # 根据镜头类型添加提示词前缀
        type_prompts = {
            "wide": "Wide angle shot, ",
            "closeup": "Closeup shot, detailed, ",
            "medium": "Medium shot, ",
            "extreme": "Extreme closeup, macro, "
        }
        
        # 基础提示词模板
        base_prompt = type_prompts.get(shot_type, "")
        
        # 简单翻译（示例逻辑，实际应调用翻译 API 或 GPT）
        # 这里只是简单示例
        prompt = f"{base_prompt}Cinematic scene, {description}, professional lighting, 4k, high quality"
        
        return prompt
    
    async def _save_storyboard(self, storyboard: Dict[str, Any]) -> str:
        """
        保存分镜到文件
        
        Args:
            storyboard: 分镜数据
            
        Returns:
            保存路径
        """
        storyboard_id = storyboard.get("storyboardId")
        if not storyboard_id:
            raise ValueError("分镜 ID 不能为空")
        
        # 确保 scripts 目录存在
        scripts_dir = os.path.join(self.base_dir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        
        # 保存路径
        save_path = os.path.join(self.base_dir, f"{storyboard_id}.json")
        
        # 保存到文件
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(storyboard, f, ensure_ascii=False, indent=2)
        
        return save_path
    
    async def get_storyboard(self, storyboard_id: str) -> Dict[str, Any]:
        """
        获取分镜详情
        
        Args:
            storyboard_id: 分镜 ID
            
        Returns:
            分镜数据
            
        Raises:
            FileNotFoundError: 分镜文件不存在
            ValueError: 参数错误
        """
        if not storyboard_id:
            raise ValueError("分镜 ID 不能为空")
        
        # 构建文件路径
        file_path = os.path.join(self.base_dir, f"{storyboard_id}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"分镜文件不存在：{storyboard_id}")
        
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            storyboard = json.load(f)
        
        return storyboard
    
    async def list_storyboards(self, script_id: str = None, page: int = 1, 
                               page_size: int = 20) -> Dict[str, Any]:
        """
        获取分镜列表
        
        Args:
            script_id: 剧本 ID（可选，用于过滤）
            page: 页码
            page_size: 每页数量
            
        Returns:
            分镜列表
        """
        # 获取所有分镜文件
        storyboards = []
        
        if os.path.exists(self.base_dir):
            for filename in os.listdir(self.base_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.base_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            storyboard = json.load(f)
                            
                            # 如果指定了 script_id，进行过滤
                            if script_id and storyboard.get("scriptId") != script_id:
                                continue
                            
                            # 只返回基本信息
                            storyboards.append({
                                "storyboardId": storyboard.get("storyboardId"),
                                "scriptId": storyboard.get("scriptId"),
                                "title": storyboard.get("title"),
                                "createdAt": storyboard.get("createdAt"),
                                "sceneCount": len(storyboard.get("scenes", []))
                            })
                    except Exception:
                        continue
        
        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = storyboards[start_idx:end_idx]
        
        return {
            "total": len(storyboards),
            "page": page,
            "pageSize": page_size,
            "storyboards": paginated
        }
    
    async def delete_storyboard(self, storyboard_id: str) -> bool:
        """
        删除分镜
        
        Args:
            storyboard_id: 分镜 ID
            
        Returns:
            是否删除成功
        """
        file_path = os.path.join(self.base_dir, f"{storyboard_id}.json")
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        
        return False
