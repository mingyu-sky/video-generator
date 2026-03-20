# Video Generator API 文档

**版本**: v3.0  
**最后更新**: 2026-03-21  
**状态**: ✅ 阶段一已完成 (v1.3.0)  
**变更**: 基于阶段一实现经验完善接口设计

---

## 基础信息

- **Base URL**: `http://localhost:15321/api/v1`
- **认证方式**: 无 (v1.3.0 版本)
- **数据格式**: JSON
- **CORS**: 允许所有来源
- **GitHub**: https://github.com/mingyu-sky/video-generator

---

## 接口总览

| 模块 | 接口数 | 已完成 | 状态 |
|------|--------|--------|------|
| 文件管理 | 6 | 6 | ✅ |
| 视频处理 | 8 | 8 | ✅ |
| 音频处理 | 2 | 0 | ⏳ 阶段二 |
| 任务管理 | 3 | 2 | ⚠️ 部分完成 |
| 素材库 | 2 | 0 | ⏳ 阶段三 |
| 系统 | 2 | 0 | ⏳ |
| **总计** | **23** | **16** | **70%** |

---

## 一、文件管理模块 ✅

### 1.1 上传文件

#### POST /files/upload

上传视频/音频/图片文件

**请求**
```http
POST /api/v1/files/upload
Content-Type: multipart/form-data

file: <file>
type: video | audio | image
```

**响应**
```json
{
  "code": 200,
  "data": {
    "fileId": "550e8400-e29b-41d4-a716-446655440000",
    "fileName": "video.mp4",
    "fileSize": 1048576,
    "fileType": "video",
    "duration": 30.5,
    "format": "mp4",
    "resolution": "1920x1080",
    "uploadTime": "2026-03-21T10:00:00Z",
    "downloadUrl": "/api/v1/files/550e8400-e29b-41d4-a716-446655440000/download"
  },
  "message": "上传成功"
}
```

**错误码**
| 码 | 说明 | HTTP 状态 |
|---|------|----------|
| 1001 | 文件格式不支持 | 400 |
| 1002 | 文件大小超限 (2GB) | 400 |
| 1003 | 文件损坏 | 400 |
| 1004 | 文件类型不匹配 | 400 |

**实现状态**: ✅ 已完成 (迭代 1)

---

### 1.2 获取文件列表

#### GET /files

获取已上传文件列表

**请求**
```http
GET /api/v1/files?type=video&page=1&pageSize=20
```

**响应**
```json
{
  "code": 200,
  "data": {
    "total": 50,
    "page": 1,
    "pageSize": 20,
    "files": [...]
  }
}
```

**实现状态**: ✅ 已完成 (迭代 1)

---

### 1.3 获取文件详情

#### GET /files/:fileId

**实现状态**: ✅ 已完成 (迭代 1)

---

### 1.4 下载文件

#### GET /files/:fileId/download

**实现状态**: ✅ 已完成 (迭代 1)

---

### 1.5 删除文件

#### DELETE /files/:fileId

**实现状态**: ✅ 已完成 (迭代 1)

---

### 1.6 批量删除文件

#### POST /files/batch-delete

**实现状态**: ✅ 已完成 (迭代 1)

---

## 二、视频处理模块 ✅

### 2.1 视频拼接

#### POST /video/concat

合并多个视频文件

**请求**
```json
{
  "videos": ["fileId1", "fileId2", "fileId3"],
  "outputName": "merged_video.mp4",
  "transition": "none"
}
```

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| videos | array | 是 | 视频 fileId 列表，至少 2 个 |
| outputName | string | 否 | 输出文件名 |
| transition | string | 否 | 转场效果：none/fade/dissolve，默认 none |

**响应**
```json
{
  "code": 202,
  "data": {
    "taskId": "task-uuid",
    "status": "pending",
    "estimatedTime": 60
  },
  "message": "任务已提交"
}
```

**实现状态**: ✅ 已完成 (迭代 3)

**测试用例**:
```python
def test_video_concat():
    # 13 个单元测试之一
    response = client.post("/video/concat", json={
        "videos": ["video1.mp4", "video2.mp4"],
        "outputName": "merged.mp4"
    })
    assert response.status_code == 202
    assert "taskId" in response.json()["data"]
```

---

### 2.2 添加文字特效

#### POST /video/text-overlay

在视频上添加文字

**请求**
```json
{
  "videoId": "fileId",
  "text": "Hello World",
  "position": {"x": 100, "y": 200},
  "style": {
    "fontSize": 24,
    "fontFamily": "Arial",
    "color": "#FFFFFF",
    "strokeColor": "#000000",
    "strokeWidth": 1
  },
  "duration": {"start": 0, "end": 5},
  "outputName": "video_with_text.mp4"
}
```

**实现状态**: ✅ 已完成 (迭代 3)

---

### 2.3 添加图片/动图水印

#### POST /video/image-overlay

**请求**
```json
{
  "videoId": "fileId",
  "imageId": "imageFileId",
  "position": {"x": 50, "y": 50},
  "opacity": 0.8,
  "duration": {"start": 0, "end": -1},
  "outputName": "video_with_watermark.mp4"
}
```

**参数说明**:
- `duration.end`: -1 表示直到视频结束

**实现状态**: ✅ 已完成 (迭代 3)

---

### 2.4 添加背景音乐

#### POST /video/add-music

**请求**
```json
{
  "videoId": "fileId",
  "musicId": "audioId",
  "startTime": 0,
  "endTime": -1,
  "volume": 0.3,
  "fade": {"in": 2.0, "out": 2.0},
  "loop": true,
  "outputName": "video_with_music.mp4"
}
```

**实现状态**: ✅ 已完成 (迭代 3)

---

### 2.5 添加配音

#### POST /video/add-voiceover

**请求**
```json
{
  "videoId": "fileId",
  "voiceoverId": "audioId",
  "alignMode": "start",
  "startTime": 0,
  "volume": 0.8,
  "outputName": "video_with_voiceover.mp4"
}
```

**实现状态**: ✅ 已完成 (迭代 3)

---

### 2.6 添加字幕

#### POST /video/add-subtitles

**请求**
```json
{
  "videoId": "fileId",
  "subtitleId": "srtFileId",
  "offset": 0,
  "style": {
    "fontSize": 20,
    "fontFamily": "思源黑体",
    "color": "#FFFFFF",
    "strokeColor": "#000000",
    "position": "bottom",
    "offsetY": -50
  },
  "outputName": "video_with_subtitles.mp4"
}
```

**实现状态**: ✅ 已完成 (迭代 3)

---

### 2.7 添加转场特效

#### POST /video/transition

**请求**
```json
{
  "videos": ["fileId1", "fileId2"],
  "transition": "fade",
  "duration": 1.0,
  "outputName": "video_with_transition.mp4"
}
```

**支持的转场**:
- `fade` - 淡入淡出
- `dissolve` - 溶解
- `wipe` - 擦除
- `slide` - 滑动

**实现状态**: ✅ 已完成 (迭代 3)

---

### 2.8 一站式处理（流水线）⭐

#### POST /video/process

一站式视频处理，支持多步骤流水线

**请求**
```json
{
  "videoId": "fileId",
  "steps": [
    {
      "type": "add_music",
      "params": {
        "musicId": "xxx",
        "volume": 0.3,
        "fade": {"in": 2.0, "out": 2.0}
      }
    },
    {
      "type": "add_voiceover",
      "params": {
        "voiceoverId": "xxx",
        "volume": 0.8,
        "alignMode": "start"
      }
    },
    {
      "type": "add_subtitles",
      "params": {
        "subtitleId": "xxx",
        "style": {"fontSize": 20}
      }
    }
  ],
  "outputName": "final_video.mp4"
}
```

**支持的步骤类型**:
- `add_music` - 添加背景音乐
- `add_voiceover` - 添加配音
- `add_subtitles` - 添加字幕
- `text_overlay` - 添加文字
- `image_overlay` - 添加图片水印

**响应**
```json
{
  "code": 202,
  "data": {
    "taskId": "task-uuid",
    "status": "pending",
    "totalSteps": 3,
    "currentStep": 0
  }
}
```

**优势**:
- ✅ 一次 API 调用完成多个处理步骤
- ✅ 保证原子性（要么全部成功，要么全部失败）
- ✅ 减少网络往返

**实现状态**: ✅ 已完成 (迭代 3)

**代码示例**:
```python
# Python SDK 示例
from video_generator import VideoClient

client = VideoClient(base_url="http://localhost:15321")

# 一站式处理
task = client.process_video(
    video_id="video-123",
    steps=[
        {"type": "add_music", "params": {"music_id": "music-456", "volume": 0.3}},
        {"type": "add_voiceover", "params": {"voiceover_id": "voice-789"}},
        {"type": "add_subtitles", "params": {"subtitle_id": "sub-000"}}
    ],
    output_name="final.mp4"
)

# 查询进度
result = client.wait_for_task(task["taskId"], timeout=300)
print(f"下载链接：{result['downloadUrl']}")
```

---

## 三、音频处理模块 ⏳

### 3.1 AI 配音生成

#### POST /audio/voiceover

使用 Edge TTS 生成配音

**请求**
```json
{
  "text": "这是配音文本",
  "voice": "zh-CN-XiaoxiaoNeural",
  "speed": 1.0,
  "volume": 1.0,
  "outputName": "voiceover.mp3"
}
```

**可用音色**:
| 音色代码 | 说明 | 适用场景 |
|----------|------|----------|
| zh-CN-XiaoxiaoNeural | 女声，温暖 | 解说、旁白 |
| zh-CN-YunxiNeural | 男声，沉稳 | 新闻、纪录片 |
| zh-CN-XiaoyiNeural | 女声，活泼 | 广告、促销 |
| en-US-JennyNeural | 女声，英语 | 英文内容 |

**实现状态**: ⏳ 阶段二开发

---

### 3.2 ASR 字幕生成

#### POST /audio/asr

使用阿里云 ASR 生成字幕

**实现状态**: ⏳ 阶段二开发

---

## 四、任务管理模块 ⚠️

### 4.1 查询任务进度

#### GET /tasks/:taskId

**请求**
```http
GET /api/v1/tasks/:taskId
```

**响应**
```json
{
  "code": 200,
  "data": {
    "taskId": "task-uuid",
    "type": "video/add-music",
    "status": "processing",
    "progress": 50,
    "message": "正在处理音频...",
    "createdAt": "2026-03-21T10:00:00Z",
    "updatedAt": "2026-03-21T10:01:00Z",
    "result": {
      "outputId": "outputFileId",
      "downloadUrl": "/api/v1/files/outputFileId/download"
    },
    "error": {
      "code": 0,
      "message": ""
    }
  }
}
```

**状态枚举**:
- `pending` - 等待处理
- `processing` - 处理中
- `completed` - 完成
- `failed` - 失败
- `cancelled` - 已取消

**实现状态**: ✅ 已完成 (迭代 2)

---

### 4.2 取消任务

#### DELETE /tasks/:taskId

**实现状态**: ⏳ 待开发

---

### 4.3 批量查询任务

#### POST /tasks/batch-query

**实现状态**: ⏳ 待开发

---

## 五、素材库模块 ⏳

### 5.1 获取音乐列表

#### GET /materials/music

**实现状态**: ⏳ 阶段三开发

---

### 5.2 获取模板列表

#### GET /materials/templates

**实现状态**: ⏳ 阶段三开发

---

## 六、系统模块 ⏳

### 6.1 健康检查

#### GET /health

**实现状态**: ⏳ 待开发

---

### 6.2 系统信息

#### GET /system/info

**实现状态**: ⏳ 待开发

---

## 七、错误响应格式

### 统一错误响应

```json
{
  "code": 1001,
  "message": "文件格式不支持",
  "details": "仅支持 MP4, MOV, AVI 格式",
  "timestamp": "2026-03-21T10:00:00Z",
  "path": "/api/v1/files/upload"
}
```

### 完整错误码表

| 错误码 | 说明 | HTTP 状态 | 模块 |
|--------|------|----------|------|
| **文件管理 (1000-1999)** |
| 1001 | 文件格式不支持 | 400 | 文件 |
| 1002 | 文件大小超限 | 400 | 文件 |
| 1003 | 文件损坏 | 400 | 文件 |
| 1004 | 文件类型不匹配 | 400 | 文件 |
| 1005 | 文件不存在 | 404 | 文件 |
| **视频处理 (2000-2999)** |
| 2001 | 视频数量不足 | 400 | 视频 |
| 2002 | 视频格式不一致 | 400 | 视频 |
| 2003 | 时间范围超出视频长度 | 400 | 视频 |
| 2010 | 文本过长 | 400 | 配音 |
| 2011 | 音色不支持 | 400 | 配音 |
| 2012 | 配音生成失败 | 500 | 配音 |
| 2020 | ASR 识别失败 | 500 | 字幕 |
| 2021 | 音频格式不支持 | 400 | 字幕 |
| **任务管理 (3000-3999)** |
| 3001 | 任务不存在 | 404 | 任务 |
| 3002 | 任务已完成，无法取消 | 400 | 任务 |
| **系统错误 (5000-5999)** |
| 5001 | 服务器资源不足 | 503 | 系统 |
| 5002 | 处理超时 | 408 | 系统 |
| 5003 | 内部服务器错误 | 500 | 系统 |
| 9999 | 未知错误 | 500 | 系统 |

---

## 八、开发进度

### 阶段一 ✅ (v1.3.0 - 已完成)

| 接口 | 优先级 | 状态 | Git Commit |
|------|--------|------|------------|
| **文件管理** |
| POST /files/upload | P0 | ✅ | 迭代 1 |
| GET /files | P0 | ✅ | 迭代 1 |
| GET /files/:id | P0 | ✅ | 迭代 1 |
| GET /files/:id/download | P0 | ✅ | 迭代 1 |
| DELETE /files/:id | P0 | ✅ | 迭代 1 |
| POST /files/batch-delete | P0 | ✅ | 迭代 1 |
| **任务管理** |
| GET /tasks/:id | P0 | ✅ | 迭代 2 |
| **视频处理** |
| POST /video/concat | P0 | ✅ | 迭代 3 |
| POST /video/text-overlay | P0 | ✅ | 迭代 3 |
| POST /video/image-overlay | P0 | ✅ | 迭代 3 |
| POST /video/add-music | P0 | ✅ | 迭代 3 |
| POST /video/add-voiceover | P0 | ✅ | 迭代 3 |
| POST /video/transition | P0 | ✅ | 迭代 3 |
| POST /video/add-subtitles | P0 | ✅ | 迭代 3 |
| POST /video/process | P0 | ✅ | 迭代 3 |

**测试覆盖**: 13 个单元测试，100% 通过率  
**Git Tag**: v1.3.0  
**发布链接**: https://github.com/mingyu-sky/video-generator/releases/tag/v1.3.0

---

### 阶段二 ⏳ (计划 v2.0)

| 接口 | 优先级 | 预计工时 | 状态 |
|------|--------|----------|------|
| POST /audio/voiceover | P0 | 1.5 人天 | ⏳ |
| POST /audio/asr | P1 | 1.5 人天 | ⏳ |
| DELETE /tasks/:id | P0 | 0.5 人天 | ⏳ |
| POST /tasks/batch-query | P1 | 0.5 人天 | ⏳ |

---

## 九、API 设计规范

### RESTful 规范

1. **资源命名**: 使用名词复数 (`/files`, `/videos`)
2. **HTTP 方法**:
   - GET - 查询
   - POST - 创建/处理
   - PUT - 更新
   - DELETE - 删除
3. **状态码**:
   - 200 - 成功
   - 202 - 已接受（异步任务）
   - 400 - 客户端错误
   - 404 - 资源不存在
   - 500 - 服务器错误
4. **版本控制**: `/api/v1/` 前缀

### 异步任务规范

**提交任务响应**:
```json
{
  "code": 202,
  "data": {
    "taskId": "xxx",
    "status": "pending",
    "estimatedTime": 60
  }
}
```

**查询任务响应**:
```json
{
  "code": 200,
  "data": {
    "taskId": "xxx",
    "status": "completed",
    "progress": 100,
    "result": {
      "outputId": "xxx",
      "downloadUrl": "/api/v1/files/xxx/download"
    }
  }
}
```

### 阶段一经验总结

**最佳实践**:
1. ✅ 所有耗时操作使用异步任务模式
2. ✅ 统一错误响应格式
3. ✅ 详细的错误码便于排查
4. ✅ 单元测试覆盖核心逻辑

**待改进**:
1. ⚠️ 添加 WebSocket 实时通知
2. ⚠️ 实现任务取消功能
3. ⚠️ 添加请求限流
4. ⚠️ 完善日志记录

---

## 十、快速开始

### 安装依赖

```bash
cd /home/admin/.openclaw/workspace/video-generator
source venv/bin/activate
pip install -r requirements.txt
```

### 启动服务

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 15321 --reload
```

### 访问文档

- Swagger UI: http://localhost:15321/docs
- ReDoc: http://localhost:15321/redoc

### 运行测试

```bash
pytest tests/test_video_processing.py -v
```

**预期输出**:
```
tests/test_video_processing.py::test_video_concat PASSED
tests/test_video_processing.py::test_text_overlay PASSED
tests/test_video_processing.py::test_image_overlay PASSED
tests/test_video_processing.py::test_add_music PASSED
tests/test_video_processing.py::test_add_voiceover PASSED
tests/test_video_processing.py::test_add_subtitles PASSED
tests/test_video_processing.py::test_transition PASSED
tests/test_video_processing.py::test_process_pipeline PASSED
...
13 passed in 2.34s
```

---

**维护人**: 后端开发团队  
**最后更新**: 2026-03-21 04:15 CST  
**下一版本**: v2.0 (阶段二 - AI 短剧能力)
