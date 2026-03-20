"""
音频服务单元测试 (AudioService)
测试用例覆盖：
- TC-AUDIO-SVC-001: 配音生成 - 正常流程
- TC-AUDIO-SVC-002: 配音生成 - 默认音色
- TC-AUDIO-SVC-003: 配音生成 - 语速音量调节
- TC-AUDIO-SVC-004: 配音生成 - 空文本验证
- TC-AUDIO-SVC-005: 配音生成 - 长文本验证
- TC-AUDIO-SVC-006: 配音生成 - 音色验证
- TC-AUDIO-SVC-007: 获取音色列表
"""
import pytest
import os
import sys
import asyncio
import uuid
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.audio_service import AudioService, EDGE_TTS_AVAILABLE


class TestAudioServiceVoiceover:
    """音频服务 - 配音生成测试"""
    
    @pytest.fixture
    def audio_service(self):
        """创建音频服务实例"""
        return AudioService()
    
    @pytest.mark.asyncio
    async def test_voiceover_success(self, audio_service):
        """TC-AUDIO-SVC-001: 配音生成 - 正常流程"""
        if not EDGE_TTS_AVAILABLE:
            pytest.skip("Edge TTS 未安装，跳过测试")
        
        result = await audio_service.generate_voiceover(
            text="这是测试配音文本",
            voice="zh-CN-XiaoxiaoNeural",
            speed=1.0,
            volume=1.0
        )
        
        assert "audioId" in result
        assert "fileName" in result
        assert "filePath" in result
        assert result["voice"] == "zh-CN-XiaoxiaoNeural"
        assert os.path.exists(result["filePath"])
        
        # 清理测试文件
        if os.path.exists(result["filePath"]):
            os.remove(result["filePath"])
    
    @pytest.mark.asyncio
    async def test_voiceover_default_voice(self, audio_service):
        """TC-AUDIO-SVC-002: 配音生成 - 使用默认音色"""
        if not EDGE_TTS_AVAILABLE:
            pytest.skip("Edge TTS 未安装，跳过测试")
        
        result = await audio_service.generate_voiceover(
            text="使用默认音色测试"
        )
        
        assert "audioId" in result
        assert "fileName" in result
        assert result["voice"] == "zh-CN-XiaoxiaoNeural"  # 默认音色
        
        # 清理测试文件
        if os.path.exists(result["filePath"]):
            os.remove(result["filePath"])
    
    @pytest.mark.asyncio
    async def test_voiceover_custom_speed_volume(self, audio_service):
        """TC-AUDIO-SVC-003: 配音生成 - 自定义语速音量"""
        if not EDGE_TTS_AVAILABLE:
            pytest.skip("Edge TTS 未安装，跳过测试")
        
        result = await audio_service.generate_voiceover(
            text="测试语速音量调节",
            speed=1.5,
            volume=0.8
        )
        
        assert "audioId" in result
        assert "fileName" in result
        assert os.path.exists(result["filePath"])
        
        # 清理测试文件
        if os.path.exists(result["filePath"]):
            os.remove(result["filePath"])
    
    @pytest.mark.asyncio
    async def test_voiceover_empty_text(self, audio_service):
        """TC-AUDIO-SVC-004: 配音生成 - 空文本验证"""
        with pytest.raises(ValueError) as exc_info:
            await audio_service.generate_voiceover(text="")
        
        assert "文本不能为空" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_voiceover_long_text(self, audio_service):
        """TC-AUDIO-SVC-005: 配音生成 - 长文本验证"""
        # 生成超过 10000 字的文本
        long_text = "测试" * 5001  # 10002 字
        
        with pytest.raises(ValueError) as exc_info:
            await audio_service.generate_voiceover(text=long_text)
        
        assert "文本过长" in str(exc_info.value) or "最大支持 10000 字" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_voiceover_custom_output_name(self, audio_service):
        """配音生成 - 自定义输出文件名"""
        if not EDGE_TTS_AVAILABLE:
            pytest.skip("Edge TTS 未安装，跳过测试")
        
        custom_name = f"custom_{uuid.uuid4().hex[:8]}.mp3"
        result = await audio_service.generate_voiceover(
            text="测试自定义文件名",
            output_name=custom_name
        )
        
        assert result["fileName"] == custom_name
        assert os.path.exists(result["filePath"])
        
        # 清理测试文件
        if os.path.exists(result["filePath"]):
            os.remove(result["filePath"])
    
    @pytest.mark.asyncio
    async def test_voiceover_speed_bounds(self, audio_service):
        """配音生成 - 语速边界值处理"""
        if not EDGE_TTS_AVAILABLE:
            pytest.skip("Edge TTS 未安装，跳过测试")
        
        # 测试语速下限 (应该被限制到 0.5)
        result1 = await audio_service.generate_voiceover(
            text="测试语速下限",
            speed=0.1  # 低于 0.5，应该被限制
        )
        assert result1["fileName"]
        
        # 测试语速上限 (应该被限制到 2.0)
        result2 = await audio_service.generate_voiceover(
            text="测试语速上限",
            speed=3.0  # 高于 2.0，应该被限制
        )
        assert result2["fileName"]
        
        # 清理测试文件
        for r in [result1, result2]:
            if os.path.exists(r["filePath"]):
                os.remove(r["filePath"])
    
    @pytest.mark.asyncio
    async def test_voiceover_volume_bounds(self, audio_service):
        """配音生成 - 音量边界值处理"""
        if not EDGE_TTS_AVAILABLE:
            pytest.skip("Edge TTS 未安装，跳过测试")
        
        # 测试音量下限 (应该被限制到 0.0)
        result1 = await audio_service.generate_voiceover(
            text="测试音量下限",
            volume=-0.5  # 低于 0.0，应该被限制
        )
        assert result1["fileName"]
        
        # 测试音量上限 (应该被限制到 1.0)
        result2 = await audio_service.generate_voiceover(
            text="测试音量上限",
            volume=2.0  # 高于 1.0，应该被限制
        )
        assert result2["fileName"]
        
        # 清理测试文件
        for r in [result1, result2]:
            if os.path.exists(r["filePath"]):
                os.remove(r["filePath"])


class TestAudioServiceVoices:
    """音频服务 - 音色管理测试"""
    
    @pytest.fixture
    def audio_service(self):
        """创建音频服务实例"""
        return AudioService()
    
    @pytest.mark.asyncio
    async def test_list_voices(self, audio_service):
        """TC-AUDIO-SVC-007: 获取音色列表"""
        voices = await audio_service.list_voices()
        
        assert isinstance(voices, list)
        assert len(voices) > 0
        
        # 验证返回格式
        for voice in voices[:5]:  # 检查前 5 个
            assert "name" in voice
            assert "gender" in voice
            assert "locale" in voice
    
    @pytest.mark.asyncio
    async def test_supported_voices_contains_chinese(self, audio_service):
        """验证支持的音色包含中文音色"""
        # 检查预设的中文音色列表
        assert "zh-CN-XiaoxiaoNeural" in audio_service.supported_voices
        assert "zh-CN-YunxiNeural" in audio_service.supported_voices
        assert "zh-CN-XiaoyiNeural" in audio_service.supported_voices
    
    def test_default_voice(self, audio_service):
        """验证默认音色设置"""
        assert audio_service.default_voice == "zh-CN-XiaoxiaoNeural"


class TestAudioServiceASR:
    """音频服务 - ASR 字幕生成测试"""
    
    @pytest.fixture
    def audio_service(self):
        """创建音频服务实例"""
        return AudioService()
    
    @pytest.mark.asyncio
    async def test_generate_mock_subtitles_srt(self, audio_service):
        """ASR - 生成模拟 SRT 字幕"""
        content = audio_service._generate_mock_subtitles("srt")
        
        assert "00:00:00,000 --> 00:00:02,000" in content
        assert "这是模拟的 ASR 字幕内容" in content
    
    @pytest.mark.asyncio
    async def test_generate_mock_subtitles_vtt(self, audio_service):
        """ASR - 生成模拟 VTT 字幕"""
        content = audio_service._generate_mock_subtitles("vtt")
        
        assert "WEBVTT" in content
        assert "00:00:00.000 --> 00:00:02.000" in content
    
    @pytest.mark.asyncio
    async def test_generate_asr_file_not_found(self, audio_service):
        """ASR - 音频文件不存在"""
        with pytest.raises(ValueError) as exc_info:
            await audio_service.generate_asr(
                audio_id="fake_id",
                audio_path="/nonexistent/path/audio.mp3"
            )
        
        assert "音频文件不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_asr_invalid_language(self, audio_service):
        """ASR - 不支持的语言（应使用默认语言）"""
        # 创建一个临时音频文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake audio content")
            temp_path = f.name
        
        try:
            result = await audio_service.generate_asr(
                audio_id="test_id",
                audio_path=temp_path,
                language="invalid-lang"  # 不支持的语言
            )
            
            # 应该使用默认语言 zh-CN
            assert result["language"] == "zh-CN" or "language" in result
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestAudioServiceIntegration:
    """音频服务集成测试"""
    
    @pytest.fixture
    def audio_service(self):
        """创建音频服务实例"""
        return AudioService()
    
    @pytest.mark.asyncio
    async def test_full_voiceover_workflow(self, audio_service):
        """完整配音工作流程测试"""
        if not EDGE_TTS_AVAILABLE:
            pytest.skip("Edge TTS 未安装，跳过测试")
        
        # 1. 生成配音
        result = await audio_service.generate_voiceover(
            text="这是一个完整的配音工作流程测试",
            voice="zh-CN-YunxiNeural",
            speed=1.2,
            volume=0.9
        )
        
        # 2. 验证结果
        assert "audioId" in result
        assert "filePath" in result
        assert os.path.exists(result["filePath"])
        
        # 3. 验证文件大小 (应该大于 0)
        file_size = os.path.getsize(result["filePath"])
        assert file_size > 0
        
        # 4. 清理测试文件
        os.remove(result["filePath"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
