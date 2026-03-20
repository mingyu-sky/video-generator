#!/usr/bin/env python3
"""
Edge TTS 配音测试
"""
import sys
sys.path.insert(0, 'src')

from video_generator_v2 import VideoGenerator, TTSConfig

def test_edge_tts():
    """测试 Edge TTS 配音生成"""
    print("=" * 50)
    print("🎤 Edge TTS 配音测试")
    print("=" * 50)
    
    generator = VideoGenerator()
    
    # 测试文本
    test_text = """
    欢迎观看视频生成系统测试。
    这是使用 Edge TTS 生成的 AI 配音。
    支持多语言、多音色、语速调节。
    效果还不错吧？
    """
    
    print("\n📝 测试文本:")
    print(test_text.strip())
    
    print("\n🎵 生成配音...")
    try:
        output = generator.generate_voiceover(
            text=test_text,
            output_path='assets/test_voiceover.mp3',
            config=TTSConfig(
                voice="zh-CN-XiaoxiaoNeural",  # 中文女声
                rate="+0%",
                volume="+0%",
                pitch="+0Hz"
            )
        )
        print(f"✅ 配音生成成功：{output}")
        
        # 验证文件
        import os
        size = os.path.getsize(output)
        print(f"   文件大小：{size/1024:.1f} KB")
        
    except Exception as e:
        print(f"❌ 失败：{e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    print("=" * 50)
    return True

if __name__ == '__main__':
    success = test_edge_tts()
    sys.exit(0 if success else 1)
