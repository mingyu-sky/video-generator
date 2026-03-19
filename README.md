# Video Generator - 视频生成系统

基于 Python + MoviePy + FFmpeg 的视频批量生成工具。

## 功能特性

- ✅ 添加背景音乐（支持淡入淡出、音量调节）
- ✅ 添加配音（支持音画同步）
- ✅ 添加字幕（SRT 格式，支持样式定制）
- ✅ 添加片头片尾
- ✅ 时间轴特效（模糊、灰度、速度等）
- ✅ 批量处理支持

## 快速开始

### 安装依赖

```bash
# 系统依赖
sudo apt-get install -y ffmpeg

# Python 依赖
pip install -r requirements.txt
```

### 基础使用

```python
from video_generator import VideoGenerator, AudioConfig, SubtitleConfig

generator = VideoGenerator()

# 配置
audio_config = AudioConfig(
    background_music='bgm.mp3',
    music_volume=0.3
)

subtitle_config = SubtitleConfig(
    srt_file='subtitles.srt'
)

# 处理
output = generator.process(
    input_video='input.mp4',
    output_video='output.mp4',
    audio_config=audio_config,
    subtitle_config=subtitle_config
)
```

### CLI 使用

```bash
python src/video_generator.py \
  -i input.mp4 \
  -o output.mp4 \
  -m bgm.mp3 \
  -s subtitles.srt
```

## 项目结构

```
video-generator/
├── src/
│   └── video_generator.py    # 核心模块
├── tests/
│   └── test_video_generator.py  # 测试用例
├── examples/
│   └── basic_usage.py        # 使用示例
├── requirements.txt          # 依赖清单
└── README.md                 # 本文档
```

## API 文档

### VideoGenerator

主处理类，提供完整的视频处理能力。

#### 方法

- `load_video(path)` - 加载视频文件
- `add_background_music(video, music_path, volume, fade_in, fade_out)` - 添加背景音乐
- `add_voiceover(video, voiceover_path, volume, align_mode)` - 添加配音
- `add_subtitles(video, srt_path, config)` - 添加字幕
- `add_intro(video, intro_path, fade_duration)` - 添加片头
- `add_outro(video, outro_path, fade_duration)` - 添加片尾
- `add_effect_at_time(video, effect_type, start_time, duration, **params)` - 添加特效
- `render(video, output_path, **kwargs)` - 渲染输出
- `process(input_video, output_video, **configs)` - 完整处理流程

### 配置类

#### AudioConfig

```python
AudioConfig(
    background_music='bgm.mp3',  # 背景音乐文件
    music_volume=0.3,             # 音量 0-1
    voiceover='voice.mp3',        # 配音文件
    voiceover_volume=0.8,         # 配音音量
    fade_in=2.0,                  # 淡入时长 (秒)
    fade_out=2.0                  # 淡出时长 (秒)
)
```

#### SubtitleConfig

```python
SubtitleConfig(
    srt_file='subtitles.srt',     # SRT 字幕文件
    font='思源黑体 Bold',          # 字体
    font_size=24,                 # 字号
    color='white',                # 颜色
    stroke_color='black',         # 描边颜色
    position='bottom',            # 位置
    offset_y=-50                  # Y 轴偏移
)
```

#### EffectConfig

```python
EffectConfig(
    intro_file='intro.mp4',       # 片头文件
    outro_file='outro.mp4',       # 片尾文件
    effects=[                     # 特效列表
        {'type': 'blur', 'start_time': 10.0, 'duration': 2.0},
        {'type': 'grayscale', 'start_time': 20.0, 'duration': 3.0}
    ]
)
```

## 运行测试

```bash
# 安装测试依赖
pip install pytest

# 运行测试
pytest tests/test_video_generator.py -v
```

## 性能优化

### GPU 加速

```bash
# 安装 NVIDIA 驱动和 CUDA
sudo apt-get install -y nvidia-driver-525 nvidia-cuda-toolkit

# 使用 GPU 编码
generator.render(video, output, codec='h264_nvenc')
```

### 批量处理

```python
import concurrent.futures

generator = VideoGenerator()
tasks = [...]  # 任务列表

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_task, tasks))
```

## 技术栈

- **Python** 3.10+
- **MoviePy** - 视频编辑
- **FFmpeg** - 编解码
- **PyDub** - 音频处理
- **pysubs2** - 字幕解析

## 许可证

MIT License

## 联系方式

有问题请提 Issue 或联系开发团队。
