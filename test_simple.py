#!/usr/bin/env python3
"""
简单测试脚本 - 测试视频生成基础功能
"""
import sys
sys.path.insert(0, 'src')

# Python 3.6 兼容
try:
    import importlib.resources as importlib_resources
except ImportError:
    import importlib_resources

from video_generator import VideoGenerator, AudioConfig

def test_basic():
    """基础测试：加载视频并输出"""
    generator = VideoGenerator()
    
    print("📹 加载测试视频...")
    video = generator.load_video('assets/test_video.mp4')
    print(f"✅ 视频加载成功：{video.duration}秒, {video.size}")
    
    print("\n🎵 添加背景音乐测试...")
    # 用同一个视频当背景音乐（测试用）
    video_with_music = generator.add_background_music(
        video, 
        'assets/test_video.mp4', 
        volume=0.3,
        fade_in=1.0,
        fade_out=1.0
    )
    print("✅ 音乐添加成功")
    
    print("\n🎬 渲染输出...")
    output = generator.render(video_with_music, 'assets/output_test.mp4')
    print(f"✅ 输出成功：{output}")
    
    print("\n🎉 测试完成！")
    return output

if __name__ == '__main__':
    test_basic()
