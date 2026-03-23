"""
一键视频生成服务
整合特效、模板、任务管理，提供一键生成能力
"""
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from .effect_service import EffectService, TextEffect, FollowEffect, PIPEffect
from moviepy.editor import VideoFileClip, CompositeVideoClip


class OneClickService:
    """一键视频生成服务"""
    
    def __init__(self, file_service=None, task_service=None):
        self.file_service = file_service
        self.task_service = task_service
        self.effect_service = EffectService()
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "oneclick")
        os.makedirs(self.base_dir, exist_ok=True)
    
    def create_generation_task(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建一键生成任务
        
        Args:
            config: 生成配置
                - videoId: 主视频 ID
                - templateId: 模板 ID
                - textEffects: 文字特效配置列表
                - followEffect: 点关注特效配置
                - pipEffect: 画中画特效配置
                - outputName: 输出文件名
                
        Returns:
            任务信息
        """
        task_id = f"oneclick_{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).isoformat()
        
        task = {
            "taskId": task_id,
            "type": "oneclick_generation",
            "status": "pending",
            "config": config,
            "createdAt": created_at,
            "progress": 0
        }
        
        # 如果有关联任务服务，保存任务
        if self.task_service:
            self.task_service.tasks[task_id] = task
        
        return task
    
    def process_oneclick(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理一键生成任务
        
        Args:
            task_id: 任务 ID
            config: 生成配置
            
        Returns:
            处理结果
        """
        # 更新任务状态
        if self.task_service:
            self.task_service.update_task(task_id, {"status": "processing", "progress": 10})
        
        # 获取视频文件
        video_id = config.get('videoId')
        if self.file_service:
            video_path = self.file_service.get_file_path(video_id)
        else:
            video_path = config.get('videoPath')
        
        output_name = config.get('outputName', f"oneclick_{uuid.uuid4().hex[:8]}.mp4")
        output_path = os.path.join(self.base_dir, output_name)
        
        # 加载主视频
        video = VideoFileClip(video_path)
        clips = [video]
        
        # 应用文字特效
        text_effects = config.get('textEffects', [])
        for i, text_config in enumerate(text_effects):
            if self.task_service:
                self.task_service.update_task(task_id, {"progress": 20 + i * 10})
            
            text_clip = TextEffect.create(
                text=text_config.get('text', ''),
                duration=text_config.get('duration', video.duration),
                style=text_config.get('style', {})
            )
            clips.append(text_clip)
        
        # 应用点关注特效
        follow_config = config.get('followEffect')
        if follow_config:
            if self.task_service:
                self.task_service.update_task(task_id, {"progress": 70})
            
            follow_clip = FollowEffect.create(
                duration=follow_config.get('duration', 5.0),
                style=follow_config.get('style', {})
            ).set_start(follow_config.get('startTime', video.duration - 10))
            clips.append(follow_clip)
        
        # 应用画中画特效
        pip_config = config.get('pipEffect')
        if pip_config:
            if self.task_service:
                self.task_service.update_task(task_id, {"progress": 85})
            
            pip_video_path = self.file_service.get_file_path(pip_config.get('pipVideoId')) if self.file_service else pip_config.get('pipVideoPath')
            pip_clip = VideoFileClip(pip_video_path)
            
            pip_result = PIPEffect.create(
                main_clip=video,
                pip_clip=pip_clip,
                layout=pip_config.get('layout', 'bottom-right'),
                style=pip_config.get('style', {})
            )
            clips = [pip_result] + clips[1:]  # 替换主视频
        
        # 合成最终视频
        if self.task_service:
            self.task_service.update_task(task_id, {"progress": 90})
        
        final = CompositeVideoClip(clips)
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        # 清理资源
        video.close()
        final.close()
        
        # 更新任务状态
        if self.task_service:
            self.task_service.update_task(task_id, {
                "status": "completed",
                "progress": 100,
                "result": {
                    "outputPath": output_path,
                    "outputName": output_name
                }
            })
        
        return {
            "taskId": task_id,
            "status": "completed",
            "outputPath": output_path,
            "outputName": output_name
        }
    
    def generate_from_template(self, video_id: str, template_id: str, 
                               params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        从模板生成视频
        
        Args:
            video_id: 视频文件 ID
            template_id: 模板 ID
            params: 自定义参数
            
        Returns:
            生成结果
        """
        # 创建任务
        config = {
            "videoId": video_id,
            "templateId": template_id,
            "textEffects": [],
            "followEffect": None,
            "pipEffect": None,
            "outputName": f"template_{template_id}_{uuid.uuid4().hex[:8]}.mp4"
        }
        
        # 应用模板配置
        # TODO: 从模板服务加载模板配置并应用到 config
        
        # 应用自定义参数
        if params:
            config.update(params)
        
        # 创建并处理任务
        task = self.create_generation_task(config)
        result = self.process_oneclick(task['taskId'], config)
        
        return result


__all__ = ['OneClickService']
