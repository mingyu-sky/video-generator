"""
视频生成系统 - 主处理流水线
"""
from moviepy.editor import *
from moviepy.video.tools.subtitles import SubtitlesClip
from pathlib import Path
import subprocess
from typing import List, Optional, Dict
from dataclasses import dataclass
from loguru import logger
import pysubs2
import click


@dataclass
class AudioConfig:
    """音频配置"""
    background_music: Optional[str] = None
    music_volume: float = 0.3
    voiceover: Optional[str] = None
    voiceover_volume: float = 0.8
    fade_in: float = 2.0
    fade_out: float = 2.0


@dataclass
class SubtitleConfig:
    """字幕配置"""
    srt_file: Optional[str] = None
    font: str = "思源黑体 Bold"
    font_size: int = 24
    color: str = "white"
    stroke_color: str = "black"
    stroke_width: int = 1
    position: str = "bottom"
    offset_y: int = -50


@dataclass
class EffectConfig:
    """特效配置"""
    intro_file: Optional[str] = None
    outro_file: Optional[str] = None
    effects: List[Dict] = None  # [{type, start_time, duration, params}]


class VideoGenerator:
    """视频生成器"""
    
    def __init__(self, temp_dir: str = "/tmp/video_gen"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"VideoGenerator initialized, temp dir: {self.temp_dir}")
    
    def load_video(self, video_path: str) -> VideoFileClip:
        """加载视频文件"""
        logger.info(f"Loading video: {video_path}")
        clip = VideoFileClip(str(video_path))
        logger.info(f"Video loaded: {clip.duration}s, {clip.size}")
        return clip
    
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
        
        # 加载配音
        voiceover = AudioFileClip(str(voiceover_path))
        voiceover = voiceover.volumex(volume)
        
        # 对齐模式
        if align_mode == 'start':
            start = 0
        elif align_mode == 'end':
            start = video.duration - voiceover.duration
        else:
            start = 0
        
        # 裁剪配音时长
        if start + voiceover.duration > video.duration:
            voiceover = voiceover.subclip(0, video.duration - start)
        
        # 如果降低背景音乐
        if reduce_bgm and video.audio is not None:
            # 简单实现：配音出现时背景音乐音量降低
            bgm_reduced = video.audio.volumex(0.3)
            combined = CompositeAudioClip([bgm_reduced, voiceover.set_start(start)])
            return video.set_audio(combined)
        else:
            return video.set_audio(voiceover.set_start(start))
    
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
                'start': sub.start / 1000.0,  # ms to s
                'end': sub.end / 1000.0,
                'content': text
            })
        
        # 渲染字幕
        sub_clip = SubtitlesClip(subtitles, make_textclip=make_textclip)
        
        # 设置位置
        if config.position == 'bottom':
            sub_clip = sub_clip.set_position(('center', video.h + config.offset_y))
        
        # 合成视频
        return CompositeVideoClip([video, sub_clip])
    
    def add_intro(
        self,
        video: VideoFileClip,
        intro_path: str,
        fade_duration: float = 0.5
    ) -> VideoFileClip:
        """添加片头"""
        logger.info(f"Adding intro: {intro_path}")
        
        intro = VideoFileClip(str(intro_path))
        
        # 淡入淡出
        intro = intro.crossfadein(fade_duration)
        video = video.crossfadein(fade_duration)
        
        # 拼接
        return concatenate_videoclips([intro, video])
    
    def add_outro(
        self,
        video: VideoFileClip,
        outro_path: str,
        fade_duration: float = 0.5
    ) -> VideoFileClip:
        """添加片尾"""
        logger.info(f"Adding outro: {outro_path}")
        
        outro = VideoFileClip(str(outro_path))
        
        # 淡入淡出
        video = video.crossfadeout(fade_duration)
        outro = outro.crossfadein(fade_duration)
        
        # 拼接
        return concatenate_videoclips([video, outro])
    
    def add_effect_at_time(
        self,
        video: VideoFileClip,
        effect_type: str,
        start_time: float,
        duration: float,
        **params
    ) -> VideoFileClip:
        """在指定时间添加特效"""
        logger.info(f"Adding effect {effect_type} at {start_time}s, duration {duration}s")
        
        # 裁剪出需要特效的片段
        effect_clip = video.subclip(start_time, start_time + duration)
        
        # 应用特效
        if effect_type == 'blur':
            effect_clip = effect_clip.resize(0.5).resize(video.size)
        elif effect_type == 'grayscale':
            effect_clip = effect_clip.fx(vfx.blackwhite)
        elif effect_type == 'speed':
            speed = params.get('speed', 1.0)
            effect_clip = effect_clip.speedx(speed)
        else:
            logger.warning(f"Unknown effect type: {effect_type}")
            return video
        
        # 拼接
        before = video.subclip(0, start_time) if start_time > 0 else None
        after = video.subclip(start_time + duration) if start_time + duration < video.duration else None
        
        clips = [c for c in [before, effect_clip, after] if c is not None]
        return concatenate_videoclips(clips)
    
    def render(
        self,
        video: VideoFileClip,
        output_path: str,
        fps: int = 30,
        codec: str = 'libx264',
        audio_codec: str = 'aac',
        bitrate: str = '5000k',
        preset: str = 'medium'
    ) -> str:
        """渲染输出视频"""
        logger.info(f"Rendering video to: {output_path}")
        
        output_path = str(output_path)
        
        # 写入视频
        video.write_videofile(
            output_path,
            fps=fps,
            codec=codec,
            audio_codec=audio_codec,
            bitrate=bitrate,
            preset=preset,
            temp_audiofile=str(self.temp_dir / "temp.m4a"),
            remove_temp=True
        )
        
        logger.info(f"Video rendered successfully: {output_path}")
        
        # 关闭资源
        video.close()
        
        return output_path
    
    def process(
        self,
        input_video: str,
        output_video: str,
        audio_config: Optional[AudioConfig] = None,
        subtitle_config: Optional[SubtitleConfig] = None,
        effect_config: Optional[EffectConfig] = None
    ) -> str:
        """完整处理流程"""
        logger.info(f"Starting processing: {input_video} -> {output_video}")
        
        # 加载视频
        video = self.load_video(input_video)
        
        # 处理音频
        if audio_config:
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
        
        # 处理字幕
        if subtitle_config and subtitle_config.srt_file:
            video = self.add_subtitles(video, subtitle_config.srt_file, subtitle_config)
        
        # 处理特效
        if effect_config:
            if effect_config.intro_file:
                video = self.add_intro(video, effect_config.intro_file)
            if effect_config.outro_file:
                video = self.add_outro(video, effect_config.outro_file)
            
            if effect_config.effects:
                for effect in effect_config.effects:
                    video = self.add_effect_at_time(
                        video,
                        effect['type'],
                        effect['start_time'],
                        effect['duration'],
                        **effect.get('params', {})
                    )
        
        # 渲染输出
        return self.render(video, output_video)


# CLI 入口
@click.command()
@click.option('--input', '-i', 'input_video', required=True, help='输入视频文件')
@click.option('--output', '-o', 'output_video', required=True, help='输出视频文件')
@click.option('--music', '-m', 'music_file', help='背景音乐文件')
@click.option('--voiceover', '-v', 'voiceover_file', help='配音文件')
@click.option('--subtitle', '-s', 'subtitle_file', help='字幕文件 (SRT)')
@click.option('--intro', 'intro_file', help='片头文件')
@click.option('--outro', 'outro_file', help='片尾文件')
def main(input_video, output_video, music_file, voiceover_file, 
         subtitle_file, intro_file, outro_file):
    """视频生成工具"""
    generator = VideoGenerator()
    
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
    
    # 处理视频
    output_path = generator.process(
        input_video,
        output_video,
        audio_config,
        subtitle_config,
        effect_config
    )
    
    print(f"✅ Video generated successfully: {output_path}")


if __name__ == '__main__':
    import click
    main()
