# 第三阶段接口文档

**版本**: v3.0 (阶段三)  
**创建日期**: 2026-03-21  
**状态**: ⏳ 待开发  
**依据**: PHASE3_REVIEW.md

---

## 📋 接口总览

### 新增接口（阶段三）

| 模块 | 接口 | 方法 | 说明 | 优先级 |
|------|------|------|------|--------|
| 仪表盘 | /dashboard/stats | GET | 仪表盘统计 | P0 |
| 仪表盘 | /dashboard/recent | GET | 最近使用 | P0 |
| 模板管理 | /templates | POST | 保存配置模板 | P0 |
| 模板管理 | /templates | GET | 获取模板列表 | P0 |
| 模板管理 | /templates/:id | DELETE | 删除模板 | P1 |
| 素材库 | /materials/music | GET | 音乐列表 | P0 |
| 素材库 | /materials/templates | GET | 模板列表 | P0 |
| 素材库 | /materials/upload | POST | 上传素材 | P1 |
| 系统 | /health | GET | 健康检查 | P0 |
| 系统 | /system/info | GET | 系统信息 | P1 |

**总计**: 10 个新增接口

---

## 一、仪表盘模块

### 1.1 仪表盘统计

#### GET /dashboard/stats

获取仪表盘统计数据

**请求**
```http
GET /api/v1/dashboard/stats
```

**响应**
```json
{
  "code": 200,
  "data": {
    "tasks": {
      "total": 156,
      "pending": 3,
      "processing": 2,
      "completed": 148,
      "failed": 3
    },
    "files": {
      "total": 342,
      "videos": 180,
      "audios": 98,
      "images": 64,
      "storageUsed": "15.6GB"
    },
    "scripts": {
      "total": 23,
      "thisMonth": 8
    },
    "batches": {
      "total": 12,
      "processing": 1,
      "completed": 11
    },
    "usage": {
      "todayQuota": 60,
      "todayUsed": 35,
      "todayRemaining": 25
    }
  },
  "message": "success"
}
```

**实现要点**:
- 聚合查询各模块统计数据
- 缓存优化（5 分钟过期）
- 异步计算耗时统计

**测试用例**:
```python
def test_dashboard_stats_success():
    """测试仪表盘统计 - 正常流程"""
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "tasks" in data
    assert "files" in data
    assert "scripts" in data
    assert "batches" in data
    assert "usage" in data

def test_dashboard_stats_empty_data():
    """测试仪表盘统计 - 空数据"""
    # 清空数据库后测试
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["tasks"]["total"] == 0
    assert data["files"]["total"] == 0

def test_dashboard_stats_cache():
    """测试仪表盘统计 - 缓存机制"""
    # 第一次请求
    start = time.time()
    client.get("/api/v1/dashboard/stats")
    first_time = time.time() - start
    
    # 第二次请求（应该命中缓存）
    start = time.time()
    client.get("/api/v1/dashboard/stats")
    second_time = time.time() - start
    
    # 缓存命中应该更快
    assert second_time < first_time
```

**优先级**: P0  
**工作量**: 0.5 人天

---

### 1.2 最近使用

#### GET /dashboard/recent

获取最近使用的任务/剧本/素材

**请求**
```http
GET /api/v1/dashboard/recent?type=tasks&limit=10
```

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 否 | tasks/scripts/batches/all，默认 all |
| limit | integer | 否 | 返回数量，默认 10，最大 50 |

**响应**
```json
{
  "code": 200,
  "data": {
    "tasks": [
      {
        "taskId": "task-uuid",
        "type": "video/add-music",
        "status": "completed",
        "createdAt": "2026-03-21T10:00:00Z",
        "completedAt": "2026-03-21T10:02:00Z",
        "result": {
          "outputId": "file-uuid",
          "downloadUrl": "/api/v1/files/file-uuid/download"
        }
      }
    ],
    "scripts": [
      {
        "scriptId": "script-uuid",
        "title": "霸道总裁爱上我",
        "episodes": 80,
        "createdAt": "2026-03-20T15:00:00Z"
      }
    ],
    "batches": [
      {
        "batchId": "batch-uuid",
        "scriptId": "script-uuid",
        "scriptTitle": "霸道总裁爱上我",
        "totalEpisodes": 80,
        "progress": 100,
        "status": "completed"
      }
    ]
  },
  "message": "success"
}
```

**实现要点**:
- 按创建时间倒序排序
- 支持类型过滤
- 限制返回数量

**测试用例**:
```python
def test_dashboard_recent_tasks():
    """测试最近使用 - 任务列表"""
    response = client.get("/api/v1/dashboard/recent?type=tasks&limit=5")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "tasks" in data
    assert len(data["tasks"]) <= 5

def test_dashboard_recent_all():
    """测试最近使用 - 全部类型"""
    response = client.get("/api/v1/dashboard/recent?type=all&limit=10")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "tasks" in data
    assert "scripts" in data
    assert "batches" in data

def test_dashboard_recent_invalid_type():
    """测试最近使用 - 无效类型"""
    response = client.get("/api/v1/dashboard/recent?type=invalid")
    assert response.status_code == 400
    assert response.json()["code"] == 4001
```

**优先级**: P0  
**工作量**: 0.5 人天

---

## 二、模板管理模块

### 2.1 保存配置模板

#### POST /templates

保存视频处理配置模板

**请求**
```json
POST /api/v1/templates
{
  "name": "抖音短视频模板",
  "description": "添加背景音乐 + 字幕 + 水印",
  "steps": [
    {
      "type": "add_music",
      "params": {
        "volume": 0.3,
        "fade": {"in": 2.0, "out": 2.0}
      }
    },
    {
      "type": "add_subtitles",
      "params": {
        "fontSize": 20,
        "position": "bottom"
      }
    },
    {
      "type": "image_overlay",
      "params": {
        "position": {"x": 50, "y": 50},
        "opacity": 0.8
      }
    }
  ],
  "isPublic": false
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "templateId": "tmpl-uuid",
    "name": "抖音短视频模板",
    "createdAt": "2026-03-21T10:00:00Z"
  },
  "message": "模板保存成功"
}
```

**错误码**
| 码 | 说明 |
|---|------|
| 4001 | 模板名称为空 |
| 4002 | 处理步骤为空 |
| 4003 | 步骤类型不支持 |

**测试用例**:
```python
def test_template_save_success():
    """测试保存模板 - 正常流程"""
    response = client.post("/api/v1/templates", json={
        "name": "测试模板",
        "steps": [{"type": "add_music", "params": {"volume": 0.3}}]
    })
    assert response.status_code == 200
    assert "templateId" in response.json()["data"]

def test_template_save_empty_name():
    """测试保存模板 - 名称为空"""
    response = client.post("/api/v1/templates", json={
        "name": "",
        "steps": [{"type": "add_music", "params": {}}]
    })
    assert response.status_code == 400
    assert response.json()["code"] == 4001

def test_template_save_empty_steps():
    """测试保存模板 - 步骤为空"""
    response = client.post("/api/v1/templates", json={
        "name": "测试模板",
        "steps": []
    })
    assert response.status_code == 400
    assert response.json()["code"] == 4002

def test_template_save_invalid_step_type():
    """测试保存模板 - 无效步骤类型"""
    response = client.post("/api/v1/templates", json={
        "name": "测试模板",
        "steps": [{"type": "invalid_type", "params": {}}]
    })
    assert response.status_code == 400
    assert response.json()["code"] == 4003
```

**优先级**: P0  
**工作量**: 1 人天

---

### 2.2 获取模板列表

#### GET /templates

获取用户的配置模板列表

**请求**
```http
GET /api/v1/templates?page=1&pageSize=20
```

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认 1 |
| pageSize | integer | 否 | 每页数量，默认 20 |

**响应**
```json
{
  "code": 200,
  "data": {
    "total": 15,
    "page": 1,
    "pageSize": 20,
    "templates": [
      {
        "templateId": "tmpl-uuid",
        "name": "抖音短视频模板",
        "description": "添加背景音乐 + 字幕 + 水印",
        "stepCount": 3,
        "isPublic": false,
        "createdAt": "2026-03-21T10:00:00Z",
        "updatedAt": "2026-03-21T10:00:00Z"
      }
    ]
  },
  "message": "success"
}
```

**测试用例**:
```python
def test_templates_list_success():
    """测试模板列表 - 正常流程"""
    response = client.get("/api/v1/templates?page=1&pageSize=10")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "total" in data
    assert "templates" in data

def test_templates_list_pagination():
    """测试模板列表 - 分页"""
    # 创建 25 个模板
    for i in range(25):
        client.post("/api/v1/templates", json={
            "name": f"模板{i}",
            "steps": [{"type": "add_music", "params": {}}]
        })
    
    # 第一页
    response = client.get("/api/v1/templates?page=1&pageSize=10")
    assert len(response.json()["data"]["templates"]) == 10
    
    # 第二页
    response = client.get("/api/v1/templates?page=2&pageSize=10")
    assert len(response.json()["data"]["templates"]) == 10
    
    # 第三页
    response = client.get("/api/v1/templates?page=3&pageSize=10")
    assert len(response.json()["data"]["templates"]) == 5
```

**优先级**: P0  
**工作量**: 0.5 人天

---

### 2.3 删除模板

#### DELETE /templates/:id

删除配置模板

**请求**
```http
DELETE /api/v1/templates/:templateId
```

**响应**
```json
{
  "code": 200,
  "message": "模板删除成功"
}
```

**错误码**
| 码 | 说明 |
|---|------|
| 4004 | 模板不存在 |

**测试用例**:
```python
def test_template_delete_success():
    """测试删除模板 - 正常流程"""
    # 先创建模板
    create_resp = client.post("/api/v1/templates", json={
        "name": "待删除模板",
        "steps": [{"type": "add_music", "params": {}}]
    })
    template_id = create_resp.json()["data"]["templateId"]
    
    # 删除模板
    response = client.delete(f"/api/v1/templates/{template_id}")
    assert response.status_code == 200
    
    # 验证已删除
    get_resp = client.get(f"/api/v1/templates/{template_id}")
    assert get_resp.status_code == 404

def test_template_delete_not_found():
    """测试删除模板 - 不存在"""
    response = client.delete("/api/v1/templates/non-existent-id")
    assert response.status_code == 404
    assert response.json()["code"] == 4004
```

**优先级**: P1  
**工作量**: 0.5 人天

---

## 三、素材库模块

### 3.1 音乐列表

#### GET /materials/music

获取音乐素材列表

**请求**
```http
GET /api/v1/materials/music?genre=pop&mood=energetic&page=1
```

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| genre | string | 否 | 音乐类型：pop/classical/electronic/ambient |
| mood | string | 否 | 情绪：happy/sad/energetic/calm |
| duration | string | 否 | 时长：short(<30s)/medium(30s-2m)/long(>2m) |
| page | integer | 否 | 页码，默认 1 |
| pageSize | integer | 否 | 每页数量，默认 20 |

**响应**
```json
{
  "code": 200,
  "data": {
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "music": [
      {
        "fileId": "music-uuid",
        "title": "Energetic Action",
        "artist": "Alex Grohl",
        "genre": "pop",
        "mood": "energetic",
        "duration": 180,
        "downloadUrl": "/api/v1/files/music-uuid/download",
        "previewUrl": "/api/v1/materials/music/music-uuid/preview"
      }
    ]
  },
  "message": "success"
}
```

**实现要点**:
- 预置免费音乐库（50+ 首）
- 支持分类筛选
- 支持 30 秒在线试听

**测试用例**:
```python
def test_music_list_success():
    """测试音乐列表 - 正常流程"""
    response = client.get("/api/v1/materials/music?page=1&pageSize=10")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "total" in data
    assert "music" in data

def test_music_list_filter_by_genre():
    """测试音乐列表 - 按类型筛选"""
    response = client.get("/api/v1/materials/music?genre=electronic")
    assert response.status_code == 200
    music_list = response.json()["data"]["music"]
    for music in music_list:
        assert music["genre"] == "electronic"

def test_music_list_filter_by_mood():
    """测试音乐列表 - 按情绪筛选"""
    response = client.get("/api/v1/materials/music?mood=energetic")
    assert response.status_code == 200
    music_list = response.json()["data"]["music"]
    for music in music_list:
        assert music["mood"] == "energetic"

def test_music_preview():
    """测试音乐试听"""
    response = client.get("/api/v1/materials/music/music-uuid/preview")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/mpeg"
```

**优先级**: P0  
**工作量**: 1.5 人天

---

### 3.2 模板列表

#### GET /materials/templates

获取视频模板列表

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
        "previewUrl": "/api/v1/templates/tmpl-uuid/preview.mp4",
        "downloadUrl": "/api/v1/files/tmpl-uuid/download"
      }
    ]
  },
  "message": "success"
}
```

**实现要点**:
- 预置视频模板（20+ 个）
- 支持分类筛选
- 支持在线预览

**测试用例**:
```python
def test_templates_list_success():
    """测试模板列表 - 正常流程"""
    response = client.get("/api/v1/materials/templates?type=intro")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "templates" in data

def test_templates_list_filter_by_type():
    """测试模板列表 - 按类型筛选"""
    response = client.get("/api/v1/materials/templates?type=outro")
    assert response.status_code == 200
    templates = response.json()["data"]["templates"]
    for tmpl in templates:
        assert tmpl["type"] == "outro"
```

**优先级**: P0  
**工作量**: 1 人天

---

### 3.3 上传素材

#### POST /materials/upload

用户上传自定义素材

**请求**
```http
POST /api/v1/materials/upload
Content-Type: multipart/form-data

file: <file>
type: music | template
category: pop | intro | ...
tags: tag1,tag2,tag3
```

**响应**
```json
{
  "code": 200,
  "data": {
    "fileId": "file-uuid",
    "fileName": "my_music.mp3",
    "fileType": "music",
    "category": "pop",
    "tags": ["tag1", "tag2", "tag3"],
    "uploadTime": "2026-03-21T10:00:00Z"
  },
  "message": "素材上传成功"
}
```

**测试用例**:
```python
def test_material_upload_music():
    """测试上传素材 - 音乐"""
    files = {'file': open('test_music.mp3', 'rb')}
    data = {'type': 'music', 'category': 'pop', 'tags': 'upbeat,energetic'}
    response = client.post("/api/v1/materials/upload", files=files, data=data)
    assert response.status_code == 200
    assert "fileId" in response.json()["data"]

def test_material_upload_template():
    """测试上传素材 - 模板"""
    files = {'file': open('test_intro.mp4', 'rb')}
    data = {'type': 'template', 'category': 'intro', 'tags': 'simple,clean'}
    response = client.post("/api/v1/materials/upload", files=files, data=data)
    assert response.status_code == 200

def test_material_upload_invalid_type():
    """测试上传素材 - 无效类型"""
    files = {'file': open('test.txt', 'rb')}
    data = {'type': 'invalid', 'category': 'test'}
    response = client.post("/api/v1/materials/upload", files=files, data=data)
    assert response.status_code == 400
```

**优先级**: P1  
**工作量**: 1 人天

---

## 四、系统模块

### 4.1 健康检查

#### GET /health

系统健康检查

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
    "version": "v2.0.7",
    "uptime": 86400,
    "timestamp": "2026-03-21T10:00:00Z",
    "checks": {
      "database": {"status": "ok", "latency": "5ms"},
      "storage": {"status": "ok", "used": "15.6GB", "total": "100GB"},
      "redis": {"status": "ok", "latency": "2ms"},
      "sora_api": {"status": "ok", "latency": "120ms"}
    }
  },
  "message": "success"
}
```

**测试用例**:
```python
def test_health_check_success():
    """测试健康检查 - 正常"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "healthy"
    assert "version" in data
    assert "checks" in data

def test_health_check_database_down():
    """测试健康检查 - 数据库异常"""
    # 模拟数据库异常
    response = client.get("/api/v1/health")
    data = response.json()["data"]
    assert data["checks"]["database"]["status"] == "ok"  # 或 "error"
```

**优先级**: P0  
**工作量**: 0.5 人天

---

### 4.2 系统信息

#### GET /system/info

获取系统详细信息

**请求**
```http
GET /api/v1/system/info
```

**响应**
```json
{
  "code": 200,
  "data": {
    "version": "v2.0.7",
    "buildTime": "2026-03-21T00:00:00Z",
    "environment": "production",
    "pythonVersion": "3.10.0",
    "fastapiVersion": "0.104.1",
    "stats": {
      "totalFiles": 342,
      "totalTasks": 1560,
      "totalScripts": 23,
      "totalBatches": 12,
      "storageUsed": "15.6GB",
      "storageTotal": "100GB"
    },
    "features": {
      "audioVoiceover": true,
      "asrSubtitle": true,
      "scriptGenerate": true,
      "storyboard": true,
      "aiVideo": true,
      "batchGenerate": true,
      "quotaManagement": true
    }
  },
  "message": "success"
}
```

**测试用例**:
```python
def test_system_info_success():
    """测试系统信息 - 正常流程"""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "version" in data
    assert "environment" in data
    assert "stats" in data
    assert "features" in data

def test_system_info_features():
    """测试系统信息 - 功能列表"""
    response = client.get("/api/v1/system/info")
    features = response.json()["data"]["features"]
    assert features["audioVoiceover"] == True
    assert features["asrSubtitle"] == True
    assert features["scriptGenerate"] == True
```

**优先级**: P1  
**工作量**: 0.5 人天

---

## 五、错误码补充

### 阶段三新增错误码

| 错误码 | 说明 | HTTP 状态 | 模块 |
|--------|------|----------|------|
| **仪表盘 (4000-4009)** |
| 4000 | 统计类型不支持 | 400 | 仪表盘 |
| **模板管理 (4010-4019)** |
| 4010 | 模板名称为空 | 400 | 模板 |
| 4011 | 处理步骤为空 | 400 | 模板 |
| 4012 | 步骤类型不支持 | 400 | 模板 |
| 4013 | 模板不存在 | 404 | 模板 |
| **素材库 (4020-4029)** |
| 4020 | 音乐类型不支持 | 400 | 素材 |
| 4021 | 音乐情绪不支持 | 400 | 素材 |
| 4022 | 模板类型不支持 | 400 | 素材 |
| 4023 | 素材格式不支持 | 400 | 素材 |
| 4024 | 素材不存在 | 404 | 素材 |
| **系统 (5000-5009)** |
| 5000 | 健康检查失败 | 503 | 系统 |
| 5004 | 服务不可用 | 503 | 系统 |

---

## 六、测试用例汇总

### 阶段三测试文件

| 文件 | 用例数 | 说明 |
|------|--------|------|
| test_dashboard.py | 8 | 仪表盘模块 |
| test_templates.py | 12 | 模板管理模块 |
| test_materials.py | 15 | 素材库模块 |
| test_system.py | 6 | 系统模块 |
| **总计** | **41** | |

### 测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| 仪表盘 | ≥90% |
| 模板管理 | ≥85% |
| 素材库 | ≥85% |
| 系统 | ≥90% |
| **总计** | **≥87%** |

---

## 七、实现优先级

### 第一批（P0 - 核心功能）

1. GET /dashboard/stats (0.5 人天)
2. GET /dashboard/recent (0.5 人天)
3. POST/GET /templates (1.5 人天)
4. GET /materials/music (1.5 人天)
5. GET /materials/templates (1 人天)
6. GET /health (0.5 人天)

**小计**: 5.5 人天

### 第二批（P1 - 增强功能）

1. DELETE /templates/:id (0.5 人天)
2. POST /materials/upload (1 人天)
3. GET /system/info (0.5 人天)

**小计**: 2 人天

### 第三批（P2 - 优化功能）

1. 音乐试听接口
2. 模板预览接口
3. 缓存优化

**小计**: 1.5 人天

---

## 八、开发计划

| 批次 | 功能 | 工作量 | 状态 |
|------|------|--------|------|
| 第一批 | P0 核心功能 | 5.5 人天 | ⏳ |
| 第二批 | P1 增强功能 | 2 人天 | ⏳ |
| 第三批 | P2 优化功能 | 1.5 人天 | ⏳ |
| **总计** | | **9 人天** | |

**注**: 阶段三前端开发需 25 人天，后端接口 9 人天可并行开发

---

**文档生成时间**: 2026-03-21 05:56 CST  
**下一步**: 确认后启动阶段三后端开发
