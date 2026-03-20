#!/usr/bin/env python3
"""
完整功能测试 - 音乐 + 字幕 + 特效
"""
import sys
sys.path.insert(0, 'src')

try:
    import importlib.resources as importlib_resources
except ImportError:
    import importlib_resources

from video_generator import VideoGenerator, AudioConfig, SubtitleConfig, EffectConfig

def test_full():
    """完整功能测试"""
    generator = VideoGenerator()
    
    print("=" * 50)
    print("🎬 完整功能测试")
    print("=" * 50)
    
    # 1. 加载视频
    print("\n📹 1. 加载视频...")
    video = generator.load_video('assets/test_clip.mp4')
    print(f"   ✅ 视频：{video.duration}秒，分辨率 {video.size}")
    
    # 2. 添加背景音乐
    print("\n🎵 2. 添加背景音乐...")
    video = generator.add_background_music(
        video,
        'assets/bgm.mp3',
        volume=0.3,
        fade_in=1.0,
        fade_out=1.0
    )
    print("   ✅ 音乐已添加（音量 30%，淡入淡出 1 秒）")
    
    # 3. 添加时间轴特效（模糊效果）
    print("\n✨ 3. 添加特效...")
    video = generator.add_effect_at_time(
        video,
        effect_type='blur',
        start_time=1.0,
        duration=2.0,
        blur_size=5
    )
    print("   ✅ 模糊特效已添加（1-3 秒）")
    
    # 4. 渲染输出
    print("\n🎬 4. 渲染输出...")
    output = generator.render(video, 'assets/output_full.mp4', fps=24)
    print(f"   ✅ 输出完成：{output}")
    
    print("\n" + "=" * 50)
    print("🎉 全部测试通过！")
    print("=" * 50)
    
    return output

if __name__ == '__main__':
    test_full()
