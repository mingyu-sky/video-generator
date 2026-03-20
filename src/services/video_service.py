"""
视频处理服务
使用 MoviePy + FFmpeg 进行视频处理
支持：拼接、文字特效、图片水印、背景音乐、配音、转场、字幕等
"""
import os
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import uuid
import subprocess
import json

# MoviePy 导入
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, ImageClip, TextClip, CompositeVideoClip,
        CompositeAudioClip, concatenate_videoclips, concatenate_audioclips
    )
    from moviepy.video.fx.all import fadein, fadeout
    from moviepy.audio.fx.all import audio_fadein, audio_fadeout
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


class VideoService:
    """视频处理服务"""
    
    def __init__(self, file_service=None, task_service=None):
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
        self.output_dir = os.path.join(self.base_dir, "outputs")
        self.temp_dir = os.path.join(self.base_dir, "temp")
        
        # 确保目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 服务引用
        self.file_service = file_service
        self.task_service = task_service
        
        # 转场效果映射
        self.transitions = {
            "fade": self._apply_fade_transition,
            "dissolve": self._apply_dissolve_transition,
            "wipe": self._apply_wipe_transition,
            "slide": self._apply_slide_transition
        }
    
    async def concat_videos(self, video_ids: List[str], output_name: str = None,
                           transition: str = "none") -> Dict[str, Any]:
        """
        视频拼接
        
        Args:
            video_ids: 视频文件 ID 列表
            output_name: 输出文件名
            transition: 转场效果 (none/fade/dissolve)
            
        Returns:
            处理结果
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("MoviePy 未安装，请运行：pip install moviepy")
        
        if len(video_ids) < 2:
            raise ValueError("至少需要 2 个视频进行拼接")
        
        # 获取视频文件路径
        video_paths = []
        for video_id in video_ids:
            if self.file_service:
                path = await self.file_service.get_file_path(video_id)
                if not path:
                    raise ValueError(f"视频文件不存在：{video_id}")
                video_paths.append(path)
            else:
                video_paths.append(video_id)  # 直接使用路径
        
        # 生成输出文件名
        if not output_name:
            output_name = f"concat_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(self.output_dir, output_name)
        
        # 加载视频片段
        clips = []
        for path in video_paths:
            clip = VideoFileClip(path)
            clips.append(clip)
        
        try:
            # 应用转场效果
            if transition == "none":
                # 简单拼接
                final_clip = concatenate_videoclips(clips, method="compose")
            else:
                # 应用转场
                final_clip = self._concat_with_transition(clips, transition)
            
            # 写入文件
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=clips[0].fps if clips else 30
            )
            
            # 获取输出信息
            output_duration = final_clip.duration
            output_resolution = f"{final_clip.w}x{final_clip.h}"
            
            # 关闭 clips
            for clip in clips:
                clip.close()
            final_clip.close()
            
            return {
                "outputId": str(uuid.uuid4()),
                "fileName": output_name,
                "filePath": output_path,
                "duration": output_duration,
                "resolution": output_resolution
            }
            
        except Exception as e:
            # 清理资源
            for clip in clips:
                clip.close()
            raise RuntimeError(f"视频拼接失败：{str(e)}")
    
    def _concat_with_transition(self, clips: List, transition: str, duration: float = 1.0) -> VideoFileClip:
        """应用转场效果进行拼接"""
        if len(clips) < 2:
            return clips[0] if clips else None
        
        if transition not in self.transitions:
            transition = "fade"
        
        return self.transitions[transition](clips, duration)
    
    def _apply_fade_transition(self, clips: List, duration: float = 1.0) -> VideoFileClip:
        """淡入淡出转场"""
        result_clips = []
        for i, clip in enumerate(clips):
            if i == 0:
                result_clips.append(clip)
            else:
                # 前一个视频淡出
                prev_clip = result_clips[-1]
                prev_clip = prev_clip.fx(fadeout, duration)
                result_clips[-1] = prev_clip
                
                # 当前视频淡入
                clip = clip.fx(fadein, duration)
                result_clips.append(clip)
        
        return concatenate_videoclips(result_clips, method="compose")
    
    def _apply_dissolve_transition(self, clips: List, duration: float = 1.0) -> VideoFileClip:
        """溶解转场"""
        # 简化实现，使用淡入淡出模拟
        return self._apply_fade_transition(clips, duration)
    
    def _apply_wipe_transition(self, clips: List, duration: float = 1.0) -> VideoFileClip:
        """擦除转场"""
        # 简化实现
        return self._apply_fade_transition(clips, duration)
    
    def _apply_slide_transition(self, clips: List, duration: float = 1.0) -> VideoFileClip:
        """滑动转场"""
        # 简化实现
        return self._apply_fade_transition(clips, duration)
    
    async def add_text_overlay(self, video_id: str, text: str, position: Dict[str, int],
                               style: Dict[str, Any], duration: Dict[str, float],
                               output_name: str = None) -> Dict[str, Any]:
        """
        添加文字特效
        
        Args:
            video_id: 视频文件 ID
            text: 文字内容
            position: 位置 {"x": 100, "y": 200}
            style: 样式 {"fontSize": 24, "fontFamily": "Arial", "color": "#FFFFFF", ...}
            duration: 时长 {"start": 0, "end": 5}
            output_name: 输出文件名
            
        Returns:
            处理结果
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("MoviePy 未安装")
        
        # 获取视频路径
        if self.file_service:
            video_path = await self.file_service.get_file_path(video_id)
            if not video_path:
                raise ValueError(f"视频文件不存在：{video_id}")
        else:
            video_path = video_id
        
        # 加载视频
        video = VideoFileClip(video_path)
        
        # 验证时间范围
        start_time = duration.get("start", 0)
        end_time = duration.get("end", video.duration)
        if end_time < 0:
            end_time = video.duration
        if start_time < 0 or end_time > video.duration:
            video.close()
            raise ValueError(f"时间范围超出视频长度 (0-{video.duration:.1f}秒)")
        
        # 创建文字片段
        font_size = style.get("fontSize", 24)
        font_family = style.get("fontFamily", "Arial")
        color = style.get("color", "#FFFFFF")
        stroke_color = style.get("strokeColor", "#000000")
        stroke_width = style.get("strokeWidth", 1)
        
        try:
            txt_clip = TextClip(
                text=text,
                fontsize=font_size,
                font=font_family,
                color=color,
                stroke_color=stroke_color,
                stroke_width=stroke_width
            )
        except Exception as e:
            # 如果指定字体不可用，使用默认字体
            txt_clip = TextClip(
                text=text,
                fontsize=font_size,
                color=color,
                stroke_color=stroke_color,
                stroke_width=stroke_width
            )
        
        # 设置位置和时长
        pos_x = position.get("x", 100)
        pos_y = position.get("y", 200)
        txt_clip = txt_clip.set_position((pos_x, pos_y))
        txt_clip = txt_clip.set_start(start_time).set_end(end_time)
        
        # 合成视频
        final_video = CompositeVideoClip([video, txt_clip])
        
        # 生成输出文件名
        if not output_name:
            output_name = f"text_overlay_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(self.output_dir, output_name)
        
        try:
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=video.fps
            )
            
            result = {
                "outputId": str(uuid.uuid4()),
                "fileName": output_name,
                "filePath": output_path,
                "duration": final_video.duration
            }
            
        finally:
            video.close()
            txt_clip.close()
            final_video.close()
        
        return result
    
    async def add_image_overlay(self, video_id: str, image_id: str, position: Dict[str, int],
                                opacity: float = 1.0, duration: Dict[str, float] = None,
                                output_name: str = None) -> Dict[str, Any]:
        """
        添加图片/动图水印
        
        Args:
            video_id: 视频文件 ID
            image_id: 图片文件 ID
            position: 位置 {"x": 50, "y": 50}
            opacity: 透明度 (0.0-1.0)
            duration: 时长 {"start": 0, "end": -1}
            output_name: 输出文件名
            
        Returns:
            处理结果
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("MoviePy 未安装")
        
        # 获取文件路径
        if self.file_service:
            video_path = await self.file_service.get_file_path(video_id)
            image_path = await self.file_service.get_file_path(image_id)
            if not video_path:
                raise ValueError(f"视频文件不存在：{video_id}")
            if not image_path:
                raise ValueError(f"图片文件不存在：{image_id}")
        else:
            video_path = video_id
            image_path = image_id
        
        # 加载视频和图片
        video = VideoFileClip(video_path)
        image = ImageClip(image_path)
        
        # 设置透明度
        if opacity < 1.0:
            image = image.set_opacity(opacity)
        
        # 设置位置
        pos_x = position.get("x", 50)
        pos_y = position.get("y", 50)
        image = image.set_position((pos_x, pos_y))
        
        # 设置时长
        if duration:
            start_time = duration.get("start", 0)
            end_time = duration.get("end", -1)
            if end_time < 0:
                end_time = video.duration
            image = image.set_start(start_time).set_end(end_time)
        else:
            image = image.set_start(0).set_duration(video.duration)
        
        # 合成视频
        final_video = CompositeVideoClip([video, image])
        
        # 生成输出文件名
        if not output_name:
            output_name = f"image_overlay_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(self.output_dir, output_name)
        
        try:
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=video.fps
            )
            
            result = {
                "outputId": str(uuid.uuid4()),
                "fileName": output_name,
                "filePath": output_path,
                "duration": final_video.duration
            }
            
        finally:
            video.close()
            image.close()
            final_video.close()
        
        return result
    
    async def add_background_music(self, video_id: str, music_id: str,
                                   start_time: float = 0, end_time: float = -1,
                                   volume: float = 0.3, fade: Dict[str, float] = None,
                                   loop: bool = True, output_name: str = None) -> Dict[str, Any]:
        """
        添加背景音乐
        
        Args:
            video_id: 视频文件 ID
            music_id: 音频文件 ID
            start_time: 从视频的第几秒开始播放
            end_time: 结束时间 (-1 表示直到视频结束)
            volume: 音量 (0.0-1.0)
            fade: 淡入淡出 {"in": 2.0, "out": 2.0}
            loop: 是否循环
            output_name: 输出文件名
            
        Returns:
            处理结果
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("MoviePy 未安装")
        
        # 获取文件路径
        if self.file_service:
            video_path = await self.file_service.get_file_path(video_id)
            music_path = await self.file_service.get_file_path(music_id)
            if not video_path:
                raise ValueError(f"视频文件不存在：{video_id}")
            if not music_path:
                raise ValueError(f"音频文件不存在：{music_id}")
        else:
            video_path = video_id
            music_path = music_id
        
        # 加载视频和音频
        video = VideoFileClip(video_path)
        music = AudioFileClip(music_path)
        
        # 调整音量
        music = music.volumex(volume)
        
        # 应用淡入淡出
        if fade:
            fade_in = fade.get("in", 0)
            fade_out = fade.get("out", 0)
            if fade_in > 0:
                music = music.fx(audio_fadein, fade_in)
            if fade_out > 0:
                music = music.fx(audio_fadeout, fade_out)
        
        # 处理音频时长
        video_duration = video.duration
        if end_time < 0:
            end_time = video_duration
        
        audio_duration = end_time - start_time
        
        if loop and music.duration < audio_duration:
            # 循环音频
            loops_needed = int(audio_duration / music.duration) + 1
            music_clips = [music] * loops_needed
            music = concatenate_audioclips(music_clips)
        
        # 裁剪音频到指定时长
        music = music.subclip(0, audio_duration)
        
        # 设置音频开始时间
        music = music.set_start(start_time)
        
        # 混合音频
        if video.audio:
            final_audio = CompositeAudioClip([video.audio, music])
        else:
            final_audio = music
        
        final_video = video.set_audio(final_audio)
        
        # 生成输出文件名
        if not output_name:
            output_name = f"bgm_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(self.output_dir, output_name)
        
        try:
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=video.fps
            )
            
            result = {
                "outputId": str(uuid.uuid4()),
                "fileName": output_name,
                "filePath": output_path,
                "duration": final_video.duration
            }
            
        finally:
            video.close()
            music.close()
            final_video.close()
        
        return result
    
    async def add_voiceover(self, video_id: str, voiceover_id: str,
                           align_mode: str = "start", start_time: float = 0,
                           volume: float = 0.8, output_name: str = None) -> Dict[str, Any]:
        """
        添加配音
        
        Args:
            video_id: 视频文件 ID
            voiceover_id: 配音音频文件 ID
            align_mode: 对齐模式 (start/center/end/custom)
            start_time: 自定义开始时间
            volume: 音量 (0.0-1.0)
            output_name: 输出文件名
            
        Returns:
            处理结果
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("MoviePy 未安装")
        
        # 获取文件路径
        if self.file_service:
            video_path = await self.file_service.get_file_path(video_id)
            voiceover_path = await self.file_service.get_file_path(voiceover_id)
            if not video_path:
                raise ValueError(f"视频文件不存在：{video_id}")
            if not voiceover_path:
                raise ValueError(f"配音文件不存在：{voiceover_id}")
        else:
            video_path = video_id
            voiceover_path = voiceover_id
        
        # 加载视频和音频
        video = VideoFileClip(video_path)
        voiceover = AudioFileClip(voiceover_path)
        
        # 调整音量
        voiceover = voiceover.volumex(volume)
        
        # 计算开始时间
        video_duration = video.duration
        audio_duration = voiceover.duration
        
        if align_mode == "start":
            actual_start = 0
        elif align_mode == "center":
            actual_start = (video_duration - audio_duration) / 2
        elif align_mode == "end":
            actual_start = video_duration - audio_duration
        elif align_mode == "custom":
            actual_start = start_time
        else:
            actual_start = 0
        
        # 确保开始时间非负
        actual_start = max(0, actual_start)
        
        # 设置音频开始时间
        voiceover = voiceover.set_start(actual_start)
        
        # 混合音频
        if video.audio:
            final_audio = CompositeAudioClip([video.audio, voiceover])
        else:
            final_audio = voiceover
        
        final_video = video.set_audio(final_audio)
        
        # 生成输出文件名
        if not output_name:
            output_name = f"voiceover_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(self.output_dir, output_name)
        
        try:
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=video.fps
            )
            
            result = {
                "outputId": str(uuid.uuid4()),
                "fileName": output_name,
                "filePath": output_path,
                "duration": final_video.duration
            }
            
        finally:
            video.close()
            voiceover.close()
            final_video.close()
        
        return result
    
    async def add_transition(self, video_ids: List[str], transition: str,
                            duration: float = 1.0, output_name: str = None) -> Dict[str, Any]:
        """
        添加转场特效
        
        Args:
            video_ids: 视频文件 ID 列表
            transition: 转场类型 (fade/dissolve/wipe/slide)
            duration: 转场时长 (秒)
            output_name: 输出文件名
            
        Returns:
            处理结果
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("MoviePy 未安装")
        
        if len(video_ids) < 2:
            raise ValueError("至少需要 2 个视频")
        
        if transition not in self.transitions:
            raise ValueError(f"不支持的转场效果：{transition}")
        
        # 获取视频文件路径
        video_paths = []
        for video_id in video_ids:
            if self.file_service:
                path = await self.file_service.get_file_path(video_id)
                if not path:
                    raise ValueError(f"视频文件不存在：{video_id}")
                video_paths.append(path)
            else:
                video_paths.append(video_id)
        
        # 加载视频片段
        clips = []
        for path in video_paths:
            clip = VideoFileClip(path)
            clips.append(clip)
        
        try:
            # 应用转场
            final_clip = self._concat_with_transition(clips, transition, duration)
            
            # 生成输出文件名
            if not output_name:
                output_name = f"transition_{uuid.uuid4().hex[:8]}.mp4"
            output_path = os.path.join(self.output_dir, output_name)
            
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=clips[0].fps if clips else 30
            )
            
            result = {
                "outputId": str(uuid.uuid4()),
                "fileName": output_name,
                "filePath": output_path,
                "duration": final_clip.duration
            }
            
        finally:
            for clip in clips:
                clip.close()
            final_clip.close()
        
        return result
    
    async def add_subtitles(self, video_id: str, subtitle_id: str,
                           offset: float = 0, style: Dict[str, Any] = None,
                           output_name: str = None) -> Dict[str, Any]:
        """
        添加字幕
        
        Args:
            video_id: 视频文件 ID
            subtitle_id: SRT 字幕文件 ID
            offset: 时间偏移 (秒)
            style: 样式 {"fontSize": 20, "fontFamily": "思源黑体", "color": "#FFFFFF", ...}
            output_name: 输出文件名
            
        Returns:
            处理结果
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("MoviePy 未安装")
        
        # 获取文件路径
        if self.file_service:
            video_path = await self.file_service.get_file_path(video_id)
            subtitle_path = await self.file_service.get_file_path(subtitle_id)
            if not video_path:
                raise ValueError(f"视频文件不存在：{video_id}")
            if not subtitle_path:
                raise ValueError(f"字幕文件不存在：{subtitle_id}")
        else:
            video_path = video_id
            subtitle_path = subtitle_id
        
        # 加载视频
        video = VideoFileClip(video_path)
        
        # 解析 SRT 文件
        subtitles = self._parse_srt(subtitle_path, offset)
        
        # 创建字幕片段列表
        subtitle_clips = []
        
        # 样式默认值
        default_style = {
            "fontSize": 20,
            "fontFamily": "Arial",
            "color": "#FFFFFF",
            "strokeColor": "#000000",
            "strokeWidth": 1,
            "position": "bottom",
            "offsetY": -50
        }
        if style:
            default_style.update(style)
        
        # 创建每个字幕片段
        for sub in subtitles:
            try:
                txt_clip = TextClip(
                    text=sub["text"],
                    fontsize=default_style["fontSize"],
                    font=default_style["fontFamily"],
                    color=default_style["color"],
                    stroke_color=default_style["strokeColor"],
                    stroke_width=default_style["strokeWidth"]
                )
            except:
                txt_clip = TextClip(
                    text=sub["text"],
                    fontsize=default_style["fontSize"],
                    color=default_style["color"],
                    stroke_color=default_style["strokeColor"],
                    stroke_width=default_style["strokeWidth"]
                )
            
            # 设置位置
            if default_style["position"] == "bottom":
                txt_clip = txt_clip.set_position(("center", default_style.get("offsetY", -50)))
            elif default_style["position"] == "top":
                txt_clip = txt_clip.set_position(("center", 50))
            else:
                txt_clip = txt_clip.set_position(("center", "center"))
            
            # 设置时长
            txt_clip = txt_clip.set_start(sub["start"]).set_end(sub["end"])
            subtitle_clips.append(txt_clip)
        
        # 合成视频
        final_video = CompositeVideoClip([video] + subtitle_clips)
        
        # 生成输出文件名
        if not output_name:
            output_name = f"subtitles_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(self.output_dir, output_name)
        
        try:
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=video.fps
            )
            
            result = {
                "outputId": str(uuid.uuid4()),
                "fileName": output_name,
                "filePath": output_path,
                "duration": final_video.duration
            }
            
        finally:
            video.close()
            for clip in subtitle_clips:
                clip.close()
            final_video.close()
        
        return result
    
    def _parse_srt(self, srt_path: str, offset: float = 0) -> List[Dict[str, Any]]:
        """解析 SRT 字幕文件"""
        subtitles = []
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割字幕块
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            # 解析时间轴
            time_line = lines[1]
            match = self._parse_time_line(time_line)
            if not match:
                continue
            
            start_time = match["start"] + offset
            end_time = match["end"] + offset
            
            # 确保时间非负
            start_time = max(0, start_time)
            end_time = max(start_time + 0.1, end_time)
            
            # 获取字幕文本（可能有多行）
            text = '\n'.join(lines[2:])
            
            subtitles.append({
                "start": start_time,
                "end": end_time,
                "text": text
            })
        
        return subtitles
    
    def _parse_time_line(self, time_line: str) -> Optional[Dict[str, float]]:
        """解析 SRT 时间轴行"""
        # 格式：00:00:00,000 --> 00:00:02,000
        try:
            parts = time_line.split(' --> ')
            if len(parts) != 2:
                return None
            
            start = self._parse_timestamp(parts[0].strip())
            end = self._parse_timestamp(parts[1].strip())
            
            if start is None or end is None:
                return None
            
            return {"start": start, "end": end}
        except:
            return None
    
    def _parse_timestamp(self, timestamp: str) -> Optional[float]:
        """解析时间戳为秒数"""
        try:
            # 处理 SRT 格式：00:00:00,000
            timestamp = timestamp.replace(',', '.')
            parts = timestamp.split(':')
            if len(parts) != 3:
                return None
            
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            
            return hours * 3600 + minutes * 60 + seconds
        except:
            return None
    
    async def process_pipeline(self, video_id: str, steps: List[Dict[str, Any]],
                               output_name: str = None) -> Dict[str, Any]:
        """
        一站式处理（流水线）
        
        Args:
            video_id: 视频文件 ID
            steps: 处理步骤列表
            output_name: 输出文件名
            
        Returns:
            处理结果
        """
        if not steps:
            raise ValueError("处理步骤不能为空")
        
        current_video_id = video_id
        step_results = []
        
        for i, step in enumerate(steps):
            step_type = step.get("type")
            params = step.get("params", {})
            
            # 添加输出文件名后缀
            step_output_name = f"step{i}_{output_name}" if output_name else None
            
            # 执行对应步骤
            if step_type == "add_music":
                result = await self.add_background_music(
                    video_id=current_video_id,
                    music_id=params.get("musicId"),
                    start_time=params.get("startTime", 0),
                    end_time=params.get("endTime", -1),
                    volume=params.get("volume", 0.3),
                    fade=params.get("fade"),
                    loop=params.get("loop", True),
                    output_name=step_output_name
                )
            elif step_type == "add_voiceover":
                result = await self.add_voiceover(
                    video_id=current_video_id,
                    voiceover_id=params.get("voiceoverId"),
                    align_mode=params.get("alignMode", "start"),
                    start_time=params.get("startTime", 0),
                    volume=params.get("volume", 0.8),
                    output_name=step_output_name
                )
            elif step_type == "add_subtitles":
                result = await self.add_subtitles(
                    video_id=current_video_id,
                    subtitle_id=params.get("subtitleId"),
                    offset=params.get("offset", 0),
                    style=params.get("style"),
                    output_name=step_output_name
                )
            elif step_type == "text_overlay":
                result = await self.add_text_overlay(
                    video_id=current_video_id,
                    text=params.get("text"),
                    position=params.get("position", {"x": 100, "y": 200}),
                    style=params.get("style", {}),
                    duration=params.get("duration", {"start": 0, "end": -1}),
                    output_name=step_output_name
                )
            elif step_type == "image_overlay":
                result = await self.add_image_overlay(
                    video_id=current_video_id,
                    image_id=params.get("imageId"),
                    position=params.get("position", {"x": 50, "y": 50}),
                    opacity=params.get("opacity", 1.0),
                    duration=params.get("duration"),
                    output_name=step_output_name
                )
            else:
                raise ValueError(f"不支持的处理步骤：{step_type}")
            
            step_results.append({
                "step": i + 1,
                "type": step_type,
                "outputId": result["outputId"]
            })
            
            # 更新当前视频 ID 为输出文件（用于下一步处理）
            # 注意：这里需要保存临时文件元数据，简化处理直接使用路径
            current_video_id = result["filePath"]
        
        # 最终输出
        final_result = step_results[-1]
        
        return {
            "outputId": final_result["outputId"],
            "fileName": output_name or f"processed_{uuid.uuid4().hex[:8]}.mp4",
            "filePath": current_video_id,
            "totalSteps": len(steps),
            "stepResults": step_results
        }
