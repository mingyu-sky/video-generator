# Video Generator API 文档

**版本**: v1.0  
**最后更新**: 2026-03-21  
**状态**: ⏳ 待开发

---

## 基础信息

- **Base URL**: `http://localhost:15321/api/v1`
- **认证方式**: 无 (v3.1 版本移除认证)
- **数据格式**: JSON

---

## 接口列表

### 1. 文件上传

#### POST /upload

上传视频/音频文件

**请求**
```http
POST /api/v1/upload
Content-Type: multipart/form-data

file: <video/audio file>
type: video | audio
```

**响应**
```json
{
  "code": 200,
  "data": {
    "fileId": "uuid-string",
    "fileName": "video.mp4",
    "fileSize": 1048576,
    "duration": 30.5,
    "uploadTime": "2026-03-21T10:00:00Z"
  },
  "message": "上传成功"
}
```

**错误码**
| 码 | 说明 |
|---|------|
| 1001 | 文件格式不支持 |
| 1002 | 文件大小超限 (2GB) |
| 1003 | 文件损坏 |

---

### 2. 视频拼接

#### POST /video/concat

合并多个视频文件

**请求**
```json
{
  "videos": ["fileId1", "fileId2", "fileId3"],
  "outputName": "merged_video.mp4"
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "taskId": "task-uuid",
    "status": "processing",
    "estimatedTime": 60
  },
  "message": "任务已提交"
}
```

---

### 3. 添加文字特效

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
    "color": "#FFFFFF",
    "font": "Arial"
  },
  "duration": {
    "start": 0,
    "end": 5
  }
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "taskId": "task-uuid"
  },
  "message": "任务已提交"
}
```

---

### 4. 添加图片/动图水印

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
  "opacity": 0.8
}
```

---

### 5. AI 配音生成

#### POST /audio/voiceover

使用 Edge TTS 生成配音

**请求**
```json
{
  "text": "这是配音文本",
  "voice": "zh-CN-XiaoxiaoNeural",
  "speed": 1.0,
  "outputName": "voiceover.mp3"
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "audioId": "audio-uuid",
    "duration": 10.5
  },
  "message": "配音生成成功"
}
```

---

### 6. 视频添加配音

#### POST /video/add-voiceover

**请求**
```json
{
  "videoId": "fileId",
  "voiceoverId": "audioId",
  "volume": 0.8,
  "alignMode": "start"  // start | center | end
}
```

---

### 7. 添加背景音乐

#### POST /video/add-music

**请求**
```json
{
  "videoId": "fileId",
  "musicId": "audioId",
  "volume": 0.3,
  "fade": {
    "in": 2.0,
    "out": 2.0
  }
}
```

---

### 8. 添加转场特效

#### POST /video/transition

**请求**
```json
{
  "videos": ["fileId1", "fileId2"],
  "transition": "fade",  // fade | dissolve | wipe
  "duration": 1.0
}
```

---

### 9. 任务查询

#### GET /tasks/:taskId

查询任务进度

**响应**
```json
{
  "code": 200,
  "data": {
    "taskId": "task-uuid",
    "status": "processing",  // pending | processing | completed | failed
    "progress": 50,
    "message": "处理中...",
    "result": {
      "outputId": "outputFileId",
      "downloadUrl": "/downloads/output.mp4"
    }
  }
}
```

---

## 错误响应格式

```json
{
  "code": 1001,
  "message": "文件格式不支持",
  "details": "仅支持 MP4, MOV, AVI 格式"
}
```

## 完整错误码表

| 错误码 | 说明 | HTTP 状态 |
|--------|------|----------|
| 1001 | 文件格式不支持 | 400 |
| 1002 | 文件大小超限 | 400 |
| 1003 | 文件损坏 | 400 |
| 2001 | 音频处理失败 | 500 |
| 2002 | 配音生成失败 | 500 |
| 3001 | 字幕识别失败 | 500 |
| 4001 | 特效应用失败 | 500 |
| 5001 | 服务器资源不足 | 503 |
| 5002 | 处理超时 | 408 |
| 9999 | 未知错误 | 500 |

---

## 开发计划

### 第一阶段 (8 人天)

| 接口 | 优先级 | 工作量 | 状态 |
|------|--------|--------|------|
| POST /upload | P0 | 2 人天 | ⏳ 待开发 |
| GET /tasks/:id | P0 | 1 人天 | ⏳ 待开发 |
| POST /video/concat | P0 | 2 人天 | ⏳ 待开发 |
| POST /video/text-overlay | P0 | 1.5 人天 | ⏳ 待开发 |
| POST /video/image-overlay | P0 | 1.5 人天 | ⏳ 待开发 |
| POST /audio/voiceover | P0 | 1.5 人天 | ⏳ 待开发 |
| POST /video/add-voiceover | P0 | 1 人天 | ⏳ 待开发 |
| POST /video/add-music | P0 | 1 人天 | ⏳ 待开发 |
| POST /video/transition | P0 | 1.5 人天 | ⏳ 待开发 |

---

**维护人**: 后端开发团队  
**最后更新**: 2026-03-21
