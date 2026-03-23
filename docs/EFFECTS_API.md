# 特效管理 API 文档

**版本**: v1.0  
**创建日期**: 2026-03-24  
**状态**: ✅ 已完成

---

## 接口概览

| 接口 | 功能 | 路径 |
|------|------|------|
| 文字特效 | 应用文字到视频 | `POST /api/v1/effects/text` |
| 点关注特效 | 应用关注动画 | `POST /api/v1/effects/follow` |
| 画中画 | 视频叠加 | `POST /api/v1/effects/pip` |

---

## 1. 文字特效

### POST /api/v1/effects/text

**请求**
```json
{
  "videoId": "video_uuid",
  "text": "Hello World",
  "outputName": "output.mp4",
  "style": {
    "fontSize": 36,
    "color": "#FFFFFF",
    "font": "Arial-Bold",
    "strokeColor": "#000000",
    "strokeWidth": 1,
    "effect": "typewriter",
    "position": "bottom-center",
    "backgroundColor": "rgba(0,0,0,0.6)",
    "backgroundPadding": 10
  }
}
```

**特效类型**
- `none` - 无特效
- `typewriter` - 打字机
- `flash` - 闪烁
- `bounce` - 弹跳
- `slide` - 滑入
- `fade` - 渐显

**位置选项**
- `top-left`, `top-center`, `top-right`
- `center`
- `bottom-left`, `bottom-center`, `bottom-right`

**响应**
```json
{
  "code": 200,
  "data": {
    "outputName": "output.mp4",
    "downloadUrl": "/api/v1/files/output/output.mp4"
  },
  "message": "文字特效应用成功"
}
```

---

## 2. 点关注特效

### POST /api/v1/effects/follow

**请求**
```json
{
  "videoId": "video_uuid",
  "outputName": "output.mp4",
  "startTime": 25,
  "duration": 5,
  "style": {
    "buttonType": "circle",
    "animation": "pulse",
    "text": "点关注不迷路",
    "position": "bottom-right",
    "size": 80,
    "color": "#FF4500"
  }
}
```

**按钮类型**
- `circle` - 圆形
- `square` - 方形
- `heart` - 心形

**动画类型**
- `pulse` - 脉冲
- `popup` - 弹出
- `fade` - 渐显

**响应**
```json
{
  "code": 200,
  "data": {
    "outputName": "effect_follow_abc123.mp4",
    "downloadUrl": "/api/v1/files/output/effect_follow_abc123.mp4"
  },
  "message": "点关注特效应用成功"
}
```

---

## 3. 画中画特效

### POST /api/v1/effects/pip

**请求**
```json
{
  "mainVideoId": "main_video_uuid",
  "pipVideoId": "pip_video_uuid",
  "outputName": "output.mp4",
  "layout": "bottom-right",
  "style": {
    "size": 0.25,
    "border": true,
    "borderColor": "#FFFFFF",
    "shadow": true,
    "transition": "fade"
  }
}
```

**布局模式**
- `bottom-right` - 右下角
- `bottom-left` - 左下角
- `center` - 居中

**响应**
```json
{
  "code": 200,
  "data": {
    "outputName": "effect_pip_xyz789.mp4",
    "downloadUrl": "/api/v1/files/output/effect_pip_xyz789.mp4"
  },
  "message": "画中画特效应用成功"
}
```

---

## 错误码

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| 5002 | 视频处理失败 | 检查视频文件是否存在 |
| 4004 | 文件不存在 | 确认文件 ID 正确 |
| 4001 | 参数错误 | 检查请求参数格式 |

---

## 使用示例

### Python
```python
import requests

# 文字特效
response = requests.post('http://localhost:15321/api/v1/effects/text', json={
    'videoId': 'video_123',
    'text': 'Hello World',
    'style': {
        'effect': 'typewriter',
        'position': 'center',
        'fontSize': 48,
        'color': '#FFFFFF'
    }
})
print(response.json())
```

### JavaScript
```javascript
// 点关注特效
fetch('http://localhost:15321/api/v1/effects/follow', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    videoId: 'video_123',
    startTime: 25,
    duration: 5,
    style: {
      animation: 'pulse',
      text: '点关注',
      position: 'bottom-right'
    }
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

---

**维护人**: 开发团队  
**最后更新**: 2026-03-24
