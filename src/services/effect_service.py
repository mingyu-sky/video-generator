"""
特效服务模块
实现文字特效、点关注特效、画中画特效
基于 MoviePy 实现
"""
import os
from typing import Dict, Any, List, Optional, Tuple
from moviepy.editor import (
    VideoFileClip, CompositeVideoClip, TextClip, ImageClip,
    ColorClip, CompositeAudioClip
)
from moviepy.video.fx.all import fadein, fadeout
import numpy as np


class TextEffect:
    """文字特效类"""
    
    # 可用字体列表
    FONTS = ['Arial', 'Arial-Bold', 'Helvetica', 'Times-New-Roman', 'Courier']
    
    # 预设位置
    POSITIONS = {
        'top-left': ('left', 20, 20),
        'top-center': ('center', 0, 20),
        'top-right': ('right', 20, 20),
        'center': ('center', 0, 0),
        'bottom-left': ('left', 20, -20),
        'bottom-center': ('center', 0, -50),
        'bottom-right': ('right', 20, -20),
    }
    
    @classmethod
    def create(cls, text: str, duration: float, style: Optional[Dict[str, Any]] = None) -> TextClip:
        """
        创建文字特效
        
        Args:
            text: 文字内容
            duration: 显示时长（秒）
            style: 样式配置
            
        Returns:
            TextClip 对象
        """
        style = style or {}
        
        # 提取样式参数
        font_size = style.get('fontSize', 36)
        font = style.get('font', 'Arial-Bold')
        color = style.get('color', 'white')
        stroke_color = style.get('strokeColor', 'black')
        stroke_width = style.get('strokeWidth', 1)
        bg_color = style.get('backgroundColor', None)
        bg_padding = style.get('backgroundPadding', 10)
        
        # 创建基础文字（MoviePy TextClip 不支持 duration，用 set_duration）
        txt_clip = TextClip(
            txt=text,
            fontsize=font_size,
            font=font,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width
        ).set_duration(duration)
        
        # 应用特效类型
        effect_type = style.get('effect', 'none')
        if effect_type == 'typewriter':
            txt_clip = cls.typewriter_effect(txt_clip, text)
        elif effect_type == 'flash':
            txt_clip = cls.flash_effect(txt_clip)
        elif effect_type == 'bounce':
            txt_clip = cls.bounce_effect(txt_clip)
        elif effect_type == 'slide':
            txt_clip = cls.slide_effect(txt_clip, style.get('slideDirection', 'left'))
        elif effect_type == 'fade':
            txt_clip = fadein(txt_clip, 0.5)
        
        # 添加背景
        if bg_color:
            txt_clip = cls.add_background(txt_clip, bg_color, bg_padding)
        
        # 设置位置
        position = style.get('position', 'center')
        txt_clip = cls.set_position(txt_clip, position)
        
        return txt_clip
    
    @staticmethod
    def typewriter_effect(clip: TextClip, text: str) -> CompositeVideoClip:
        """打字机效果 - 逐字显示"""
        clips = []
        for i in range(1, len(text) + 1):
            partial_text = text[:i]
            partial_clip = TextClip(
                txt=partial_text,
                fontsize=clip.fontSize,
                font=clip.font,
                color=clip.color,
                stroke_color=clip.stroke_color,
                stroke_width=clip.stroke_width
            ).set_duration(clip.duration / len(text)).set_start(i * clip.duration / len(text))
            clips.append(partial_clip)
        
        return CompositeVideoClip(clips)
    
    @staticmethod
    def flash_effect(clip: TextClip) -> CompositeVideoClip:
        """闪烁效果"""
        flash_duration = 0.3
        num_flashes = int(clip.duration / flash_duration)
        clips = []
        
        for i in range(num_flashes):
            start = i * flash_duration
            visible = i % 2 == 0
            if visible:
                flash_clip = clip.copy().set_start(start).set_duration(flash_duration)
                clips.append(flash_clip)
        
        return CompositeVideoClip(clips) if clips else clip
    
    @staticmethod
    def bounce_effect(clip: TextClip) -> CompositeVideoClip:
        """弹跳效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            if t < 0.5:
                offset = int(20 * np.sin(np.pi * t / 0.5))
                shifted = np.zeros_like(frame)
                h = min(frame.shape[0], offset + frame.shape[0])
                if offset > 0:
                    shifted[offset:h] = frame[:h-offset]
                else:
                    shifted[:h] = frame[-offset:h-offset]
                return shifted
            return frame
        
        return clip.transform(make_frame)
    
    @staticmethod
    def slide_effect(clip: TextClip, direction: str = 'left') -> CompositeVideoClip:
        """滑入效果"""
        return fadein(clip, 0.5)
    
    @classmethod
    def set_position(cls, clip: TextClip, position: str) -> TextClip:
        """设置文字位置"""
        pos_config = cls.POSITIONS.get(position, ('center', 0, 0))
        
        if pos_config[0] == 'center':
            return clip.set_position(('center', pos_config[2]))
        elif pos_config[0] == 'left':
            return clip.set_position((pos_config[1], pos_config[2]))
        elif pos_config[0] == 'right':
            return clip.set_position((pos_config[1], pos_config[2]))
        return clip
    
    @staticmethod
    def add_background(clip: TextClip, color: str, padding: int) -> CompositeVideoClip:
        """添加背景"""
        bg = ColorClip(
            size=(clip.w + padding * 2, clip.h + padding * 2),
            color=tuple(int(color[i:i+2], 16) for i in (1, 3, 5)) if color.startswith('#') else (0, 0, 0)
        ).set_duration(clip.duration).set_opacity(0.7)
        
        return CompositeVideoClip([bg, clip.set_position('center')])


class FollowEffect:
    """点关注特效类"""
    
    @classmethod
    def create(cls, duration: float, style: Optional[Dict[str, Any]] = None) -> CompositeVideoClip:
        """
        创建点关注特效
        
        Args:
            duration: 显示时长（秒）
            style: 样式配置
            
        Returns:
            CompositeVideoClip 对象
        """
        style = style or {}
        
        button_type = style.get('buttonType', 'circle')
        animation = style.get('animation', 'pulse')
        text = style.get('text', '点关注')
        position = style.get('position', 'bottom-right')
        size = style.get('size', 80)
        color = style.get('color', '#FF4500')
        
        # 创建按钮
        button_clip = cls.create_button(size, color, button_type).set_duration(duration)
        
        # 创建文字
        text_clip = TextClip(
            txt=text,
            fontsize=20,
            font='Arial-Bold',
            color='white',
            stroke_color='black',
            stroke_width=1
        ).set_duration(duration)
        
        # 应用动画
        if animation == 'pulse':
            button_clip = cls.pulse_animation(button_clip, duration)
        elif animation == 'popup':
            button_clip = cls.popup_animation(button_clip, duration)
        elif animation == 'fade':
            button_clip = fadein(button_clip, 0.3)
        
        # 组合按钮和文字
        text_clip = text_clip.set_position((button_clip.w // 2, size + 10), relative=True)
        return CompositeVideoClip([button_clip, text_clip])
    
    @staticmethod
    def create_button(size: int, color: str, button_type: str) -> ColorClip:
        """创建关注按钮（简化：使用色块）"""
        # 解析颜色
        if color.startswith('#'):
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        else:
            r, g, b = 255, 69, 0
        
        return ColorClip(size=(size, size), color=(r, g, b))
    
    @staticmethod
    def pulse_animation(clip: VideoFileClip, duration: float) -> VideoFileClip:
        """脉冲动画"""
        def make_frame(t):
            frame = clip.get_frame(t % 1)
            scale = 1 + 0.1 * np.sin(np.pi * (t % 1) * 2)
            return frame
        return clip.transform(make_frame).set_duration(duration)
    
    @staticmethod
    def popup_animation(clip: VideoFileClip, duration: float) -> VideoFileClip:
        """弹出动画"""
        return fadein(clip, 0.3).set_duration(duration)


class PIPEffect:
    """画中画特效类"""
    
    # 预设布局
    LAYOUTS = {
        'bottom-right': {'pos': ('right', 'bottom'), 'size_ratio': 0.25},
        'bottom-left': {'pos': ('left', 'bottom'), 'size_ratio': 0.25},
        'center': {'pos': ('center', 'center'), 'size_ratio': 0.3},
    }
    
    @classmethod
    def create(cls, main_clip: VideoFileClip, pip_clip: VideoFileClip, 
               layout: str = 'bottom-right', style: Optional[Dict[str, Any]] = None) -> CompositeVideoClip:
        """
        创建画中画效果
        
        Args:
            main_clip: 主视频
            pip_clip: 画中画视频
            layout: 布局模式
            style: 样式配置
            
        Returns:
            CompositeVideoClip 对象
        """
        style = style or {}
        
        # 获取布局配置
        layout_config = cls.LAYOUTS.get(layout, cls.LAYOUTS['bottom-right'])
        size_ratio = style.get('size', layout_config['size_ratio'])
        
        # 计算画中画尺寸
        pip_width = int(main_clip.w * size_ratio)
        pip_height = int(pip_clip.h * (pip_width / pip_clip.w))
        
        # 调整画中画大小
        pip_resized = pip_clip.resize(width=pip_width)
        
        # 添加边框
        if style.get('border', False):
            pip_resized = cls.add_border(pip_resized, style.get('borderColor', 'white'))
        
        # 添加阴影
        if style.get('shadow', False):
            pip_resized = cls.add_shadow(pip_resized)
        
        # 设置位置
        pip_resized = cls.set_position(pip_resized, main_clip, layout_config['pos'])
        
        # 添加过渡效果
        transition = style.get('transition', 'fade')
        if transition == 'fade':
            pip_resized = fadein(pip_resized, 0.5)
        
        return CompositeVideoClip([main_clip, pip_resized])
    
    @staticmethod
    def add_border(clip: VideoFileClip, color: str = 'white') -> CompositeVideoClip:
        """添加边框"""
        border_width = 2
        border = ColorClip(
            size=(clip.w + border_width * 2, clip.h + border_width * 2),
            color=tuple(int(color[i:i+2], 16) for i in (1, 3, 5)) if color.startswith('#') else (255, 255, 255)
        ).set_duration(clip.duration)
        return CompositeVideoClip([border, clip.set_position('center')])
    
    @staticmethod
    def add_shadow(clip: VideoFileClip) -> VideoFileClip:
        """添加阴影"""
        return clip.set_opacity(0.9)
    
    @staticmethod
    def set_position(clip: VideoFileClip, main_clip: VideoFileClip, pos: Tuple[str, str]) -> VideoFileClip:
        """设置画中画位置"""
        x_pos, y_pos = pos
        
        if x_pos == 'right':
            x = main_clip.w - clip.w - 20
        elif x_pos == 'left':
            x = 20
        else:
            x = (main_clip.w - clip.w) // 2
        
        if y_pos == 'bottom':
            y = main_clip.h - clip.h - 20
        elif y_pos == 'top':
            y = 20
        else:
            y = (main_clip.h - clip.h) // 2
        
        return clip.set_position((x, y))


class EffectService:
    """特效服务 - 统一管理所有特效"""
    
    def __init__(self):
        self.text_effect = TextEffect()
        self.follow_effect = FollowEffect()
        self.pip_effect = PIPEffect()
    
    def apply_text_effect(self, video_path: str, text: str, output_path: str,
                         style: Optional[Dict[str, Any]] = None) -> str:
        """应用文字特效到视频"""
        video = VideoFileClip(video_path)
        text_clip = TextEffect.create(text, video.duration, style)
        
        position = style.get('position', 'bottom-center') if style else 'bottom-center'
        text_clip = TextEffect.set_position(text_clip, position)
        
        final = CompositeVideoClip([video, text_clip])
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        video.close()
        final.close()
        
        return output_path
    
    def apply_follow_effect(self, video_path: str, output_path: str,
                           start_time: float, duration: float,
                           style: Optional[Dict[str, Any]] = None) -> str:
        """应用点关注特效到视频"""
        video = VideoFileClip(video_path)
        follow_clip = FollowEffect.create(duration, style)
        follow_clip = follow_clip.set_start(start_time)
        
        position = style.get('position', 'bottom-right') if style else 'bottom-right'
        if position == 'bottom-right':
            follow_clip = follow_clip.set_position((video.w - 100, video.h - 100))
        elif position == 'bottom-left':
            follow_clip = follow_clip.set_position((20, video.h - 100))
        
        final = CompositeVideoClip([video, follow_clip])
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        video.close()
        final.close()
        
        return output_path
    
    def apply_pip_effect(self, main_video_path: str, pip_video_path: str, 
                        output_path: str, layout: str = 'bottom-right',
                        style: Optional[Dict[str, Any]] = None) -> str:
        """应用画中画特效"""
        main_clip = VideoFileClip(main_video_path)
        pip_clip = VideoFileClip(pip_video_path)
        
        final = PIPEffect.create(main_clip, pip_clip, layout, style)
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        main_clip.close()
        pip_clip.close()
        final.close()
        
        return output_path


__all__ = ['EffectService', 'TextEffect', 'FollowEffect', 'PIPEffect']
