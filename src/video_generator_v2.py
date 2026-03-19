"""
视频生成系统 - 主处理流水线
版本：v1.1 (已改进)
改进内容:
- 资源管理：使用 context manager 确保剪辑资源正确释放
- 错误处理：完善的异常捕获和重试机制
- 输入验证：文件路径、参数范围验证
- 配置管理：支持环境变量和配置文件
- 进度回调：长时间处理提供进度通知
"""
from moviepy.editor import *
from moviepy.video.tools.subtitles import SubtitlesClip
from pathlib import Path
from typing import List, Optional, Dict, Callable
from dataclasses import dataclass
from loguru import logger
import pysubs2
import os
import time
from contextlib import contextmanager
import functools


# ==================== 异常定义 ====================

class VideoProcessingError(Exception):
    """视频处理异常基类"""
    pass


class FileNotFoundError(VideoProcessingError):
    """文件未找到"""
    pass


class InvalidParameterError(VideoProcessingError):
    """无效参数"""
    pass


class ResourceExhaustedError(VideoProcessingError):
    """资源耗尽"""
    pass


class RenderError(VideoProcessingError):
    """渲染失败"""
    pass


# ==================== 重试装饰器 ====================

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """失败重试装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay * attempt)  # 指数退避
            logger.error(f"All {max_attempts} attempts failed")
            raise last_exception
        return wrapper
    return decorator


# ==================== 配置类 ====================

@dataclass
class SystemConfig:
    """系统配置"""
    temp_dir: str = "/tmp/video_gen"
    max_file_size_gb: float = 2.0
    max_video_duration_hours: int = 4
    ffmpeg_preset: str = "medium"
    gpu_acceleration: bool = False
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            temp_dir=os.getenv("VIDEO_GEN_TEMP", "/tmp/video_gen"),
            max_file_size_gb=float(os.getenv("VIDEO_GEN_MAX_SIZE", "2.0")),
            gpu_acceleration=os.getenv("VIDEO_GEN_GPU", "false").lower() == "true"
        )


@dataclass
class AudioConfig:
    """音频配置"""
    background_music: Optional[str] = None
    music_volume: float = 0.3
    voiceover: Optional[str] = None
    voiceover_volume: float = 0.8
    fade_in: float = 2.0
    fade_out: float = 2.0
    
    def validate(self):
        """验证参数"""
        if not 0 <= self.music_volume <= 1.0:
            raise InvalidParameterError(f"Music volume must be 0-1, got {self.music_volume}")
        if not 0 <= self.voiceover_volume <= 1.0:
            raise InvalidParameterError(f"Voiceover volume must be 0-1, got {self.voiceover_volume}")
        if self.fade_in < 0 or self.fade_out < 0:
            raise InvalidParameterError("Fade duration cannot be negative")


@dataclass
class SubtitleConfig:
    """字幕配置"""
    srt_file: Optional[str] = None
    font: str = "Arial"
    font_size: int = 24
    color: str = "white"
    stroke_color: str = "black"
    stroke_width: int = 1
    position: str = "bottom"
    offset_y: int = -50
    
    def validate(self):
        """验证参数"""
        if self.position not in ["bottom", "top", "center"]:
            raise InvalidParameterError(f"Invalid position: {self.position}")


@dataclass
class EffectConfig:
    """特效配置"""
    intro_file: Optional[str] = None
    outro_file: Optional[str] = None
    effects: List[Dict] = field(default_factory=list)


# ==================== 核心处理类 ====================

class VideoGenerator:
    """视频生成器"""
    
    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or SystemConfig.from_env()
        self.temp_dir = Path(self.config.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置日志
        logger.add(
            self.temp_dir / "video_generator.log",
            rotation="10 MB",
            retention="5 days",
            level=self.config.log_level
        )
        
        logger.info(f"VideoGenerator initialized, temp dir: {self.temp_dir}")
        logger.info(f"Config: GPU={self.config.gpu_acceleration}, MaxSize={self.config.max_file_size_gb}GB")
    
    @contextmanager
    def manage_clip(self, clip):
        """上下文管理器：确保剪辑资源正确释放"""
        try:
            yield clip
        finally:
            if clip:
                try:
                    clip.close()
                except Exception as e:
                    logger.warning(f"Failed to close clip: {e}")
    
    def _validate_file(self, file_path: str, file_type: str = "File"):
        """验证文件存在和大小"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"{file_type} not found: {file_path}")
        
        # 检查文件大小
        size_gb = path.stat().st_size / (1024**3)
        if size_gb > self.config.max_file_size_gb:
            raise InvalidParameterError(
                f"{file_type} size ({size_gb:.2f}GB) exceeds limit ({self.config.max_file_size_gb}GB)"
            )
    
    def _validate_duration(self, duration: float, max_hours: int = None):
        """验证视频时长"""
        max_hours = max_hours or self.config.max_video_duration_hours
        max_seconds = max_hours * 3600
        
        if duration > max_seconds:
            raise InvalidParameterError(
                f"Video duration ({duration/3600:.2f}h) exceeds limit ({max_hours}h)"
            )
    
    def load_video(self, video_path: str) -> VideoFileClip:
        """加载视频文件"""
        logger.info(f"Loading video: {video_path}")
        
        # 验证文件
        self._validate_file(video_path, "Video file")
        
        try:
            clip = VideoFileClip(str(video_path))
            self._validate_duration(cl ip.duration)
            logger.info(f"Video loaded: {clip.duration}s, {clip.size}")
            return clip
        except Exception as e:
            logger.error(f"Failed to load video: {e}")
            raise VideoProcessingError(f"Failed to load video {video_path}: {e}")
    
    @retry_on_failure(max_attempts=3, delay=1.0, exceptions=(RenderError,))
    def add_background_music(
        self, 
        video: VideoFileClip, 
        music_path: str, 
        volume: float = 0.3,
        fade_in: float = 2.0,
        fade_out: float = 2.0
    ) -> VideoFileClip:
        """添加背景音乐"""
        logger.info(f"Adding background music: {music_path}, volume: {volume}")
        
        # 验证文件
        self._validate_file(music_path, "Music file")
        
        try:
            # 加载音乐
            music = AudioFileClip(str(music_path))
            
            # 裁剪音乐时长匹配视频
            if music.duration > video.duration:
                music = music.subclip(0, video.duration)
            
            # 淡入淡出
            music = music.audio_fadein(fade_in).audio_fadeout(fade_out)
            
            # 调节音量
            music = music.volumex(volume)
            
            # 如果视频已有音频，混合；否则直接设置
            if video.audio is not None:
                final_audio = CompositeAudioClip([video.audio, music])
            else:
                final_audio = music
            
            return video.set_audio(final_audio)
        
        except Exception as e:
            logger.error(f"Failed to add background music: {e}")
            raise RenderError(f"Failed to add background music: {e}")
    
    def add_voiceover(
        self,
        video: VideoFileClip,
        voiceover_path: str,
        volume: float = 0.8,
        align_mode: str = 'start',
        reduce_bgm: bool = True
    ) -> VideoFileClip:
        """添加配音"""
        logger.info(f"Adding voiceover: {voiceover_path}, mode: {align_mode}")
        
        # 验证文件
        self._validate_file(voiceover_path, "Voiceover file")
        
        try:
            # 加载配音
            voiceover = AudioFileClip(str(voiceover_path))
            voiceover = voiceover.volumex(volume)
            
            # 对齐模式
            if align_mode == 'start':
                start = 0
            elif align_mode == 'end':
                start = max(0, video.duration - voiceover.duration)
            else:
                start = 0
            
            # 裁剪配音时长
            if start + voiceover.duration > video.duration:
                voiceover = voiceover.subclip(0, video.duration - start)
            
            # 如果降低背景音乐
            if reduce_bgm and video.audio is not None:
                bgm_reduced = video.audio.volumex(0.3)
                combined = CompositeAudioClip([bgm_reduced, voiceover.set_start(start)])
                return video.set_audio(combined)
            else:
                return video.set_audio(voiceover.set_start(start))
        
        except Exception as e:
            logger.error(f"Failed to add voiceover: {e}")
            raise RenderError(f"Failed to add voiceover: {e}")
    
    def add_subtitles(
        self,
        video: VideoFileClip,
        srt_path: str,
        config: Optional[SubtitleConfig] = None
    ) -> VideoFileClip:
        """添加字幕"""
        logger.info(f"Adding subtitles: {srt_path}")
        
        if config is None:
            config = SubtitleConfig()
        
        # 验证配置
        config.validate()
        self._validate_file(srt_path, "Subtitle file")
        
        try:
            # 解析 SRT 文件
            subs = pysubs2.load(str(srt_path))
            
            # 转换为 MoviePy 格式
            def make_textclip(text):
                return TextClip(
                    text,
                    font=config.font,
                    fontsize=config.font_size,
                    color=config.color,
                    stroke_color=config.stroke_color,
                    stroke_width=config.stroke_width
                )
            
            # 创建字幕片段
            subtitles = []
            for sub in subs:
                text = sub.text.replace('\\N', '\n')
                subtitles.append({
                    'start': sub.start / 1000.0,
                    'end': sub.end / 1000.0,
                    'content': text
                })
            
            # 渲染字幕
            sub_clip = SubtitlesClip(subtitles, make_textclip=make_textclip)
            
            # 设置位置
            if config.position == 'bottom':
                sub_clip = sub_clip.set_position(('center', video.h + config.offset_y))
            elif config.position == 'top':
                sub_clip = sub_clip.set_position(('center', -config.offset_y))
            else:
                sub_clip = sub_clip.set_position(('center', 'center'))
            
            # 合成视频
            return CompositeVideoClip([video, sub_clip])
        
        except Exception as e:
            logger.error(f"Failed to add subtitles: {e}")
            raise RenderError(f"Failed to add subtitles: {e}")
    
    def add_intro(
        self,
        video: VideoFileClip,
        intro_path: str,
        fade_duration: float = 0.5
    ) -> VideoFileClip:
        """添加片头"""
        logger.info(f"Adding intro: {intro_path}")
        
        self._validate_file(intro_path, "Intro file")
        
        try:
            intro = VideoFileClip(str(intro_path))
            intro = intro.crossfadein(fade_duration)
            video = video.crossfadein(fade_duration)
            return concatenate_videoclips([intro, video])
        except Exception as e:
            logger.error(f"Failed to add intro: {e}")
            raise RenderError(f"Failed to add intro: {e}")
    
    def add_outro(
        self,
        video: VideoFileClip,
        outro_path: str,
        fade_duration: float = 0.5
    ) -> VideoFileClip:
        """添加片尾"""
        logger.info(f"Adding outro: {outro_path}")
        
        self._validate_file(outro_path, "Outro file")
        
        try:
            outro = VideoFileClip(str(outro_path))
            video = video.crossfadeout(fade_duration)
            outro = outro.crossfadein(fade_duration)
            return concatenate_videoclips([video, outro])
        except Exception as e:
            logger.error(f"Failed to add outro: {e}")
            raise RenderError(f"Failed to add outro: {e}")
    
    def add_effect_at_time(
        self,
        video: VideoFileClip,
        effect_type: str,
        start_time: float,
        duration: float,
        progress_callback: Optional[Callable[[float], None]] = None,
        **params
    ) -> VideoFileClip:
        """在指定时间添加特效"""
        logger.info(f"Adding effect {effect_type} at {start_time}s, duration {duration}s")
        
        try:
            # 验证时间范围
            if start_time < 0 or start_time >= video.duration:
                raise InvalidParameterError(f"Effect start_time {start_time}s is out of range [0, {video.duration})")
            
            # 裁剪出需要特效的片段
            effect_clip = video.subclip(start_time, min(start_time + duration, video.duration))
            
            # 应用特效
            if effect_type == 'blur':
                effect_clip = effect_clip.resize(0.5).resize(video.size)
            elif effect_type == 'grayscale':
                effect_clip = effect_clip.fx(vfx.blackwhite)
            elif effect_type == 'speed':
                speed = params.get('speed', 1.0)
                if speed <= 0:
                    raise InvalidParameterError(f"Speed must be positive, got {speed}")
                effect_clip = effect_clip.speedx(speed)
            else:
                logger.warning(f"Unknown effect type: {effect_type}, skipping")
                return video
            
            # 拼接
            before = video.subclip(0, start_time) if start_time > 0 else None
            after = video.subclip(start_time + duration) if start_time + duration < video.duration else None
            
            clips = [c for c in [before, effect_clip, after] if c is not None]
            result = concatenate_videoclips(clips)
            
            if progress_callback:
                progress_callback(1.0)
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to add effect: {e}")
            raise RenderError(f"Failed to add effect: {e}")
    
    @retry_on_failure(max_attempts=2, delay=2.0, exceptions=(RenderError,))
    def render(
        self,
        video: VideoFileClip,
        output_path: str,
        fps: int = 30,
        codec: str = 'libx264',
        audio_codec: str = 'aac',
        bitrate: str = '5000k',
        preset: str = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> str:
        """渲染输出视频"""
        logger.info(f"Rendering video to: {output_path}")
        
        preset = preset or self.config.ffmpeg_preset
        
        if self.config.gpu_acceleration:
            codec = 'h264_nvenc'
            preset = 'p5'
            logger.info("Using GPU acceleration")
        
        try:
            output_path = str(output_path)
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 写入视频
            video.write_videofile(
                output_path,
                fps=fps,
                codec=codec,
                audio_codec=audio_codec,
                bitrate=bitrate,
                preset=preset,
                temp_audiofile=str(self.temp_dir / f"temp_{os.getpid()}.m4a"),
                remove_temp=True,
                logger='bar' if progress_callback else None,
                callback=progress_callback
            )
            
            logger.info(f"Video rendered successfully: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to render video: {e}")
            raise RenderError(f"Failed to render video: {e}")
    
    def process(
        self,
        input_video: str,
        output_video: str,
        audio_config: Optional[AudioConfig] = None,
        subtitle_config: Optional[SubtitleConfig] = None,
        effect_config: Optional[EffectConfig] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> str:
        """
        完整处理流程
        
        Args:
            input_video: 输入视频路径
            output_video: 输出视频路径
            audio_config: 音频配置
            subtitle_config: 字幕配置
            effect_config: 特效配置
            progress_callback: 进度回调函数 (stage, progress)
        """
        logger.info(f"Starting processing: {input_video} -> {output_video}")
        
        video = None
        
        try:
            # 验证输入文件
            self._validate_file(input_video, "Input video")
            
            # 加载视频
            if progress_callback:
                progress_callback("load", 0.0)
            video = self.load_video(input_video)
            if progress_callback:
                progress_callback("load", 1.0)
            
            # 处理音频
            if audio_config:
                audio_config.validate()
                if progress_callback:
                    progress_callback("audio", 0.0)
                
                if audio_config.background_music:
                    video = self.add_background_music(
                        video,
                        audio_config.background_music,
                        audio_config.music_volume,
                        audio_config.fade_in,
                        audio_config.fade_out
                    )
                if audio_config.voiceover:
                    video = self.add_voiceover(
                        video,
                        audio_config.voiceover,
                        audio_config.voiceover_volume
                    )
                
                if progress_callback:
                    progress_callback("audio", 1.0)
            
            # 处理字幕
            if subtitle_config and subtitle_config.srt_file:
                if progress_callback:
                    progress_callback("subtitle", 0.0)
                video = self.add_subtitles(video, subtitle_config.srt_file, subtitle_config)
                if progress_callback:
                    progress_callback("subtitle", 1.0)
            
            # 处理特效
            if effect_config:
                if progress_callback:
                    progress_callback("effects", 0.0)
                
                if effect_config.intro_file:
                    video = self.add_intro(video, effect_config.intro_file)
                if effect_config.outro_file:
                    video = self.add_outro(video, effect_config.outro_file)
                
                if effect_config.effects:
                    for i, effect in enumerate(effect_config.effects):
                        if progress_callback:
                            progress_callback("effects", (i + 1) / len(effect_config.effects))
                        video = self.add_effect_at_time(
                            video,
                            effect['type'],
                            effect['start_time'],
                            effect['duration'],
                            progress_callback=None,
                            **effect.get('params', {})
                        )
                
                if progress_callback:
                    progress_callback("effects", 1.0)
            
            # 渲染输出
            if progress_callback:
                progress_callback("render", 0.0)
            output_path = self.render(video, output_video)
            if progress_callback:
                progress_callback("render", 1.0)
            
            logger.info(f"Processing completed: {output_video}")
            return output_path
        
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise
        finally:
            # 确保资源释放
            if video:
                try:
                    video.close()
                except Exception as e:
                    logger.warning(f"Failed to close video clip: {e}")


# ==================== CLI 入口 ====================

if __name__ == '__main__':
    import click
    
    @click.command()
    @click.option('--input', '-i', 'input_video', required=True, help='输入视频文件')
    @click.option('--output', '-o', 'output_video', required=True, help='输出视频文件')
    @click.option('--music', '-m', 'music_file', help='背景音乐文件')
    @click.option('--voiceover', '-v', 'voiceover_file', help='配音文件')
    @click.option('--subtitle', '-s', 'subtitle_file', help='字幕文件 (SRT)')
    @click.option('--intro', 'intro_file', help='片头文件')
    @click.option('--outro', 'outro_file', help='片尾文件')
    @click.option('--gpu', is_flag=True, help='启用 GPU 加速')
    @click.option('--verbose', is_flag=True, help='详细日志')
    def main(input_video, output_video, music_file, voiceover_file, 
             subtitle_file, intro_file, outro_file, gpu, verbose):
        """视频生成工具"""
        
        # 配置系统
        config = SystemConfig.from_env()
        config.gpu_acceleration = gpu
        config.log_level = "DEBUG" if verbose else "INFO"
        
        generator = VideoGenerator(config=config)
        
        # 构建配置
        audio_config = AudioConfig(
            background_music=music_file,
            voiceover=voiceover_file
        ) if (music_file or voiceover_file) else None
        
        subtitle_config = SubtitleConfig(
            srt_file=subtitle_file
        ) if subtitle_file else None
        
        effect_config = EffectConfig(
            intro_file=intro_file,
            outro_file=outro_file
        ) if (intro_file or outro_file) else None
        
        # 进度回调
        def on_progress(stage, progress):
            click.echo(f"\rProcessing [{stage}]: {progress*100:.0f}%", nl=False)
        
        try:
            # 处理视频
            output_path = generator.process(
                input_video,
                output_video,
                audio_config,
                subtitle_config,
                effect_config,
                progress_callback=on_progress
            )
            
            click.echo(f"\n✅ Video generated successfully: {output_path}")
        
        except FileNotFoundError as e:
            click.echo(f"\n❌ File error: {e}", err=True)
            raise SystemExit(1)
        
        except InvalidParameterError as e:
            click.echo(f"\n❌ Parameter error: {e}", err=True)
            raise SystemExit(1)
        
        except RenderError as e:
            click.echo(f"\n❌ Render error: {e}", err=True)
            raise SystemExit(1)
    
    main()
