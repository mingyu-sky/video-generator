"""
视频生成系统测试用例
"""
import pytest
import os
from pathlib import Path
from src.video_generator import (
    VideoGenerator, 
    AudioConfig, 
    SubtitleConfig, 
    EffectConfig
)


class TestAudioProcessor:
    """音频处理测试"""
    
    def test_add_background_music(self, sample_video, sample_audio):
        """测试添加背景音乐"""
        generator = VideoGenerator()
        video = generator.load_video(sample_video)
        result = generator.add_background_music(video, sample_audio, volume=0.3)
        
        assert result is not None
        assert result.audio is not None
        assert result.duration >= video.duration
    
    def test_add_voiceover(self, sample_video, sample_audio):
        """测试添加配音"""
        generator = VideoGenerator()
        video = generator.load_video(sample_video)
        result = generator.add_voiceover(video, sample_audio, volume=0.8)
        
        assert result is not None
        assert result.audio is not None
    
    def test_music_fade_in_out(self, sample_video, sample_audio):
        """测试音乐淡入淡出"""
        generator = VideoGenerator()
        video = generator.load_video(sample_video)
        result = generator.add_background_music(
            video, sample_audio, 
            fade_in=3.0, fade_out=3.0
        )
        
        assert result is not None


class TestSubtitleProcessor:
    """字幕处理测试"""
    
    def test_add_srt_subtitles(self, sample_video, sample_srt):
        """测试添加 SRT 字幕"""
        generator = VideoGenerator()
        video = generator.load_video(sample_video)
        
        config = SubtitleConfig(srt_file=sample_srt)
        result = generator.add_subtitles(video, sample_srt, config)
        
        assert result is not None
        assert result.duration == video.duration
    
    def test_subtitle_position(self, sample_video, sample_srt):
        """测试字幕位置"""
        generator = VideoGenerator()
        video = generator.load_video(sample_video)
        
        # 底部位置
        config_bottom = SubtitleConfig(srt_file=sample_srt, position='bottom', offset_y=-50)
        result_bottom = generator.add_subtitles(video, sample_srt, config_bottom)
        
        assert result_bottom is not None


class TestEffectProcessor:
    """特效处理测试"""
    
    def test_add_intro(self, sample_video, sample_intro):
        """测试添加片头"""
        generator = VideoGenerator()
        video = generator.load_video(sample_video)
        result = generator.add_intro(video, sample_intro)
        
        # 总时长应该是片头 + 原视频
        expected_duration = sample_intro.duration + video.duration
        assert abs(result.duration - expected_duration) < 0.1
    
    def test_add_outro(self, sample_video, sample_outro):
        """测试添加片尾"""
        generator = VideoGenerator()
        video = generator.load_video(sample_video)
        result = generator.add_outro(video, sample_outro)
        
        expected_duration = video.duration + sample_outro.duration
        assert abs(result.duration - expected_duration) < 0.1
    
    def test_add_blur_effect(self, sample_video):
        """测试模糊特效"""
        generator = VideoGenerator()
        video = generator.load_video(sample_video)
        result = generator.add_effect_at_time(
            video, 'blur', start_time=1.0, duration=2.0
        )
        
        assert result is not None


class TestIntegration:
    """集成测试"""
    
    def test_full_pipeline(self, sample_video, sample_audio, sample_srt, sample_intro, sample_outro):
        """测试完整处理流程"""
        generator = VideoGenerator()
        
        audio_config = AudioConfig(
            background_music=sample_audio,
            music_volume=0.3
        )
        
        subtitle_config = SubtitleConfig(srt_file=sample_srt)
        
        effect_config = EffectConfig(
            intro_file=sample_intro,
            outro_file=sample_outro
        )
        
        output_path = "/tmp/test_output.mp4"
        
        result = generator.process(
            input_video=sample_video,
            output_video=output_path,
            audio_config=audio_config,
            subtitle_config=subtitle_config,
            effect_config=effect_config
        )
        
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0


class TestEdgeCases:
    """边界条件测试"""
    
    def test_music_longer_than_video(self, sample_video, long_audio):
        """测试音乐时长超过视频"""
        generator = VideoGenerator()
        video = generator.load_video(sample_video)
        result = generator.add_background_music(video, long_audio)
        
        assert result.duration == video.duration
    
    def test_music_shorter_than_video(self, sample_video, short_audio):
        """测试音乐时长短于视频"""
        generator = VideoGenerator()
        video = generator.load_video(sample_video)
        result = generator.add_background_music(video, short_audio)
        
        # 应该循环或截断处理
        assert result.duration >= video.duration * 0.9
    
    def test_corrupted_video(self, corrupted_file):
        """测试损坏的视频文件"""
        generator = VideoGenerator()
        
        with pytest.raises(Exception):
            generator.load_video(corrupted_file)
    
    def test_missing_subtitle_file(self, sample_video):
        """测试缺失的字幕文件"""
        generator = VideoGenerator()
        video = generator.load_video(sample_video)
        
        config = SubtitleConfig(srt_file='/nonexistent/file.srt')
        
        with pytest.raises(FileNotFoundError):
            generator.add_subtitles(video, '/nonexistent/file.srt', config)


class TestPerformance:
    """性能测试"""
    
    def test_processing_speed(self, sample_video_1080p, sample_audio):
        """测试处理速度（1080p 基准）"""
        generator = VideoGenerator()
        
        import time
        start = time.time()
        
        video = generator.load_video(sample_video_1080p)
        result = generator.add_background_music(video, sample_audio)
        
        # 写入临时文件测试
        temp_output = "/tmp/perf_test.mp4"
        generator.render(result, temp_output, preset='ultrafast')
        
        elapsed = time.time() - start
        video_duration = sample_video_1080p.duration
        
        # 处理速度应该 >= 0.5x 实时
        assert elapsed < video_duration * 2.5


# Fixtures
@pytest.fixture
def sample_video():
    """示例视频"""
    return 'tests/assets/sample.mp4'


@pytest.fixture
def sample_audio():
    """示例音频"""
    return 'tests/assets/sample.mp3'


@pytest.fixture
def sample_srt():
    """示例字幕"""
    return 'tests/assets/sample.srt'


@pytest.fixture
def sample_intro():
    """示例片头"""
    return 'tests/assets/intro.mp4'


@pytest.fixture
def sample_outro():
    """示例片尾"""
    return 'tests/assets/outro.mp4'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
