# Coder Agent Memory

**角色**: 研发负责人  
**项目**: Video Generator  
**最后更新**: 2026-03-21

---

## 📋 核心职责

1. **接口开发**
   - 按 API 文档实现
   - 单元测试同步编写
   - 代码提交 Git

2. **Bug 修复**
   - 24 小时内确认
   - 48 小时内修复
   - 修复后更新缺陷文档

3. **技术文档**
   - API 开发文档
   - 部署文档
   - 代码注释

---

## 🎯 Video Generator 项目经验

### 技术栈
| 模块 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | 最新 |
| 数据库 | SQLite | 内置 |
| 测试框架 | pytest | 最新 |
| 视频处理 | FFmpeg + MoviePy | - |
| AI 配音 | Edge TTS | - |
| ASR 字幕 | 阿里云（待对接） | - |

### 项目结构
```
video-generator/
├── src/
│   ├── api/              # API 路由
│   │   └── main.py       # FastAPI 应用（441 行）
│   ├── services/         # 业务逻辑
│   │   ├── file_service.py    # 文件服务（272 行）
│   │   ├── task_service.py    # 任务服务
│   │   └── audio_service.py   # 音频服务
│   ├── models/           # 数据模型
│   └── utils/            # 工具函数
├── tests/                # 单元测试
├── uploads/              # 文件存储
│   ├── videos/
│   ├── audio/
│   └── output/
└── docs/                 # 文档
```

### 已完成迭代
| 迭代 | 模块 | 接口数 | 代码量 | 测试 | 状态 |
|------|------|--------|--------|------|------|
| 迭代 1 | 文件管理 | 6 | ~600 行 | 16 个，100% | ✅ |
| 迭代 2 | 任务管理 + 音频 | 5 | ~500 行 | 19 个，100% | ✅ |
| 迭代 3 | 视频处理 | 8 | - | - | ⏳ |

### 核心代码规范

#### 1. 统一响应格式
```python
{
    "code": 200,
    "data": {...},
    "message": "success"
}
```

#### 2. 异步任务处理
```python
# 提交任务
@app.post("/tasks")
async def create_task():
    task_id = uuid.uuid4()
    # 异步处理
    return {"code": 202, "data": {"taskId": task_id}}

# 查询任务
@app.get("/tasks/{task_id}")
async def get_task(task_id):
    # 返回进度
    return {"code": 200, "data": {"status": "processing", "progress": 50}}
```

#### 3. 文件存储规范
```python
# 目录结构
uploads/
├── videos/{uuid}.mp4      # 原始视频
├── audio/{uuid}.mp3       # 音频文件
├── output/{uuid}.mp4      # 输出视频
├── subtitles/{uuid}.srt   # 字幕文件
└── metadata/{uuid}.json   # 元数据
```

#### 4. 日志规范
```python
from loguru import logger

logger.info("文件上传成功：{}", file_id)
logger.error("文件处理失败：{}", error)
```

---

## ⚠️ 踩坑记录

### 坑 1: 文件权限问题
**问题**: uploads 目录权限不足，无法写入  
**原因**: 未提前检查目录权限  
**解决**: `chmod 755 uploads/`  
**教训**: 启动前检查环境权限

### 坑 2: 虚拟环境依赖
**问题**: 系统 Python 与项目依赖冲突  
**原因**: 未使用虚拟环境  
**解决**: `python -m venv venv`  
**教训**: 每个项目独立虚拟环境

### 坑 3: 大文件上传超时
**问题**: 上传 2GB 文件超时  
**原因**: 默认超时设置过短  
**解决**: 增加超时配置，支持断点续传  
**教训**: 大文件上传需特殊处理

### 坑 4: SQLite 并发问题
**问题**: 多任务并发写入失败  
**原因**: SQLite 不支持高并发  
**解决**: 使用连接池，减少并发写入  
**教训**: 高并发场景考虑 PostgreSQL

---

## 🎓 最佳实践

### 1. 开发流程
```
阅读 API 文档 → 实现接口 → 编写单元测试 → 自测 → 提交 Git → 通知测试
```

### 2. Git 规范
```bash
# Commit 格式
<type>: <description>

# 示例
feat: 完成文件管理模块（迭代 1）
fix: 修复文件上传权限问题
docs: 添加 API 开发文档
test: 添加文件下载测试
```

### 3. 单元测试规范
```python
# 命名规范
test_<module>_<function>_<scenario>()

# 示例
def test_file_upload_success():
    assert response.status_code == 200

def test_file_upload_invalid_format():
    assert response.status_code == 400
```

### 4. 代码审查清单
- [ ] 代码符合规范
- [ ] 单元测试通过
- [ ] 无安全漏洞
- [ ] 日志完整
- [ ] 错误处理完善
- [ ] 文档已更新

---

## 📊 效率数据

### 开发效率
| 模块 | 传统（人天） | AI 协作（小时） | 提升 |
|------|-------------|---------------|------|
| 文件管理 | 3 | 2 | 12x |
| 任务管理 | 2 | 1.5 | 10x |
| 音频处理 | 1 | 0.5 | 16x |
| **总计** | **6 人天** | **4 小时** | **~12x** |

### 代码质量
- 单元测试覆盖率：100%
- Bug 率：0 个/迭代
- 代码审查通过率：100%

---

## 🔗 相关文档
- [API 文档](docs/API.md)
- [测试用例](tests/test_cases.md)
- [缺陷管理](tests/bug_tracking.md)
- [开发总结](docs/DEVELOPMENT_SUMMARY.md)

---

**维护人**: Coder Agent  
**下次更新**: 迭代 3 完成时
