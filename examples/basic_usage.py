#!/usr/bin/env python3
"""
视频生成示例脚本
"""
from video_generator import VideoGenerator, AudioConfig, SubtitleConfig, EffectConfig


def example_basic():
    """基础示例：添加音乐和字幕"""
    generator = VideoGenerator()
    
    audio_config = AudioConfig(
        background_music='assets/bgm.mp3',
        music_volume=0.3,
        fade_in=2.0,
        fade_out=2.0
    )
    
    subtitle_config = SubtitleConfig(
        srt_file='assets/subtitles.srt',
        font_size=24,
        color='white'
    )
    
    output = generator.process(
        input_video='input.mp4',
        output_video='output_basic.mp4',
        audio_config=audio_config,
        subtitle_config=subtitle_config
    )
    
    print(f"Generated: {output}")


def example_full():
    """完整示例：音乐 + 配音 + 字幕 + 片头片尾 + 特效"""
    generator = VideoGenerator()
    
    audio_config = AudioConfig(
        background_music='assets/bgm.mp3',
        music_volume=0.3,
        voiceover='assets/voiceover.mp3',
        voiceover_volume=0.8
    )
    
    subtitle_config = SubtitleConfig(
        srt_file='assets/subtitles.srt',
        font='思源黑体 Bold',
        font_size=24
    )
    
    effect_config = EffectConfig(
        intro_file='assets/intro.mp4',
        outro_file='assets/outro.mp4',
        effects=[
            {'type': 'blur', 'start_time': 10.0, 'duration': 2.0},
            {'type': 'grayscale', 'start_time': 20.0, 'duration': 3.0}
        ]
    )
    
    output = generator.process(
        input_video='input.mp4',
        output_video='output_full.mp4',
        audio_config=audio_config,
        subtitle_config=subtitle_config,
        effect_config=effect_config
    )
    
    print(f"Generated: {output}")


def example_batch():
    """批量处理示例"""
    from video_generator import VideoGenerator, AudioConfig
    import concurrent.futures
    
    generator = VideoGenerator()
    
    tasks = [
        {
            'input': 'video1.mp4',
            'output': 'output1.mp4',
            'audio_config': AudioConfig(background_music='bgm1.mp3')
        },
        {
            'input': 'video2.mp4',
            'output': 'output2.mp4',
            'audio_config': AudioConfig(background_music='bgm2.mp3')
        },
        # ... 更多任务
    ]
    
    def process_task(task):
        return generator.process(**task)
    
    # 并行处理（4 个并发）
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(process_task, tasks))
    
    print(f"Batch processed {len(results)} videos")


if __name__ == '__main__':
    # 运行示例
    print("Running basic example...")
    example_basic()
    
    print("\nRunning full example...")
    example_full()
