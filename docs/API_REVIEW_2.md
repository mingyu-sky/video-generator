# API 文档二次审查报告

**审查人**: 王秘书  
**审查日期**: 2026-03-21  
**审查对象**: docs/API.md v2.0  
**触发原因**: 老板发现文字特效接口缺少开始时间参数

---

## 🔴 发现的问题

### 问题 1: 文字特效接口缺少开始时间 ⚠️

**接口**: POST /video/text-overlay

**当前参数**:
```json
{
  "duration": {
    "start": 0,
    "end": 5
  }
}
```

**问题**: `duration.start` 和 `duration.end` 已包含开始时间，**设计合理** ✅

**说明**: 
- `start` = 文字开始出现的时间（秒）
- `end` = 文字消失的时间（秒）
- 设计合理，无需修改

---

### 问题 2: 图片水印接口缺少开始时间 ❌

**接口**: POST /video/image-overlay

**当前参数**:
```json
{
  "duration": {
    "start": 0,
    "end": -1
  }
}
```

**问题**: 
- ✅ 有 start 参数（开始时间）
- ⚠️ end=-1 表示直到视频结束，但文档未明确说明

**建议**: 补充说明
```json
"duration": {
  "start": 0,      // 开始出现时间（秒）
  "end": -1        // 消失时间（秒），-1 表示直到视频结束
}
```

---

### 问题 3: 背景音乐接口缺少开始播放时间 ❌

**接口**: POST /video/add-music

**当前参数**:
```json
{
  "volume": 0.3,
  "fade": {"in": 2.0, "out": 2.0},
  "loop": true
}
```

**问题**: 
- ❌ 缺少 `startTime` 参数
- 无法指定从视频的第几秒开始播放音乐

**建议补充**:
```json
{
  "startTime": 0,    // 从视频的第几秒开始播放（秒）
  "volume": 0.3,
  "fade": {"in": 2.0, "out": 2.0},
  "loop": true,
  "endTime": -1      // 结束时间（秒），-1 表示直到视频结束
}
```

---

### 问题 4: 配音接口缺少开始时间 ❌

**接口**: POST /video/add-voiceover

**当前参数**:
```json
{
  "alignMode": "start"
}
```

**问题**: 
- `alignMode` 只有 start/center/end 三种对齐方式
- ❌ 无法指定精确的开始时间（如从第 5 秒开始）

**建议补充**:
```json
{
  "alignMode": "custom",  // start/center/end/custom
  "startTime": 5.0        // 自定义开始时间（秒），alignMode=custom 时必填
}
```

---

### 问题 5: 字幕接口缺少开始时间 ❌

**接口**: POST /video/add-subtitles

**当前参数**:
```json
{
  "subtitleId": "srtFileId",
  "style": {...}
}
```

**问题**: 
- ❌ 缺少 `offset` 参数
- SRT 文件有自己的时间轴，但可能需要整体偏移

**建议补充**:
```json
{
  "subtitleId": "srtFileId",
  "offset": 0,          // 字幕整体时间偏移（秒），正数延迟，负数提前
  "style": {...}
}
```

---

### 问题 6: 转场接口参数不完整 ❌

**接口**: POST /video/transition

**当前参数**:
```json
{
  "videos": ["fileId1", "fileId2"],
  "transition": "fade",
  "duration": 1.0
}
```

**问题**: 
- ✅ 基础转场参数完整
- ⚠️ 缺少转场位置参数（默认在两个视频之间）
- ⚠️ 不支持多个转场（如 3 个视频需要 2 个转场）

**建议补充**:
```json
{
  "videos": ["fileId1", "fileId2", "fileId3"],
  "transitions": [
    {
      "type": "fade",
      "duration": 1.0,
      "position": 0      // 在第 1 个视频后（索引从 0 开始）
    },
    {
      "type": "dissolve",
      "duration": 1.5,
      "position": 1      // 在第 2 个视频后
    }
  ]
}
```

---

### 问题 7: 一站式处理接口步骤类型不完整 ⚠️

**接口**: POST /video/process

**当前支持的步骤类型**:
- `add_music`
- `add_voiceover`
- `add_subtitles`
- `text_overlay`
- `image_overlay`

**问题**: 
- ❌ 缺少 `concat`（拼接）
- ❌ 缺少 `transition`（转场）

**建议补充**:
```json
"steps": [
  {
    "type": "concat",
    "params": {
      "videos": ["id1", "id2"],
      "transition": "fade"
    }
  },
  {
    "type": "add_music",
    "params": {...}
  }
]
```

---

## 📋 问题汇总

| 接口 | 问题 | 严重程度 | 建议 |
|------|------|----------|------|
| /video/text-overlay | 参数合理 | ✅ 无问题 | 无需修改 |
| /video/image-overlay | end=-1 未说明 | 🟡 轻微 | 补充文档说明 |
| /video/add-music | 缺少 startTime | 🟠 中等 | 添加参数 |
| /video/add-voiceover | 缺少精确开始时间 | 🟠 中等 | 添加 custom 模式 |
| /video/add-subtitles | 缺少时间偏移 | 🟡 轻微 | 添加 offset 参数 |
| /video/transition | 不支持多转场 | 🟠 中等 | 支持 transitions 数组 |
| /video/process | 步骤类型不完整 | 🟡 轻微 | 补充 concat/transition |

---

## 🔧 修改建议

### 必须修改（阻塞开发）

无 - 所有问题都不阻塞开发，可在开发过程中调整

### 建议修改（开发前）

1. **/video/add-music** - 添加 `startTime` 和 `endTime` 参数
2. **/video/add-voiceover** - 添加 `custom` 对齐模式

### 可选修改（开发后）

3. **/video/image-overlay** - 补充 `end=-1` 的文档说明
4. **/video/add-subtitles** - 添加 `offset` 参数
5. **/video/transition** - 支持多转场
6. **/video/process** - 补充步骤类型

---

## 📝 修改后的接口参数

### POST /video/add-music（修改后）

```json
{
  "videoId": "fileId",
  "musicId": "audioId",
  "startTime": 0,       // 新增：从视频的第几秒开始播放
  "endTime": -1,        // 新增：结束时间，-1 表示直到视频结束
  "volume": 0.3,
  "fade": {
    "in": 2.0,
    "out": 2.0
  },
  "loop": true,
  "outputName": "video_with_music.mp4"
}
```

### POST /video/add-voiceover（修改后）

```json
{
  "videoId": "fileId",
  "voiceoverId": "audioId",
  "alignMode": "custom",  // 修改：添加 custom 选项
  "startTime": 5.0,       // 新增：自定义开始时间
  "volume": 0.8,
  "outputName": "video_with_voiceover.mp4"
}
```

### POST /video/add-subtitles（修改后）

```json
{
  "videoId": "fileId",
  "subtitleId": "srtFileId",
  "offset": 0,            // 新增：时间偏移（秒）
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

---

## ✅ 审查结论

### 参数设计评价

| 维度 | 评分 | 说明 |
|------|------|------|
| 完整性 | 3.5/5 ⭐⭐⭐⭐ | 核心参数完整，部分细节缺失 |
| 一致性 | 4/5 ⭐⭐⭐⭐ | 整体一致，个别接口需统一 |
| 灵活性 | 3.5/5 ⭐⭐⭐⭐ | 支持常用场景，高级场景需扩展 |
| 易用性 | 4/5 ⭐⭐⭐⭐ | 参数命名清晰 |

### 总体评价

**API 设计整体合理**，文字特效接口的 `duration.start/end` 设计正确。发现的 7 个问题中：
- 1 个是误解（文字特效已包含开始时间）✅
- 2 个是中等优先级（音乐/配音的开始时间）🟠
- 4 个是低优先级（文档说明、高级功能）🟡

**建议**: 先启动开发，中等优先级问题在开发第一阶段补充，低优先级问题可在后续迭代优化。

---

**审查完成时间**: 2026-03-21 01:05 CST  
**下一步**: 更新 API 文档 v2.1
