# 测试用例审查报告

**审查人**: 王秘书  
**审查日期**: 2026-03-21  
**审查对象**: tests/test_cases.md v1.0  
**对比基准**: docs/API.md v2.1

---

## 📊 审查结果

### 测试用例覆盖度

| API 接口 | 测试用例 | 覆盖状态 |
|----------|----------|----------|
| **文件管理 (6 个接口)** |
| POST /files/upload | TC-FILE-001~005 | ✅ 完全覆盖 |
| GET /files | TC-FILE-006 | ✅ 覆盖 |
| GET /files/:id | TC-FILE-007 | ✅ 覆盖 |
| GET /files/:id/download | ❌ 缺失 | 🔴 待补充 |
| DELETE /files/:id | TC-FILE-008 | ✅ 覆盖 |
| POST /files/batch-delete | ❌ 缺失 | 🔴 待补充 |
| **视频处理 (8 个接口)** |
| POST /video/concat | TC-VIDEO-001~002 | ✅ 覆盖 |
| POST /video/text-overlay | TC-VIDEO-003~004 | ✅ 覆盖 |
| POST /video/image-overlay | TC-VIDEO-005 | ✅ 覆盖 |
| POST /video/add-music | TC-VIDEO-006~007 | ✅ 覆盖 |
| POST /video/add-voiceover | TC-VIDEO-008 | ✅ 覆盖 |
| POST /video/transition | TC-VIDEO-009 | ✅ 覆盖 |
| POST /video/process | TC-VIDEO-010 | ✅ 覆盖 |
| POST /video/add-subtitles | TC-VIDEO-011~012 | ✅ 覆盖 |
| **音频处理 (2 个接口)** |
| POST /audio/voiceover | TC-AUDIO-001~004 | ✅ 覆盖 |
| POST /audio/asr | ❌ 缺失 | 🔴 待补充 |
| **任务管理 (3 个接口)** |
| GET /tasks/:id | TC-TASK-001~003 | ✅ 覆盖 |
| DELETE /tasks/:id | TC-TASK-004 | ✅ 覆盖 |
| POST /tasks/batch-query | ❌ 缺失 | 🔴 待补充 |
| **素材库 (2 个接口)** | ❌ 全部缺失 | 🔴 待补充 |
| **系统 (2 个接口)** | ❌ 全部缺失 | 🔴 待补充 |

---

## 🔴 缺失的测试用例（7 个）

### 1. 文件下载接口

**接口**: GET /files/:id/download

**建议补充**:
```markdown
### TC-FILE-009: 下载文件 - 正常流程

**优先级**: P0
**前置条件**: 已上传一个视频文件

**测试步骤**:
1. 调用 `GET /api/v1/files/:fileId/download`
2. 验证响应

**预期结果**:
- ✅ HTTP 200 状态码
- ✅ Content-Type: application/octet-stream
- ✅ Content-Disposition 包含文件名
- ✅ 文件内容完整，MD5 校验通过
```

---

### 2. 批量删除文件

**接口**: POST /files/batch-delete

**建议补充**:
```markdown
### TC-FILE-010: 批量删除文件 - 正常流程

**优先级**: P1
**前置条件**: 已上传 3 个视频文件

**测试步骤**:
1. 调用 `POST /api/v1/files/batch-delete`
2. 请求体：`{"fileIds": ["id1", "id2", "id3"]}`
3. 验证响应

**预期结果**:
- ✅ HTTP 200 状态码
- ✅ 返回 deleted=3, failed=0
- ✅ 3 个文件都被删除
```

---

### 3. ASR 字幕生成

**接口**: POST /audio/asr

**建议补充**:
```markdown
### TC-AUDIO-005: ASR 字幕生成 - 正常流程

**优先级**: P1
**前置条件**: 已上传一个带语音的音频文件

**测试步骤**:
1. 调用 `POST /api/v1/audio/asr`
2. 请求体：`{"audioId": "xxx", "language": "zh-CN"}`
3. 获取 taskId
4. 轮询任务状态
5. 验证生成的字幕文件

**预期结果**:
- ✅ 任务完成
- ✅ 返回 SRT 文件
- ✅ 字幕时间与音频匹配
- ✅ 中文识别准确率≥90%
```

---

### 4. 批量查询任务

**接口**: POST /tasks/batch-query

**建议补充**:
```markdown
### TC-TASK-006: 批量查询任务 - 正常流程

**优先级**: P2
**前置条件**: 已提交 3 个任务

**测试步骤**:
1. 调用 `POST /api/v1/tasks/batch-query`
2. 请求体：`{"taskIds": ["task1", "task2", "task3"]}`
3. 验证响应

**预期结果**:
- ✅ HTTP 200 状态码
- ✅ 返回 3 个任务的状态
- ✅ 每个任务包含 taskId、status、progress
```

---

### 5. 获取音乐列表

**接口**: GET /materials/music

**建议补充**:
```markdown
### TC-MAT-001: 获取音乐列表 - 正常流程

**优先级**: P2
**前置条件**: 无

**测试步骤**:
1. 调用 `GET /api/v1/materials/music?genre=pop&page=1`
2. 验证响应

**预期结果**:
- ✅ HTTP 200 状态码
- ✅ 返回音乐列表
- ✅ 包含 fileId、title、artist、duration
- ✅ 支持 genre、mood、duration 筛选
```

---

### 6. 获取模板列表

**接口**: GET /materials/templates

**建议补充**:
```markdown
### TC-MAT-002: 获取模板列表 - 正常流程

**优先级**: P2
**前置条件**: 无

**测试步骤**:
1. 调用 `GET /api/v1/materials/templates?type=intro`
2. 验证响应

**预期结果**:
- ✅ HTTP 200 状态码
- ✅ 返回模板列表
- ✅ 包含 templateId、name、type、duration
- ✅ 支持 type 筛选
```

---

### 7. 健康检查

**接口**: GET /health

**建议补充**:
```markdown
### TC-SYS-001: 健康检查 - 正常流程

**优先级**: P2
**前置条件**: 无

**测试步骤**:
1. 调用 `GET /api/v1/health`
2. 验证响应

**预期结果**:
- ✅ HTTP 200 状态码
- ✅ status="healthy"
- ✅ 包含 version、uptime
- ✅ checks 包含 database、storage、redis 状态
```

---

## 🟡 需要更新的测试用例（4 个）

### 1. 添加背景音乐

**当前**: TC-VIDEO-006

**问题**: 未测试新增的 `startTime` 和 `endTime` 参数

**建议补充**:
```markdown
### TC-VIDEO-006-2: 添加背景音乐 - 指定开始时间

**优先级**: P1
**前置条件**: 已上传视频和音频

**测试步骤**:
1. 调用 `POST /api/v1/video/add-music`
2. 设置 `startTime=5.0`（从第 5 秒开始）
3. 设置 `endTime=20.0`（到第 20 秒结束）
4. 验证输出

**预期结果**:
- ✅ 音乐从视频第 5 秒开始播放
- ✅ 音乐在第 20 秒结束
```

---

### 2. 添加配音

**当前**: TC-VIDEO-008

**问题**: 未测试新增的 `alignMode=custom` 和 `startTime` 参数

**建议补充**:
```markdown
### TC-VIDEO-008-2: 添加配音 - 自定义开始时间

**优先级**: P1
**前置条件**: 已上传视频和配音音频

**测试步骤**:
1. 调用 `POST /api/v1/video/add-voiceover`
2. 设置 `alignMode="custom"`
3. 设置 `startTime=10.0`（从第 10 秒开始）
4. 验证输出

**预期结果**:
- ✅ 配音从视频第 10 秒开始
```

---

### 3. 添加字幕

**当前**: TC-VIDEO-012

**问题**: 未测试新增的 `offset` 参数

**建议补充**:
```markdown
### TC-VIDEO-012-2: 添加字幕 - 时间偏移

**优先级**: P2
**前置条件**: 已上传视频和 SRT 字幕

**测试步骤**:
1. 调用 `POST /api/v1/video/add-subtitles`
2. 设置 `offset=2.0`（延迟 2 秒）
3. 验证输出

**预期结果**:
- ✅ 字幕整体延迟 2 秒出现
```

---

### 4. 图片水印

**当前**: TC-VIDEO-005

**问题**: 未明确测试 `duration.end=-1` 的情况

**建议补充**:
```markdown
### TC-VIDEO-005-2: 添加图片水印 - 直到视频结束

**优先级**: P2
**前置条件**: 已上传视频和图片

**测试步骤**:
1. 调用 `POST /api/v1/video/image-overlay`
2. 设置 `duration.end=-1`
3. 验证输出

**预期结果**:
- ✅ 水印从开始时间显示到视频结束
```

---

## 📋 测试用例统计

### 当前状态

| 类别 | 数量 |
|------|------|
| 已有用例 | 31 |
| 需补充用例 | 7 |
| 需更新用例 | 4 |
| **更新后总计** | **42** |

### 按模块统计（更新后）

| 模块 | 用例数 | P0 | P1 | P2 |
|------|--------|----|----|----|
| 文件管理 | 10 | 6 | 2 | 2 |
| 视频处理 | 16 | 9 | 4 | 3 |
| 音频处理 | 5 | 3 | 2 | 0 |
| 任务管理 | 6 | 3 | 1 | 2 |
| 素材库 | 2 | 0 | 0 | 2 |
| 系统 | 2 | 0 | 0 | 2 |
| **总计** | **41** | **21** | **9** | **11** |

---

## ✅ 审查结论

### 测试用例质量

| 维度 | 评分 | 说明 |
|------|------|------|
| 核心功能覆盖 | 4.5/5 ⭐⭐⭐⭐⭐ | P0 接口全部覆盖 |
| 边界情况覆盖 | 4/5 ⭐⭐⭐⭐ | 错误场景充分 |
| 性能测试 | 3/5 ⭐⭐⭐ | 仅 3 个性能用例 |
| 新增参数覆盖 | 3/5 ⭐⭐⭐ | 需补充新参数测试 |

### 总体评价

**测试用例整体质量良好**，核心功能覆盖完整，但需要：
1. ✅ 补充 7 个缺失接口的测试用例
2. ✅ 更新 4 个用例以覆盖新增参数
3. ✅ 考虑增加性能测试用例

---

## 📝 建议行动

### 立即补充（P0/P1 接口）

1. TC-FILE-009: 下载文件
2. TC-FILE-010: 批量删除
3. TC-AUDIO-005: ASR 字幕生成
4. TC-TASK-006: 批量查询任务

### 后续补充（P2 接口）

5. TC-MAT-001: 音乐列表
6. TC-MAT-002: 模板列表
7. TC-SYS-001: 健康检查

### 参数测试补充

- TC-VIDEO-006-2: 音乐开始/结束时间
- TC-VIDEO-008-2: 配音自定义开始时间
- TC-VIDEO-012-2: 字幕时间偏移
- TC-VIDEO-005-2: 水印 end=-1

---

**审查完成时间**: 2026-03-21 01:10 CST  
**下一步**: 更新 test_cases.md 补充缺失用例
