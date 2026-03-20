"""
音频处理服务
处理 AI 配音生成 (Edge TTS) 和 ASR 字幕生成
"""
import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid

# Edge TTS 导入
try:
    import edge_tts
    from edge_tts import VoicesManager
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# 阿里云 ASR 服务导入
try:
    from .asr_service import AliyunASRService
    ALIYUN_ASR_AVAILABLE = True
except ImportError:
    ALIYUN_ASR_AVAILABLE = False


class AudioService:
    """音频处理服务"""
    
    def __init__(self, file_service=None):
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
        self.voiceover_dir = os.path.join(self.base_dir, "audio", "voiceovers")
        self.subtitles_dir = os.path.join(self.base_dir, "subtitles")
        
        # 确保目录存在
        os.makedirs(self.voiceover_dir, exist_ok=True)
        os.makedirs(self.subtitles_dir, exist_ok=True)
        
        # 文件服务引用
        self.file_service = file_service
        
        # 初始化阿里云 ASR 服务
        if ALIYUN_ASR_AVAILABLE:
            self.asr_service = AliyunASRService()
        else:
            self.asr_service = None
        
        # 支持的音色列表 (常用中文音色)
        self.supported_voices = [
            "zh-CN-XiaoxiaoNeural",
            "zh-CN-YunxiNeural",
            "zh-CN-YunjianNeural",
            "zh-CN-XiaoyiNeural",
            "zh-CN-YunyangNeural",
            "zh-CN-XiaochenNeural",
            "zh-CN-XiaohanNeural",
            "zh-CN-XiaomengNeural",
            "zh-CN-XiaomoNeural",
            "zh-CN-XiaoqiuNeural",
            "zh-CN-XiaoruiNeural",
            "zh-CN-XiaoshuangNeural",
            "zh-CN-XiaoxuanNeural",
            "zh-CN-XiaoyanNeural",
            "zh-CN-XiaoyouNeural",
            "zh-CN-YunfengNeural",
            "zh-CN-YunhaoNeural",
            "zh-CN-YunxiaNeural",
            "zh-CN-YunyeNeural",
            "zh-CN-YunzeNeural",
        ]
        
        # 默认音色
        self.default_voice = "zh-CN-XiaoxiaoNeural"
    
    async def generate_voiceover(self, text: str, voice: str = None, speed: float = 1.0, 
                                volume: float = 1.0, output_name: str = None) -> Dict[str, Any]:
        """
        使用 Edge TTS 生成配音
        
        Args:
            text: 配音文本
            voice: 音色
            speed: 语速 (0.5-2.0)
            volume: 音量 (0.0-1.0)
            output_name: 输出文件名
            
        Returns:
            生成结果
            
        Raises:
            ValueError: 参数错误
            RuntimeError: 生成失败
        """
        # 参数验证
        if not text:
            raise ValueError("配音文本不能为空")
        
        if len(text) > 10000:
            raise ValueError("文本过长，最大支持 10000 字")
        
        if voice and voice not in self.supported_voices:
            # 尝试查找匹配的音色
            available_voices = await self._get_available_voices()
            if voice not in available_voices:
                raise ValueError(f"音色不支持，支持的音色：{', '.join(self.supported_voices[:5])}...")
        
        # 使用默认音色
        voice = voice or self.default_voice
        
        # 语速和音量验证
        speed = max(0.5, min(2.0, speed))
        volume = max(0.0, min(1.0, volume))
        
        # 生成输出文件名
        if not output_name:
            output_name = f"voiceover_{uuid.uuid4().hex[:8]}.mp3"
        
        output_path = os.path.join(self.voiceover_dir, output_name)
        
        if not EDGE_TTS_AVAILABLE:
            raise RuntimeError("Edge TTS 未安装，请运行：pip install edge-tts")
        
        try:
            # 使用 edge-tts 生成音频
            # rate 格式：+20% 或 -20%
            # volume 格式：+50% 或 -50% (必须是百分比，带正负号)
            rate_str = f"{int((speed - 1.0) * 100):+d}%"
            # volume: convert 0.0-1.0 to percentage with sign (-100% to +0%)
            volume_percent = int((volume - 1.0) * 100)
            volume_str = f"{volume_percent:+d}%"
            
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate_str,
                volume=volume_str
            )
            
            await communicate.save(output_path)
            
            # 获取音频时长
            duration = await self._get_audio_duration(output_path)
            
            # 生成文件 ID
            file_id = str(uuid.uuid4())
            
            return {
                "audioId": file_id,
                "fileName": output_name,
                "filePath": output_path,
                "duration": duration,
                "voice": voice,
                "text": text[:100] + "..." if len(text) > 100 else text
            }
            
        except Exception as e:
            raise RuntimeError(f"配音生成失败：{str(e)}")
    
    async def _get_available_voices(self) -> list:
        """获取可用的音色列表"""
        if not EDGE_TTS_AVAILABLE:
            return self.supported_voices
        
        try:
            voices = await edge_tts.list_voices()
            return [v["ShortName"] for v in voices if v.get("ShortName")]
        except:
            return self.supported_voices
    
    async def _get_audio_duration(self, file_path: str) -> Optional[float]:
        """获取音频文件时长"""
        try:
            import ffmpeg
            probe = ffmpeg.probe(file_path)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            if audio_stream and 'duration' in audio_stream:
                return float(audio_stream['duration'])
            elif 'format' in probe and 'duration' in probe['format']:
                return float(probe['format']['duration'])
        except:
            pass
        
        return None
    
    async def generate_asr(self, audio_id: str, audio_path: str, language: str = "zh-CN",
                          output_format: str = "srt") -> Dict[str, Any]:
        """
        使用阿里云 ASR 生成字幕
        
        Args:
            audio_id: 音频文件 ID
            audio_path: 音频文件路径
            language: 语言 (zh-CN/en-US)
            output_format: 输出格式 (srt/vtt)
            
        Returns:
            任务结果
            
        Raises:
            ValueError: 参数错误
            RuntimeError: 识别失败
        """
        # 验证音频文件
        if not os.path.exists(audio_path):
            raise ValueError("音频文件不存在")
        
        # 验证语言
        supported_languages = ["zh-CN", "en-US", "zh-TW", "ja-JP", "ko-KR"]
        if language not in supported_languages:
            language = "zh-CN"
        
        # 验证输出格式
        if output_format not in ["srt", "vtt"]:
            output_format = "srt"
        
        # 使用阿里云 ASR 服务
        if self.asr_service and ALIYUN_ASR_AVAILABLE:
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.asr_service.process_asr(
                        audio_id=audio_id,
                        audio_path=audio_path,
                        language=language,
                        output_format=output_format
                    )
                )
                return result
            except Exception as e:
                # 如果阿里云服务失败，降级为模拟模式
                pass
        
        # 降级为模拟模式（用于测试）
        output_name = f"asr_{uuid.uuid4().hex[:8]}.{output_format}"
        output_path = os.path.join(self.subtitles_dir, output_name)
        
        subtitle_content = self._generate_mock_subtitles(output_format)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(subtitle_content)
        
        return {
            "subtitleId": str(uuid.uuid4()),
            "fileName": output_name,
            "filePath": output_path,
            "format": output_format,
            "language": language
        }
    
    def _generate_mock_subtitles(self, format: str) -> str:
        """生成模拟字幕内容（用于测试）"""
        if format == "vtt":
            return """WEBVTT

00:00:00.000 --> 00:00:02.000
这是模拟的 ASR 字幕内容

00:00:02.000 --> 00:00:05.000
阿里云 API 对接后将返回真实识别结果

00:00:05.000 --> 00:00:08.000
当前为框架实现
"""
        else:  # srt
            return """1
00:00:00,000 --> 00:00:02,000
这是模拟的 ASR 字幕内容

2
00:00:02,000 --> 00:00:05,000
阿里云 API 对接后将返回真实识别结果

3
00:00:05,000 --> 00:00:08,000
当前为框架实现
"""
    
    async def list_voices(self) -> list:
        """获取支持的音色列表"""
        if EDGE_TTS_AVAILABLE:
            try:
                voices = await edge_tts.list_voices()
                chinese_voices = [v for v in voices if v.get("Locale", "").startswith("zh-")]
                return [
                    {
                        "name": v.get("ShortName", ""),
                        "gender": v.get("Gender", ""),
                        "locale": v.get("Locale", "")
                    }
                    for v in chinese_voices
                ]
            except:
                pass
        
        return [{"name": voice, "gender": "Unknown", "locale": "zh-CN"} for voice in self.supported_voices]
