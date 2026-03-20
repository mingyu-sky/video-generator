"""
ASR 服务单元测试
测试阿里云语音转字幕功能
"""
import pytest
import os
import sys
import asyncio
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.asr_service import AliyunASRService


class TestAliyunASRService:
    """阿里云 ASR 服务测试"""
    
    @pytest.fixture
    def asr_service(self):
        """创建 ASR 服务实例"""
        # 使用环境变量或测试密钥
        return AliyunASRService(
            access_key_id=os.getenv("ALIYUN_ACCESS_KEY_ID", "test_key_id"),
            access_key_secret=os.getenv("ALIYUN_ACCESS_KEY_SECRET", "test_key_secret")
        )
    
    @pytest.fixture
    def test_audio_file(self, tmp_path):
        """创建测试音频文件"""
        audio_path = tmp_path / "test_audio.mp3"
        # 创建假的音频文件内容
        audio_path.write_bytes(b"fake audio content")
        return str(audio_path)
    
    def test_init_default(self):
        """测试初始化（默认配置）"""
        service = AliyunASRService()
        assert service.supported_languages is not None
        assert "zh-CN" in service.supported_languages
        assert "en-US" in service.supported_languages
    
    def test_init_with_credentials(self):
        """测试初始化（带凭证）"""
        service = AliyunASRService(
            access_key_id="test_id",
            access_key_secret="test_secret"
        )
        assert service.access_key_id == "test_id"
        assert service.access_key_secret == "test_secret"
    
    def test_submit_asr_task_valid(self, asr_service, test_audio_file):
        """测试提交有效的 ASR 任务"""
        result = asr_service.submit_asr_task(
            audio_file_path=test_audio_file,
            language="zh-CN"
        )
        
        assert "taskId" in result
        assert "status" in result
        assert result["status"] == "processing"
        assert result["language"] == "zh-CN"
        assert result["audioPath"] == test_audio_file
    
    def test_submit_asr_task_invalid_file(self, asr_service):
        """测试提交不存在的音频文件"""
        with pytest.raises(ValueError) as exc_info:
            asr_service.submit_asr_task(
                audio_file_path="/nonexistent/path/audio.mp3",
                language="zh-CN"
            )
        assert "音频文件不存在" in str(exc_info.value)
    
    def test_submit_asr_task_unsupported_language(self, asr_service, test_audio_file):
        """测试不支持的语言（应降级为 zh-CN）"""
        result = asr_service.submit_asr_task(
            audio_file_path=test_audio_file,
            language="xx-XX"  # 不支持的语言
        )
        
        assert result["language"] == "zh-CN"  # 应降级为默认语言
    
    def test_query_asr_result(self, asr_service):
        """测试查询 ASR 结果"""
        task_id = "asr_test_123456"
        result = asr_service.query_asr_result(task_id)
        
        assert result["taskId"] == task_id
        assert result["status"] == "completed"
        assert result["progress"] == 100
        assert "result" in result
        assert "sentences" in result["result"]
    
    def test_generate_srt(self, asr_service, tmp_path):
        """测试生成 SRT 字幕文件"""
        result_data = {
            "result": {
                "sentences": [
                    {"start_time": 0, "end_time": 2000, "text": "第一句"},
                    {"start_time": 2000, "end_time": 5000, "text": "第二句"},
                    {"start_time": 5000, "end_time": 8000, "text": "第三句"}
                ]
            }
        }
        
        output_path = str(tmp_path / "test.srt")
        asr_service.generate_srt(result_data, output_path)
        
        # 验证文件存在
        assert os.path.exists(output_path)
        
        # 验证内容格式
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "1" in content
        assert "00:00:00,000 --> 00:00:02,000" in content
        assert "第一句" in content
        assert "2" in content
        assert "00:00:02,000 --> 00:00:05,000" in content
        assert "第二句" in content
    
    def test_generate_vtt(self, asr_service, tmp_path):
        """测试生成 VTT 字幕文件"""
        result_data = {
            "result": {
                "sentences": [
                    {"start_time": 0, "end_time": 2000, "text": "First sentence"},
                    {"start_time": 2000, "end_time": 5000, "text": "Second sentence"}
                ]
            }
        }
        
        output_path = str(tmp_path / "test.vtt")
        asr_service.generate_vtt(result_data, output_path)
        
        # 验证文件存在
        assert os.path.exists(output_path)
        
        # 验证内容格式
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "WEBVTT" in content
        assert "00:00:00.000 --> 00:00:02.000" in content
        assert "First sentence" in content
    
    def test_ms_to_srt_time(self, asr_service):
        """测试毫秒转 SRT 时间格式"""
        assert asr_service._ms_to_srt_time(0) == "00:00:00,000"
        assert asr_service._ms_to_srt_time(1500) == "00:00:01,500"
        assert asr_service._ms_to_srt_time(65000) == "00:01:05,000"
        assert asr_service._ms_to_srt_time(3661000) == "01:01:01,000"
    
    def test_ms_to_vtt_time(self, asr_service):
        """测试毫秒转 VTT 时间格式"""
        assert asr_service._ms_to_vtt_time(0) == "00:00:00.000"
        assert asr_service._ms_to_vtt_time(1500) == "00:00:01.500"
        assert asr_service._ms_to_vtt_time(65000) == "00:01:05.000"
        assert asr_service._ms_to_vtt_time(3661000) == "01:01:01.000"
    
    @pytest.mark.asyncio
    async def test_process_asr_full_flow(self, asr_service, test_audio_file, tmp_path):
        """测试完整的 ASR 处理流程"""
        # 修改字幕输出目录到临时目录
        asr_service.subtitles_dir = str(tmp_path)
        
        result = await asr_service.process_asr(
            audio_id="test_audio_001",
            audio_path=test_audio_file,
            language="zh-CN",
            output_format="srt"
        )
        
        assert "subtitleId" in result
        assert "fileName" in result
        assert result["fileName"].endswith(".srt")
        assert "filePath" in result
        assert os.path.exists(result["filePath"])
        assert result["format"] == "srt"
        assert result["language"] == "zh-CN"
    
    @pytest.mark.asyncio
    async def test_process_asr_vtt_format(self, asr_service, test_audio_file, tmp_path):
        """测试 VTT 格式输出"""
        asr_service.subtitles_dir = str(tmp_path)
        
        result = await asr_service.process_asr(
            audio_id="test_audio_002",
            audio_path=test_audio_file,
            language="en-US",
            output_format="vtt"
        )
        
        assert result["fileName"].endswith(".vtt")
        assert result["format"] == "vtt"
        assert result["language"] == "en-US"
    
    def test_empty_sentences_fallback(self, asr_service, tmp_path):
        """测试空识别结果的降级处理"""
        result_data = {"result": {"sentences": []}}
        output_path = str(tmp_path / "empty.srt")
        
        output = asr_service.generate_srt(result_data, output_path)
        
        assert os.path.exists(output)
        with open(output, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 应包含默认字幕内容
        assert "语音识别结果" in content


class TestASRServiceIntegration:
    """ASR 服务集成测试"""
    
    def test_audio_service_integration(self):
        """测试 AudioService 与 ASR 服务的集成"""
        from src.services.audio_service import AudioService
        
        # 创建 AudioService 实例
        audio_service = AudioService()
        
        # 验证 ASR 服务已初始化
        assert hasattr(audio_service, 'asr_service')
        # 即使没有配置密钥，服务实例也应存在（可能为 None 或降级模式）
    
    def test_supported_languages(self):
        """测试支持的语言列表"""
        service = AliyunASRService()
        
        expected_languages = ["zh-CN", "en-US", "zh-TW", "ja-JP", "ko-KR"]
        for lang in expected_languages:
            assert lang in service.supported_languages


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
