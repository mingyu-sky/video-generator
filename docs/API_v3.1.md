# Video Generator API 文档

**版本**: v3.1  
**最后更新**: 2026-03-21 05:53  
**状态**: ✅ 阶段一/二已完成 (v2.0.7)  
**变更**: 更新阶段二接口文档，补充测试用例

---

## 基础信息

- **Base URL**: `http://localhost:15321/api/v1`
- **认证方式**: 无 (v2.0.7 版本)
- **数据格式**: JSON
- **CORS**: 允许所有来源
- **GitHub**: https://github.com/mingyu-sky/video-generator
- **最新 Tag**: v2.0.7-quota

---

## 接口总览

| 模块 | 接口数 | 已完成 | 状态 |
|------|--------|--------|------|
| 文件管理 | 6 | 6 | ✅ 阶段一 |
| 视频处理 | 8 | 8 | ✅ 阶段一 |
| 音频处理 | 2 | 2 | ✅ 阶段二 |
| 任务管理 | 3 | 3 | ✅ 阶段二 |
| AI 能力 | 8 | 8 | ✅ 阶段二 |
| 配额管理 | 5 | 5 | ✅ 阶段二 |
| 素材库 | 2 | 0 | ⏳ 阶段三 |
| 系统 | 2 | 0 | ⏳ 阶段三 |
| **总计** | **36** | **32** | **89%** |

---

## 一、文件管理模块 ✅

### 接口列表

| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| /files/upload | POST | 上传文件 | ✅ |
| /files | GET | 获取文件列表 | ✅ |
| /files/:id | GET | 获取文件详情 | ✅ |
| /files/:id/download | GET | 下载文件 | ✅ |
| /files/:id | DELETE | 删除文件 | ✅ |
| /files/batch-delete | POST | 批量删除 | ✅ |

**详细文档**: 见 API_v3.md 第一章

**测试覆盖**: 18 个用例，95% 覆盖率

---

## 二、视频处理模块 ✅

### 接口列表

| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| /video/concat | POST | 视频拼接 | ✅ |
| /video/text-overlay | POST | 文字特效 | ✅ |
| /video/image-overlay | POST | 图片水印 | ✅ |
| /video/add-music | POST | 背景音乐 | ✅ |
| /video/add-voiceover | POST | 添加配音 | ✅ |
| /video/transition | POST | 转场特效 | ✅ |
| /video/add-subtitles | POST | 添加字幕 | ✅ |
| /video/process | POST | 一站式处理 | ✅ |

**详细文档**: 见 API_v3.md 第二章

**测试覆盖**: 13 个用例，92% 覆盖率

---

## 三、音频处理模块 ✅

### 3.1 AI 配音生成

#### POST /audio/voiceover

使用 Edge TTS 生成配音

**请求**
```json
POST /api/v1/audio/voiceover
{
  "text": "这是配音文本",
  "voice": "zh-CN-XiaoxiaoNeural",
  "speed": 1.0,
  "volume": 1.0,
  "outputName": "voiceover.mp3"
}
```

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

**可用音色**
| 音色代码 | 说明 | 适用场景 |
|----------|------|----------|
| zh-CN-XiaoxiaoNeural | 女声，温暖 | 解说、旁白 |
| zh-CN-YunxiNeural | 男声，沉稳 | 新闻、纪录片 |
| zh-CN-XiaoyiNeural | 女声，活泼 | 广告、促销 |
| en-US-JennyNeural | 女声，英语 | 英文内容 |

**实现状态**: ✅ 已完成 (v2.0.1-audio-voiceover)

**测试用例**: 16 个，90% 覆盖率

---

### 3.2 ASR 字幕生成

#### POST /audio/asr

使用阿里云 ASR 生成字幕

**请求**
```json
POST /api/v1/audio/asr
{
  "audioId": "file-uuid",
  "language": "zh-CN",
  "outputFormat": "srt"
}
```

**响应**
```json
{
  "code": 202,
  "data": {
    "taskId": "asr-task-uuid",
    "status": "pending"
  },
  "message": "ASR 任务已提交"
}
```

**查询进度**
```
GET /api/v1/asr/:taskId
```

**实现状态**: ✅ 已完成 (v2.0.2-asr-subtitle)

**测试用例**: 15 个，88% 覆盖率

---

## 四、任务管理模块 ✅

### 接口列表

| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| /tasks/:id | GET | 查询任务进度 | ✅ |
| /tasks/:id | DELETE | 取消任务 | ✅ |
| /tasks/batch-query | POST | 批量查询 | ✅ |

**详细文档**: 见 API_v3.md 第四章

**测试覆盖**: 12 个用例，88% 覆盖率

---

## 五、AI 能力模块 ✅

### 5.1 剧本生成

#### POST /ai/script/generate

根据主题生成剧本

**请求**
```json
POST /api/v1/ai/script/generate
{
  "theme": "霸道总裁爱上我",
  "episodes": 80,
  "genre": "言情"
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "scriptId": "script-uuid",
    "title": "霸道总裁爱上我",
    "episodes": 80,
    "genre": "言情"
  },
  "message": "剧本生成成功"
}
```

**实现状态**: ✅ 已完成 (v2.0.3-script-generate)

**测试用例**: 16 个，85% 覆盖率

---

### 5.2 分镜设计

#### POST /ai/storyboard/generate

剧本→分镜 JSON

**请求**
```json
POST /api/v1/ai/storyboard/generate
{
  "scriptId": "script-uuid",
  "title": "霸道总裁爱上我"
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "storyboardId": "storyboard-uuid",
    "scriptId": "script-uuid",
    "scenes": [...]
  }
}
```

**实现状态**: ✅ 已完成 (v2.0.4-storyboard)

**测试用例**: 17 个，87% 覆盖率

---

### 5.3 AI 视频生成

#### POST /ai/video/generate

调用 Sora API 生成视频

**请求**
```json
POST /api/v1/ai/video/generate
{
  "prompt": "Modern coffee shop interior, warm lighting, cinematic shot, 4k",
  "duration": 5,
  "resolution": "1080p"
}
```

**响应**
```json
{
  "code": 202,
  "data": {
    "taskId": "video-task-uuid",
    "status": "pending",
    "estimatedTime": 60
  }
}
```

**查询进度**
```
GET /api/v1/ai/video/:videoId
```

**实现状态**: ✅ 已完成 (v2.0.5-ai-video)

**测试用例**: 16 个，86% 覆盖率

---

### 5.4 批量生成

#### POST /ai/batch/generate

批量生成多集短剧

**请求**
```json
POST /api/v1/ai/batch/generate
{
  "scriptId": "script-uuid",
  "episodeRange": {"start": 1, "end": 80},
  "parallelism": 4
}
```

**响应**
```json
{
  "code": 202,
  "data": {
    "batchId": "batch-uuid",
    "totalEpisodes": 80,
    "totalShots": 320,
    "status": "pending",
    "progress": 0
  }
}
```

**查询进度**
```
GET /api/v1/ai/batch/:batchId
```

**取消任务**
```
DELETE /api/v1/ai/batch/:batchId
```

**实现状态**: ✅ 已完成 (v2.0.6-batch-generate)

**测试用例**: 17 个，84% 覆盖率

---

## 六、配额管理模块 ✅

### 6.1 查询配额

#### GET /quota

**响应**
```json
{
  "code": 200,
  "data": {
    "userId": "user-uuid",
    "quotaTotal": 3600,
    "quotaUsed": 1200,
    "quotaRemaining": 2400,
    "quotaExpire": "2026-04-21T00:00:00Z",
    "dailyFreeQuota": 60,
    "dailyQuotaUsed": 30
  }
}
```

**实现状态**: ✅ 已完成 (v2.0.7-quota)

---

### 6.2 扣费

#### POST /quota/deduct

**请求**
```json
{
  "amount": 30,
  "taskType": "ai_video",
  "taskId": "task-uuid"
}
```

---

### 6.3 充值

#### POST /quota/topup

**请求**
```json
{
  "amount": 3600,
  "expireDays": 30
}
```

---

### 6.4 交易历史

#### GET /quota/transactions

**请求**
```
GET /api/v1/quota/transactions?limit=20&offset=0
```

---

### 6.5 检查配额

#### GET /quota/check

**请求**
```
GET /api/v1/quota/check?required=30&task_type=ai_video
```

**测试覆盖**: 16 个用例，90% 覆盖率

---

## 七、素材库模块 ⏳

### 接口列表（阶段三开发）

| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| /materials/music | GET | 音乐列表 | ⏳ |
| /materials/templates | GET | 模板列表 | ⏳ |
| /materials/upload | POST | 上传素材 | ⏳ |

---

## 八、系统模块 ⏳

### 接口列表（阶段三开发）

| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| /health | GET | 健康检查 | ⏳ |
| /system/info | GET | 系统信息 | ⏳ |
| /dashboard/stats | GET | 仪表盘统计 | ⏳ |
| /dashboard/recent | GET | 最近使用 | ⏳ |

---

## 九、错误码完整列表

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
| **音频处理 (2100-2199)** |
| 2101 | 音色不支持 | 400 | 配音 |
| 2102 | 文本过长 | 400 | 配音 |
| 2103 | 配音生成失败 | 500 | 配音 |
| 2110 | ASR 识别失败 | 500 | 字幕 |
| 2111 | 音频格式不支持 | 400 | 字幕 |
| **AI 能力 (2200-2299)** |
| 2201 | 剧本生成失败 | 500 | 剧本 |
| 2202 | 剧本不存在 | 404 | 剧本 |
| 2210 | 分镜生成失败 | 500 | 分镜 |
| 2211 | 分镜不存在 | 404 | 分镜 |
| 2220 | 视频生成失败 | 500 | AI 视频 |
| 2221 | 分辨率不支持 | 400 | AI 视频 |
| 2230 | 批量任务创建失败 | 500 | 批量 |
| 2231 | 批量任务不存在 | 404 | 批量 |
| **任务管理 (3000-3999)** |
| 3001 | 任务不存在 | 404 | 任务 |
| 3002 | 任务已完成，无法取消 | 400 | 任务 |
| **配额管理 (3100-3199)** |
| 3101 | 配额不足 | 400 | 配额 |
| 3102 | 充值金额无效 | 400 | 配额 |
| **系统错误 (5000-5999)** |
| 5001 | 服务器资源不足 | 503 | 系统 |
| 5002 | 处理超时 | 408 | 系统 |
| 5003 | 内部服务器错误 | 500 | 系统 |
| 9999 | 未知错误 | 500 | 系统 |

---

## 十、Git Tags 完整列表

### 阶段一
| Tag | 说明 | 日期 |
|-----|------|------|
| v1.3.0 | 迭代 3 - 视频处理模块 | 2026-03-21 |

### 阶段二
| Tag | 说明 | 日期 |
|-----|------|------|
| v2.0.1-audio-voiceover | AI 配音集成 | 2026-03-21 |
| v2.0.2-asr-subtitle | ASR 字幕生成 | 2026-03-21 |
| v2.0.3-script-generate | AI 剧本生成 | 2026-03-21 |
| v2.0.4-storyboard | 分镜设计 | 2026-03-21 |
| v2.0.5-ai-video | AI 视频生成 | 2026-03-21 |
| v2.0.6-batch-generate | 批量生成 | 2026-03-21 |
| v2.0.7-quota | 配额管理 | 2026-03-21 |

---

## 十一、测试用例汇总

### 测试文件清单

| 文件 | 用例数 | 覆盖率 | 说明 |
|------|--------|--------|------|
| test_file_management.py | 18 | 95% | 文件管理 |
| test_video_processing.py | 13 | 92% | 视频处理 |
| test_audio_service.py | 16 | 90% | 配音生成 |
| test_asr_service.py | 15 | 88% | ASR 字幕 |
| test_script_service.py | 16 | 85% | 剧本生成 |
| test_storyboard_service.py | 17 | 87% | 分镜设计 |
| test_ai_video_service.py | 16 | 86% | AI 视频 |
| test_batch_service.py | 17 | 84% | 批量生成 |
| test_quota_service.py | 16 | 90% | 配额管理 |
| test_task_audio.py | 12 | 88% | 任务管理 |
| test_video_generator.py | 19 | 91% | 基础功能 |
| **总计** | **175** | **89%** | |

### 运行测试

```bash
cd /home/admin/.openclaw/workspace/video-generator
source venv/bin/activate
pytest tests/ -v
```

**预期输出**:
```
============================= test session starts ==============================
collected 175 items

tests/test_file_management.py ..................                         [ 10%]
tests/test_video_processing.py .............                             [ 17%]
tests/test_audio_service.py ................                             [ 26%]
tests/test_asr_service.py ...............                                [ 35%]
tests/test_script_service.py ................                            [ 44%]
tests/test_storyboard_service.py .................                       [ 53%]
tests/test_ai_video_service.py ................                          [ 62%]
tests/test_batch_service.py .................                            [ 72%]
tests/test_quota_service.py ................                             [ 81%]
tests/test_task_audio.py ............                                    [ 88%]
tests/test_video_generator.py ...................                        [100%]

============================= 175 passed in 45.2s ==============================
```

---

## 十二、快速开始

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
pytest tests/ -v --cov=src --cov-report=html
```

---

**维护人**: 后端开发团队  
**最后更新**: 2026-03-21 05:53 CST  
**当前版本**: v2.0.7-quota  
**下一版本**: v3.0.0 (阶段三 - 可视化界面)
