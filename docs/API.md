# Video Generator API 文档

**版本**: v2.0  
**最后更新**: 2026-03-21  
**状态**: ⏳ 待开发  
**变更**: 补充文件管理、任务取消、一站式处理等接口

---

## 基础信息

- **Base URL**: `http://localhost:15321/api/v1`
- **认证方式**: 无 (v3.1 版本移除认证)
- **数据格式**: JSON
- **CORS**: 允许所有来源

---

## 接口总览

| 模块 | 接口数 | 说明 |
|------|--------|------|
| 文件管理 | 6 | 上传、下载、列表、删除 |
| 视频处理 | 8 | 拼接、特效、字幕等 |
| 音频处理 | 2 | AI 配音、ASR 字幕 |
| 任务管理 | 3 | 查询、取消 |
| 素材库 | 2 | 音乐、模板 |
| 系统 | 2 | 健康检查、系统信息 |
| **总计** | **23** | |

---

## 一、文件管理模块

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

---

### 1.2 获取文件列表

#### GET /files

获取已上传文件列表

**请求**
```http
GET /api/v1/files?type=video&page=1&pageSize=20
```

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 否 | video/audio/image，不传则返回全部 |
| page | integer | 否 | 页码，默认 1 |
| pageSize | integer | 否 | 每页数量，默认 20，最大 100 |
| sortBy | string | 否 | uploadTime/fileName，默认 uploadTime |
| order | string | 否 | asc/desc，默认 desc |

**响应**
```json
{
  "code": 200,
  "data": {
    "total": 50,
    "page": 1,
    "pageSize": 20,
    "files": [
      {
        "fileId": "uuid-1",
        "fileName": "video1.mp4",
        "fileSize": 1048576,
        "fileType": "video",
        "duration": 30.5,
        "uploadTime": "2026-03-21T10:00:00Z"
      }
    ]
  },
  "message": "success"
}
```

---

### 1.3 获取文件详情

#### GET /files/:fileId

获取单个文件详细信息

**请求**
```http
GET /api/v1/files/:fileId
```

**响应**
```json
{
  "code": 200,
  "data": {
    "fileId": "uuid",
    "fileName": "video.mp4",
    "fileSize": 1048576,
    "fileType": "video",
    "duration": 30.5,
    "format": "mp4",
    "resolution": "1920x1080",
    "uploadTime": "2026-03-21T10:00:00Z",
    "downloadUrl": "/api/v1/files/uuid/download",
    "thumbnailUrl": "/api/v1/files/uuid/thumbnail"
  }
}
```

**错误码**
| 码 | 说明 |
|---|------|
| 1005 | 文件不存在 |

---

### 1.4 下载文件

#### GET /files/:fileId/download

下载文件

**请求**
```http
GET /api/v1/files/:fileId/download
```

**响应**
- Content-Type: application/octet-stream
- Content-Disposition: attachment; filename="video.mp4"

**错误码**
| 码 | 说明 |
|---|------|
| 1005 | 文件不存在 |

---

### 1.5 删除文件

#### DELETE /files/:fileId

删除单个文件

**请求**
```http
DELETE /api/v1/files/:fileId
```

**响应**
```json
{
  "code": 200,
  "message": "删除成功"
}
```

**错误码**
| 码 | 说明 |
|---|------|
| 1005 | 文件不存在 |

---

### 1.6 批量删除文件

#### POST /files/batch-delete

批量删除文件

**请求**
```json
{
  "fileIds": ["uuid-1", "uuid-2", "uuid-3"]
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "deleted": 3,
    "failed": 0
  },
  "message": "批量删除完成"
}
```

---

## 二、视频处理模块

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

**错误码**
| 码 | 说明 |
|---|------|
| 2001 | 视频数量不足 |
| 2002 | 视频格式不一致 |

---

### 2.2 添加文字特效

#### POST /video/text-overlay

在视频上添加文字

**请求**
```json
{
  "videoId": "fileId",
  "text": "Hello World",
  "position": {
    "x": 100,
    "y": 200
  },
  "style": {
    "fontSize": 24,
    "fontFamily": "Arial",
    "color": "#FFFFFF",
    "strokeColor": "#000000",
    "strokeWidth": 1
  },
  "duration": {
    "start": 0,
    "end": 5
  },
  "outputName": "video_with_text.mp4"
}
```

**响应**
```json
{
  "code": 202,
  "data": {
    "taskId": "task-uuid"
  }
}
```

**错误码**
| 码 | 说明 |
|---|------|
| 2003 | 时间范围超出视频长度 |

---

### 2.3 添加图片/动图水印

#### POST /video/image-overlay

**请求**
```json
{
  "videoId": "fileId",
  "imageId": "imageFileId",
  "position": {
    "x": 50,
    "y": 50
  },
  "opacity": 0.8,
  "duration": {
    "start": 0,
    "end": -1
  },
  "outputName": "video_with_watermark.mp4"
}
```

**参数说明**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| duration.start | number | 否 | 开始出现时间（秒），默认 0 |
| duration.end | number | 否 | 消失时间（秒），-1 表示直到视频结束 |

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
  "fade": {
    "in": 2.0,
    "out": 2.0
  },
  "loop": true,
  "outputName": "video_with_music.mp4"
}
```

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startTime | number | 否 | 从视频的第几秒开始播放（秒），默认 0 |
| endTime | number | 否 | 结束时间（秒），-1 表示直到视频结束 |
| volume | number | 否 | 音量，0.0-1.0，默认 0.3 |
| fade.in | number | 否 | 淡入时长（秒），默认 0 |
| fade.out | number | 否 | 淡出时长（秒），默认 0 |
| loop | boolean | 否 | 音乐时长不足时循环，默认 true |

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| loop | boolean | 否 | 音乐时长不足时循环，默认 true |

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

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| alignMode | string | 否 | start/center/end/custom，默认 start |
| startTime | number | 否 | 自定义开始时间（秒），alignMode=custom 时必填 |
| volume | number | 否 | 音量，0.0-1.0，默认 0.8 |

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

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| offset | number | 否 | 字幕整体时间偏移（秒），正数延迟，负数提前，默认 0 |

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

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| transition | string | 是 | fade/dissolve/wipe/slide |
| duration | number | 否 | 转场时长（秒），默认 1.0 |

---

### 2.8 一站式处理（流水线）

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

---

## 三、音频处理模块

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

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 配音文本，最大 10000 字 |
| voice | string | 否 | 音色，默认 zh-CN-XiaoxiaoNeural |
| speed | number | 否 | 语速，0.5-2.0，默认 1.0 |
| volume | number | 否 | 音量，0.0-1.0，默认 1.0 |

**响应**
```json
{
  "code": 200,
  "data": {
    "audioId": "audio-uuid",
    "duration": 10.5,
    "downloadUrl": "/api/v1/files/audio-uuid/download"
  },
  "message": "配音生成成功"
}
```

**错误码**
| 码 | 说明 |
|---|------|
| 2010 | 文本过长 |
| 2011 | 音色不支持 |
| 2012 | 配音生成失败 |

---

### 3.2 ASR 字幕生成

#### POST /audio/asr

使用阿里云 ASR 生成字幕

**请求**
```json
{
  "audioId": "fileId",
  "language": "zh-CN",
  "outputFormat": "srt"
}
```

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| language | string | 否 | zh-CN/en-US，默认 zh-CN |
| outputFormat | string | 否 | srt/vtt，默认 srt |

**响应**
```json
{
  "code": 202,
  "data": {
    "taskId": "task-uuid",
    "status": "pending"
  }
}
```

**任务完成后**:
- 字幕文件保存到 `uploads/subtitles/`
- 可通过 `GET /files/:fileId` 查询

**错误码**
| 码 | 说明 |
|---|------|
| 2020 | ASR 识别失败 |
| 2021 | 音频格式不支持 |

---

## 四、任务管理模块

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

---

### 4.2 取消任务

#### DELETE /tasks/:taskId

**请求**
```http
DELETE /api/v1/tasks/:taskId
```

**响应**
```json
{
  "code": 200,
  "message": "任务已取消"
}
```

**错误码**
| 码 | 说明 |
|---|------|
| 3001 | 任务不存在 |
| 3002 | 任务已完成，无法取消 |

---

### 4.3 批量查询任务

#### POST /tasks/batch-query

**请求**
```json
{
  "taskIds": ["task-1", "task-2", "task-3"]
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "tasks": [
      {
        "taskId": "task-1",
        "status": "completed",
        "progress": 100
      }
    ]
  }
}
```

---

## 五、素材库模块

### 5.1 获取音乐列表

#### GET /materials/music

**请求**
```http
GET /api/v1/materials/music?genre=pop&page=1
```

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| genre | string | 否 | 音乐类型：pop/classical/electronic/ambient |
| mood | string | 否 | 情绪：happy/sad/energetic/calm |
| duration | string | 否 | 时长范围：short(<30s)/medium(30s-2m)/long(>2m) |

**响应**
```json
{
  "code": 200,
  "data": {
    "total": 100,
    "music": [
      {
        "fileId": "music-uuid",
        "title": "Energetic Action",
        "artist": "Alex Grohl",
        "genre": "pop",
        "mood": "energetic",
        "duration": 180,
        "downloadUrl": "/api/v1/files/music-uuid/download"
      }
    ]
  }
}
```

---

### 5.2 获取模板列表

#### GET /materials/templates

**请求**
```http
GET /api/v1/materials/templates?type=intro
```

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 否 | intro/outro/transition/effect |

**响应**
```json
{
  "code": 200,
  "data": {
    "templates": [
      {
        "templateId": "tmpl-uuid",
        "name": "简约片头",
        "type": "intro",
        "duration": 5,
        "previewUrl": "/api/v1/templates/tmpl-uuid/preview.mp4"
      }
    ]
  }
}
```

---

## 六、系统模块

### 6.1 健康检查

#### GET /health

**请求**
```http
GET /api/v1/health
```

**响应**
```json
{
  "code": 200,
  "data": {
    "status": "healthy",
    "version": "v1.0.0",
    "uptime": 86400,
    "checks": {
      "database": "ok",
      "storage": "ok",
      "redis": "ok"
    }
  }
}
```

---

### 6.2 系统信息

#### GET /system/info

**请求**
```http
GET /api/v1/system/info
```

**响应**
```json
{
  "code": 200,
  "data": {
    "version": "v1.0.0",
    "buildTime": "2026-03-21T00:00:00Z",
    "environment": "production",
    "stats": {
      "totalFiles": 1000,
      "totalTasks": 5000,
      "storageUsed": "50GB",
      "storageTotal": "100GB"
    }
  }
}
```

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

## 八、开发计划

### 第一阶段接口（10 人天）

| 接口 | 优先级 | 工作量 | 状态 |
|------|--------|--------|------|
| **文件管理** |
| POST /files/upload | P0 | 2 人天 | ⏳ |
| GET /files | P0 | 0.5 人天 | ⏳ |
| GET /files/:id | P0 | 0.5 人天 | ⏳ |
| GET /files/:id/download | P0 | 0.5 人天 | ⏳ |
| DELETE /files/:id | P0 | 0.5 人天 | ⏳ |
| **任务管理** |
| GET /tasks/:id | P0 | 1 人天 | ⏳ |
| DELETE /tasks/:id | P0 | 0.5 人天 | ⏳ |
| **视频处理** |
| POST /video/concat | P0 | 2 人天 | ⏳ |
| POST /video/text-overlay | P0 | 1.5 人天 | ⏳ |
| POST /video/image-overlay | P0 | 1 人天 | ⏳ |
| POST /video/add-music | P0 | 1 人天 | ⏳ |
| POST /video/add-voiceover | P0 | 1 人天 | ⏳ |
| **音频处理** |
| POST /audio/voiceover | P0 | 1.5 人天 | ⏳ |

**总计**: 13 人天

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

---

**维护人**: 后端开发团队  
**最后更新**: 2026-03-21  
**下一版本**: v2.1 (待补充：批量操作、WebSocket 实时通知)
