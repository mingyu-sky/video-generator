#!/usr/bin/env python3
"""
创建测试素材
使用 FFmpeg 生成测试视频和音频
"""

import subprocess
import os

ASSETS_DIR = "/home/admin/sora-video-generator/assets"

def create_test_video():
    """生成 10 秒测试视频（黑屏 + 测试音）"""
    output = f"{ASSETS_DIR}/test_video.mp4"
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'color=c=blue:s=1920x1080:d=10',
        '-f', 'lavfi', '-i', 'sine=frequency=440:duration=10',
        '-c:v', 'libx264', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '128k',
        '-shortest', output
    ]
    print(f"🎬 创建测试视频：{output}")
    subprocess.run(cmd, check=True)
    return output

def create_test_audio():
    """生成 5 秒测试音频"""
    output = f"{ASSETS_DIR}/test_audio.mp3"
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'sine=frequency=880:duration=5',
        '-c:a', 'libmp3lame', '-b:a', '128k',
        output
    ]
    print(f"🎵 创建测试音频：{output}")
    subprocess.run(cmd, check=True)
    return output

def create_test_image():
    """生成测试图片（使用 FFmpeg）"""
    output = f"{ASSETS_DIR}/test_image.png"
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'color=c=red:s=800x600:d=1',
        '-frames:v', '1',
        output
    ]
    print(f"🖼️  创建测试图片：{output}")
    subprocess.run(cmd, check=True)
    return output

if __name__ == "__main__":
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    print("=" * 60)
    print("🎨 创建测试素材")
    print("=" * 60)
    
    create_test_video()
    create_test_audio()
    create_test_image()
    
    print("\n✅ 测试素材创建完成！")
    print(f"📁 目录：{ASSETS_DIR}")
