# 第三阶段测试用例

**版本**: v3.0 (阶段三)  
**创建日期**: 2026-03-21  
**状态**: ⏳ 待执行  
**依据**: PHASE3_API.md

---

## 📊 测试用例总览

### 用例统计

| 模块 | 测试文件 | 用例数 | 优先级 | 覆盖率目标 |
|------|----------|--------|--------|-----------|
| 仪表盘 | test_dashboard.py | 8 | P0 | ≥90% |
| 模板管理 | test_templates.py | 12 | P0 | ≥85% |
| 素材库 | test_materials.py | 15 | P0 | ≥85% |
| 系统 | test_system.py | 6 | P0 | ≥90% |
| **总计** | **4 个文件** | **41** | | **≥87%** |

---

## 一、仪表盘模块测试

### 测试文件：`tests/test_dashboard.py`

#### TC-DASH-001: 仪表盘统计 - 正常流程

**优先级**: P0

**前置条件**: 系统中有任务、文件、剧本等数据

**步骤**:
1. 调用 `GET /api/v1/dashboard/stats`
2. 验证响应

**预期结果**:
- 返回 200 状态码
- 包含 tasks、files、scripts、batches、usage 统计
- 数据准确

**测试代码**:
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
    
    # 验证任务统计
    assert "total" in data["tasks"]
    assert "pending" in data["tasks"]
    assert "completed" in data["tasks"]
    
    # 验证文件统计
    assert "total" in data["files"]
    assert "videos" in data["files"]
    assert "storageUsed" in data["files"]
```

---

#### TC-DASH-002: 仪表盘统计 - 空数据

**优先级**: P1

**前置条件**: 数据库为空

**步骤**:
1. 清空所有数据
2. 调用 `GET /api/v1/dashboard/stats`
3. 验证响应

**预期结果**:
- 返回 200 状态码
- 所有统计值为 0

**测试代码**:
```python
def test_dashboard_stats_empty_data():
    """测试仪表盘统计 - 空数据"""
    # 清空数据库
    db.execute("DELETE FROM tasks")
    db.execute("DELETE FROM files")
    db.execute("DELETE FROM scripts")
    
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert data["tasks"]["total"] == 0
    assert data["files"]["total"] == 0
    assert data["scripts"]["total"] == 0
```

---

#### TC-DASH-003: 仪表盘统计 - 缓存机制

**优先级**: P2

**前置条件**: 无

**步骤**:
1. 第一次请求统计接口
2. 立即第二次请求统计接口
3. 比较响应时间

**预期结果**:
- 第二次请求应该更快（命中缓存）
- 两次数据一致

**测试代码**:
```python
def test_dashboard_stats_cache():
    """测试仪表盘统计 - 缓存机制"""
    # 第一次请求
    start = time.time()
    resp1 = client.get("/api/v1/dashboard/stats")
    first_time = time.time() - start
    
    # 立即第二次请求
    start = time.time()
    resp2 = client.get("/api/v1/dashboard/stats")
    second_time = time.time() - start
    
    # 缓存命中应该更快
    assert second_time < first_time
    
    # 数据应该一致
    assert resp1.json() == resp2.json()
```

---

#### TC-DASH-004: 最近使用 - 任务列表

**优先级**: P0

**测试代码**:
```python
def test_dashboard_recent_tasks():
    """测试最近使用 - 任务列表"""
    response = client.get("/api/v1/dashboard/recent?type=tasks&limit=5")
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert "tasks" in data
    assert len(data["tasks"]) <= 5
    
    # 验证任务字段
    if data["tasks"]:
        task = data["tasks"][0]
        assert "taskId" in task
        assert "type" in task
        assert "status" in task
        assert "createdAt" in task
```

---

#### TC-DASH-005: 最近使用 - 全部类型

**优先级**: P0

**测试代码**:
```python
def test_dashboard_recent_all():
    """测试最近使用 - 全部类型"""
    response = client.get("/api/v1/dashboard/recent?type=all&limit=10")
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert "tasks" in data
    assert "scripts" in data
    assert "batches" in data
```

---

#### TC-DASH-006: 最近使用 - 无效类型

**优先级**: P1

**测试代码**:
```python
def test_dashboard_recent_invalid_type():
    """测试最近使用 - 无效类型"""
    response = client.get("/api/v1/dashboard/recent?type=invalid")
    assert response.status_code == 400
    assert response.json()["code"] == 4000
```

---

#### TC-DASH-007: 最近使用 - 分页限制

**优先级**: P2

**测试代码**:
```python
def test_dashboard_recent_limit():
    """测试最近使用 - 分页限制"""
    # 创建 20 个任务
    for i in range(20):
        create_test_task()
    
    # 限制返回 5 个
    response = client.get("/api/v1/dashboard/recent?type=tasks&limit=5")
    assert response.status_code == 200
    assert len(response.json()["data"]["tasks"]) == 5
    
    # 限制返回 10 个
    response = client.get("/api/v1/dashboard/recent?type=tasks&limit=10")
    assert len(response.json()["data"]["tasks"]) == 10
    
    # 超过最大限制（50）
    response = client.get("/api/v1/dashboard/recent?type=tasks&limit=100")
    assert response.status_code == 400
```

---

#### TC-DASH-008: 仪表盘统计 - 并发请求

**优先级**: P2

**测试代码**:
```python
def test_dashboard_stats_concurrent():
    """测试仪表盘统计 - 并发请求"""
    import concurrent.futures
    
    def fetch_stats():
        return client.get("/api/v1/dashboard/stats")
    
    # 并发 10 个请求
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_stats) for _ in range(10)]
        results = [f.result() for f in futures]
    
    # 所有请求都应该成功
    for resp in results:
        assert resp.status_code == 200
    
    # 所有结果应该一致
    first_data = results[0].json()["data"]
    for resp in results[1:]:
        assert resp.json()["data"] == first_data
```

---

## 二、模板管理模块测试

### 测试文件：`tests/test_templates.py`

#### TC-TMPL-001: 保存模板 - 正常流程

**优先级**: P0

**测试代码**:
```python
def test_template_save_success():
    """测试保存模板 - 正常流程"""
    response = client.post("/api/v1/templates", json={
        "name": "抖音短视频模板",
        "description": "添加背景音乐 + 字幕",
        "steps": [
            {"type": "add_music", "params": {"volume": 0.3}},
            {"type": "add_subtitles", "params": {"fontSize": 20}}
        ],
        "isPublic": False
    })
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert "templateId" in data
    assert data["name"] == "抖音短视频模板"
```

---

#### TC-TMPL-002: 保存模板 - 名称为空

**优先级**: P0

**测试代码**:
```python
def test_template_save_empty_name():
    """测试保存模板 - 名称为空"""
    response = client.post("/api/v1/templates", json={
        "name": "",
        "steps": [{"type": "add_music", "params": {}}]
    })
    
    assert response.status_code == 400
    assert response.json()["code"] == 4010
```

---

#### TC-TMPL-003: 保存模板 - 步骤为空

**优先级**: P0

**测试代码**:
```python
def test_template_save_empty_steps():
    """测试保存模板 - 步骤为空"""
    response = client.post("/api/v1/templates", json={
        "name": "测试模板",
        "steps": []
    })
    
    assert response.status_code == 400
    assert response.json()["code"] == 4011
```

---

#### TC-TMPL-004: 保存模板 - 无效步骤类型

**优先级**: P0

**测试代码**:
```python
def test_template_save_invalid_step_type():
    """测试保存模板 - 无效步骤类型"""
    response = client.post("/api/v1/templates", json={
        "name": "测试模板",
        "steps": [{"type": "invalid_type", "params": {}}]
    })
    
    assert response.status_code == 400
    assert response.json()["code"] == 4012
```

---

#### TC-TMPL-005: 获取模板列表 - 正常流程

**优先级**: P0

**测试代码**:
```python
def test_templates_list_success():
    """测试获取模板列表 - 正常流程"""
    # 先创建几个模板
    for i in range(5):
        client.post("/api/v1/templates", json={
            "name": f"模板{i}",
            "steps": [{"type": "add_music", "params": {}}]
        })
    
    response = client.get("/api/v1/templates?page=1&pageSize=10")
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert "total" in data
    assert "templates" in data
    assert data["total"] >= 5
```

---

#### TC-TMPL-006: 获取模板列表 - 分页

**优先级**: P1

**测试代码**:
```python
def test_templates_list_pagination():
    """测试获取模板列表 - 分页"""
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

---

#### TC-TMPL-007: 删除模板 - 正常流程

**优先级**: P0

**测试代码**:
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
```

---

#### TC-TMPL-008: 删除模板 - 不存在

**优先级**: P1

**测试代码**:
```python
def test_template_delete_not_found():
    """测试删除模板 - 不存在"""
    response = client.delete("/api/v1/templates/non-existent-id")
    assert response.status_code == 404
    assert response.json()["code"] == 4013
```

---

#### TC-TMPL-009: 使用模板 - 应用到视频处理

**优先级**: P1

**测试代码**:
```python
def test_template_apply_to_video():
    """测试使用模板 - 应用到视频处理"""
    # 创建模板
    create_resp = client.post("/api/v1/templates", json={
        "name": "快速处理模板",
        "steps": [
            {"type": "add_music", "params": {"volume": 0.3}},
            {"type": "add_subtitles", "params": {"fontSize": 20}}
        ]
    })
    template_id = create_resp.json()["data"]["templateId"]
    
    # 使用模板处理视频
    response = client.post("/api/v1/video/process", json={
        "videoId": "test-video-id",
        "templateId": template_id,
        "outputName": "output.mp4"
    })
    
    assert response.status_code == 202
    assert "taskId" in response.json()["data"]
```

---

#### TC-TMPL-010: 模板验证 - 复杂步骤

**优先级**: P2

**测试代码**:
```python
def test_template_complex_steps():
    """测试模板验证 - 复杂步骤"""
    response = client.post("/api/v1/templates", json={
        "name": "复杂模板",
        "steps": [
            {"type": "add_music", "params": {"volume": 0.3, "fade": {"in": 2.0, "out": 2.0}}},
            {"type": "add_voiceover", "params": {"volume": 0.8, "alignMode": "start"}},
            {"type": "add_subtitles", "params": {"fontSize": 20, "position": "bottom"}},
            {"type": "image_overlay", "params": {"position": {"x": 50, "y": 50}, "opacity": 0.8}}
        ]
    })
    
    assert response.status_code == 200
```

---

#### TC-TMPL-011: 模板验证 - 参数边界值

**优先级**: P2

**测试代码**:
```python
def test_template_boundary_values():
    """测试模板验证 - 参数边界值"""
    # 音量边界值
    response = client.post("/api/v1/templates", json={
        "name": "边界测试",
        "steps": [
            {"type": "add_music", "params": {"volume": 0.0}},  # 最小值
            {"type": "add_music", "params": {"volume": 1.0}}   # 最大值
        ]
    })
    assert response.status_code == 200
    
    # 超出边界
    response = client.post("/api/v1/templates", json={
        "name": "边界测试",
        "steps": [
            {"type": "add_music", "params": {"volume": 1.5}}  # 超出最大值
        ]
    })
    assert response.status_code == 400
```

---

#### TC-TMPL-012: 模板列表 - 搜索功能

**优先级**: P2

**测试代码**:
```python
def test_templates_list_search():
    """测试模板列表 - 搜索功能"""
    # 创建不同名称的模板
    client.post("/api/v1/templates", json={
        "name": "抖音模板",
        "steps": [{"type": "add_music", "params": {}}]
    })
    client.post("/api/v1/templates", json={
        "name": "快手模板",
        "steps": [{"type": "add_music", "params": {}}]
    })
    
    # 搜索
    response = client.get("/api/v1/templates?search=抖音")
    assert response.status_code == 200
    templates = response.json()["data"]["templates"]
    assert len(templates) == 1
    assert templates[0]["name"] == "抖音模板"
```

---

## 三、素材库模块测试

### 测试文件：`tests/test_materials.py`

#### TC-MAT-001: 音乐列表 - 正常流程

**优先级**: P0

**测试代码**:
```python
def test_music_list_success():
    """测试音乐列表 - 正常流程"""
    response = client.get("/api/v1/materials/music?page=1&pageSize=10")
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert "total" in data
    assert "music" in data
```

---

#### TC-MAT-002: 音乐列表 - 按类型筛选

**优先级**: P0

**测试代码**:
```python
def test_music_list_filter_by_genre():
    """测试音乐列表 - 按类型筛选"""
    response = client.get("/api/v1/materials/music?genre=electronic")
    assert response.status_code == 200
    
    music_list = response.json()["data"]["music"]
    for music in music_list:
        assert music["genre"] == "electronic"
```

---

#### TC-MAT-003: 音乐列表 - 按情绪筛选

**优先级**: P0

**测试代码**:
```python
def test_music_list_filter_by_mood():
    """测试音乐列表 - 按情绪筛选"""
    response = client.get("/api/v1/materials/music?mood=energetic")
    assert response.status_code == 200
    
    music_list = response.json()["data"]["music"]
    for music in music_list:
        assert music["mood"] == "energetic"
```

---

#### TC-MAT-004: 音乐试听

**优先级**: P1

**测试代码**:
```python
def test_music_preview():
    """测试音乐试听"""
    response = client.get("/api/v1/materials/music/music-uuid/preview")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/mpeg"
    assert len(response.content) > 0  # 有音频数据
```

---

#### TC-MAT-005: 模板列表 - 正常流程

**优先级**: P0

**测试代码**:
```python
def test_templates_list_success():
    """测试模板列表 - 正常流程"""
    response = client.get("/api/v1/materials/templates?type=intro")
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert "templates" in data
```

---

#### TC-MAT-006: 模板列表 - 按类型筛选

**优先级**: P0

**测试代码**:
```python
def test_templates_list_filter_by_type():
    """测试模板列表 - 按类型筛选"""
    response = client.get("/api/v1/materials/templates?type=outro")
    assert response.status_code == 200
    
    templates = response.json()["data"]["templates"]
    for tmpl in templates:
        assert tmpl["type"] == "outro"
```

---

#### TC-MAT-007: 上传素材 - 音乐

**优先级**: P1

**测试代码**:
```python
def test_material_upload_music():
    """测试上传素材 - 音乐"""
    files = {'file': open('tests/fixtures/test_music.mp3', 'rb')}
    data = {'type': 'music', 'category': 'pop', 'tags': 'upbeat,energetic'}
    
    response = client.post("/api/v1/materials/upload", files=files, data=data)
    assert response.status_code == 200
    
    result = response.json()["data"]
    assert "fileId" in result
    assert result["fileType"] == "music"
```

---

#### TC-MAT-008: 上传素材 - 模板

**优先级**: P1

**测试代码**:
```python
def test_material_upload_template():
    """测试上传素材 - 模板"""
    files = {'file': open('tests/fixtures/test_intro.mp4', 'rb')}
    data = {'type': 'template', 'category': 'intro', 'tags': 'simple,clean'}
    
    response = client.post("/api/v1/materials/upload", files=files, data=data)
    assert response.status_code == 200
    
    result = response.json()["data"]
    assert "fileId" in result
    assert result["fileType"] == "template"
```

---

#### TC-MAT-009: 上传素材 - 无效类型

**优先级**: P1

**测试代码**:
```python
def test_material_upload_invalid_type():
    """测试上传素材 - 无效类型"""
    files = {'file': open('tests/fixtures/test.txt', 'rb')}
    data = {'type': 'invalid', 'category': 'test'}
    
    response = client.post("/api/v1/materials/upload", files=files, data=data)
    assert response.status_code == 400
    assert response.json()["code"] == 4023
```

---

#### TC-MAT-010: 上传素材 - 文件格式不支持

**优先级**: P1

**测试代码**:
```python
def test_material_upload_unsupported_format():
    """测试上传素材 - 文件格式不支持"""
    files = {'file': open('tests/fixtures/test.exe', 'rb')}
    data = {'type': 'music', 'category': 'pop'}
    
    response = client.post("/api/v1/materials/upload", files=files, data=data)
    assert response.status_code == 400
    assert response.json()["code"] == 4023
```

---

#### TC-MAT-011: 音乐列表 - 无效类型

**优先级**: P2

**测试代码**:
```python
def test_music_list_invalid_genre():
    """测试音乐列表 - 无效类型"""
    response = client.get("/api/v1/materials/music?genre=invalid")
    assert response.status_code == 400
    assert response.json()["code"] == 4020
```

---

#### TC-MAT-012: 模板预览

**优先级**: P2

**测试代码**:
```python
def test_template_preview():
    """测试模板预览"""
    response = client.get("/api/v1/materials/templates/tmpl-uuid/preview.mp4")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "video/mp4"
```

---

#### TC-MAT-013: 素材下载

**优先级**: P1

**测试代码**:
```python
def test_material_download():
    """测试素材下载"""
    response = client.get("/api/v1/materials/music/music-uuid/download")
    assert response.status_code == 200
    assert "Content-Disposition" in response.headers
    assert "attachment" in response.headers["Content-Disposition"]
```

---

#### TC-MAT-014: 素材库 - 收藏功能

**优先级**: P2

**测试代码**:
```python
def test_material_favorite():
    """测试素材收藏"""
    # 收藏音乐
    response = client.post("/api/v1/materials/music/music-uuid/favorite")
    assert response.status_code == 200
    
    # 获取收藏列表
    response = client.get("/api/v1/materials/favorites?type=music")
    assert response.status_code == 200
    favorites = response.json()["data"]["favorites"]
    assert any(f["fileId"] == "music-uuid" for f in favorites)
    
    # 取消收藏
    response = client.delete("/api/v1/materials/music/music-uuid/favorite")
    assert response.status_code == 200
```

---

#### TC-MAT-015: 素材库 - 使用统计

**优先级**: P2

**测试代码**:
```python
def test_material_usage_stats():
    """测试素材使用统计"""
    response = client.get("/api/v1/materials/music/music-uuid/stats")
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert "useCount" in data
    assert "favoriteCount" in data
    assert "downloadCount" in data
```

---

## 四、系统模块测试

### 测试文件：`tests/test_system.py`

#### TC-SYS-001: 健康检查 - 正常

**优先级**: P0

**测试代码**:
```python
def test_health_check_success():
    """测试健康检查 - 正常"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert data["status"] == "healthy"
    assert "version" in data
    assert "checks" in data
    
    # 验证各组件状态
    assert "database" in data["checks"]
    assert "storage" in data["checks"]
    assert "redis" in data["checks"]
```

---

#### TC-SYS-002: 健康检查 - 数据库异常

**优先级**: P1

**测试代码**:
```python
def test_health_check_database_down():
    """测试健康检查 - 数据库异常"""
    # 模拟数据库异常（通过 mock 或配置）
    with mock_database_down():
        response = client.get("/api/v1/health")
        assert response.status_code == 503
        
        data = response.json()["data"]
        assert data["status"] == "unhealthy"
        assert data["checks"]["database"]["status"] == "error"
```

---

#### TC-SYS-003: 系统信息 - 正常流程

**优先级**: P0

**测试代码**:
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
    
    # 验证版本信息
    assert data["version"] == "v2.0.7"
    
    # 验证功能列表
    assert data["features"]["audioVoiceover"] == True
    assert data["features"]["scriptGenerate"] == True
```

---

#### TC-SYS-004: 系统信息 - 功能列表完整性

**优先级**: P1

**测试代码**:
```python
def test_system_info_features():
    """测试系统信息 - 功能列表完整性"""
    response = client.get("/api/v1/system/info")
    features = response.json()["data"]["features"]
    
    # 验证所有阶段二功能都已启用
    expected_features = [
        "audioVoiceover",
        "asrSubtitle",
        "scriptGenerate",
        "storyboard",
        "aiVideo",
        "batchGenerate",
        "quotaManagement"
    ]
    
    for feature in expected_features:
        assert feature in features
        assert features[feature] == True
```

---

#### TC-SYS-005: 系统信息 - 统计信息

**优先级**: P1

**测试代码**:
```python
def test_system_info_stats():
    """测试系统信息 - 统计信息"""
    response = client.get("/api/v1/system/info")
    stats = response.json()["data"]["stats"]
    
    assert "totalFiles" in stats
    assert "totalTasks" in stats
    assert "storageUsed" in stats
    assert "storageTotal" in stats
    
    # 验证存储信息格式
    assert isinstance(stats["storageUsed"], str)
    assert stats["storageUsed"].endswith("GB") or stats["storageUsed"].endswith("MB")
```

---

#### TC-SYS-006: 健康检查 - 并发请求

**优先级**: P2

**测试代码**:
```python
def test_health_check_concurrent():
    """测试健康检查 - 并发请求"""
    import concurrent.futures
    
    def check_health():
        return client.get("/api/v1/health")
    
    # 并发 20 个请求
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_health) for _ in range(20)]
        results = [f.result() for f in futures]
    
    # 所有请求都应该成功
    for resp in results:
        assert resp.status_code == 200
```

---

## 五、集成测试

### 测试文件：`tests/test_phase3_integration.py`

#### TC-INT-001: 完整工作流 - 从模板到输出

**优先级**: P0

**测试代码**:
```python
def test_full_workflow_template_to_output():
    """测试完整工作流 - 从模板到输出"""
    # 1. 创建模板
    template_resp = client.post("/api/v1/templates", json={
        "name": "完整处理模板",
        "steps": [
            {"type": "add_music", "params": {"volume": 0.3}},
            {"type": "add_subtitles", "params": {"fontSize": 20}}
        ]
    })
    template_id = template_resp.json()["data"]["templateId"]
    
    # 2. 上传视频
    files = {'file': open('tests/fixtures/test_video.mp4', 'rb')}
    upload_resp = client.post("/api/v1/files/upload", files=files, data={'type': 'video'})
    video_id = upload_resp.json()["data"]["fileId"]
    
    # 3. 使用模板处理视频
    process_resp = client.post("/api/v1/video/process", json={
        "videoId": video_id,
        "templateId": template_id,
        "outputName": "output.mp4"
    })
    task_id = process_resp.json()["data"]["taskId"]
    
    # 4. 查询任务进度
    for _ in range(10):
        status_resp = client.get(f"/api/v1/tasks/{task_id}")
        status = status_resp.json()["data"]["status"]
        if status == "completed":
            break
        time.sleep(1)
    
    assert status == "completed"
    
    # 5. 验证输出
    result = status_resp.json()["data"]["result"]
    assert "outputId" in result
    assert "downloadUrl" in result
```

---

#### TC-INT-002: 完整工作流 - AI 短剧生成

**优先级**: P0

**测试代码**:
```python
def test_full_workflow_ai_drama():
    """测试完整工作流 - AI 短剧生成"""
    # 1. 生成剧本
    script_resp = client.post("/api/v1/ai/script/generate", json={
        "theme": "霸道总裁爱上我",
        "episodes": 5,
        "genre": "言情"
    })
    script_id = script_resp.json()["data"]["scriptId"]
    
    # 2. 生成分镜
    storyboard_resp = client.post("/api/v1/ai/storyboard/generate", json={
        "scriptId": script_id,
        "title": "霸道总裁爱上我"
    })
    storyboard_id = storyboard_resp.json()["data"]["storyboardId"]
    
    # 3. 批量生成视频
    batch_resp = client.post("/api/v1/ai/batch/generate", json={
        "scriptId": script_id,
        "episodeRange": {"start": 1, "end": 5},
        "parallelism": 2
    })
    batch_id = batch_resp.json()["data"]["batchId"]
    
    # 4. 查询批量进度
    for _ in range(30):
        status_resp = client.get(f"/api/v1/ai/batch/{batch_id}")
        progress = status_resp.json()["data"]["progress"]
        if progress == 100:
            break
        time.sleep(2)
    
    assert progress == 100
    
    # 5. 验证仪表盘统计
    dash_resp = client.get("/api/v1/dashboard/stats")
    stats = dash_resp.json()["data"]
    assert stats["batches"]["completed"] >= 1
```

---

## 六、性能测试

### 测试文件：`tests/test_phase3_performance.py`

#### TC-PERF-001: 仪表盘统计 - 响应时间

**优先级**: P1

**测试代码**:
```python
def test_dashboard_stats_response_time():
    """测试仪表盘统计 - 响应时间"""
    start = time.time()
    response = client.get("/api/v1/dashboard/stats")
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 0.5  # 500ms 以内
```

---

#### TC-PERF-002: 模板列表 - 大数据量

**优先级**: P2

**测试代码**:
```python
def test_templates_list_large_dataset():
    """测试模板列表 - 大数据量"""
    # 创建 1000 个模板
    for i in range(1000):
        client.post("/api/v1/templates", json={
            "name": f"模板{i}",
            "steps": [{"type": "add_music", "params": {}}]
        })
    
    # 测试分页查询性能
    start = time.time()
    response = client.get("/api/v1/templates?page=1&pageSize=50")
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 1.0  # 1 秒以内
    assert len(response.json()["data"]["templates"]) == 50
```

---

#### TC-PERF-003: 音乐列表 - 并发查询

**优先级**: P2

**测试代码**:
```python
def test_music_list_concurrent():
    """测试音乐列表 - 并发查询"""
    import concurrent.futures
    
    def fetch_music():
        return client.get("/api/v1/materials/music?page=1&pageSize=20")
    
    # 并发 50 个请求
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(fetch_music) for _ in range(50)]
        results = [f.result() for f in futures]
    elapsed = time.time() - start
    
    # 所有请求都应该成功
    for resp in results:
        assert resp.status_code == 200
    
    # 平均响应时间 < 1 秒
    assert elapsed / 50 < 1.0
```

---

## 七、测试执行计划

### 第一阶段：单元测试

```bash
# 仪表盘模块
pytest tests/test_dashboard.py -v

# 模板管理模块
pytest tests/test_templates.py -v

# 素材库模块
pytest tests/test_materials.py -v

# 系统模块
pytest tests/test_system.py -v
```

### 第二阶段：集成测试

```bash
# 集成测试
pytest tests/test_phase3_integration.py -v

# 性能测试
pytest tests/test_phase3_performance.py -v
```

### 第三阶段：全量测试

```bash
# 全部测试（阶段三）
pytest tests/test_dashboard.py tests/test_templates.py tests/test_materials.py tests/test_system.py -v

# 覆盖率报告
pytest tests/test_phase3*.py --cov=src --cov-report=html
```

---

## 八、测试数据准备

### 测试夹具（Fixtures）

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_template():
    """创建测试模板"""
    response = client.post("/api/v1/templates", json={
        "name": "测试模板",
        "steps": [{"type": "add_music", "params": {"volume": 0.3}}]
    })
    return response.json()["data"]["templateId"]

@pytest.fixture
def sample_music():
    """创建测试音乐"""
    return "music-uuid"

@pytest.fixture
def sample_video():
    """创建测试视频"""
    files = {'file': open('tests/fixtures/test_video.mp4', 'rb')}
    response = client.post("/api/v1/files/upload", files=files, data={'type': 'video'})
    return response.json()["data"]["fileId"]
```

### 测试资源

| 资源 | 路径 | 说明 |
|------|------|------|
| 测试视频 | tests/fixtures/test_video.mp4 | 10 秒 1080P 视频 |
| 测试音频 | tests/fixtures/test_music.mp3 | 30 秒音乐 |
| 测试图片 | tests/fixtures/test_image.png | 500x500 图片 |
| 测试文本 | tests/fixtures/test.txt | 测试文件 |

---

**文档生成时间**: 2026-03-21 05:56 CST  
**用例总数**: 41 个  
**下一步**: 开发完成后执行测试
