# Video Generator API 开发文档

## 项目结构

```
video-generator/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI 应用入口
│   ├── services/
│   │   ├── __init__.py
│   │   └── file_service.py  # 文件管理服务
│   └── models/
│       └── __init__.py
├── tests/
│   ├── test_file_management.py  # 单元测试
│   ├── test_cases.md            # 测试用例文档
│   └── bug_tracking.md          # 缺陷管理文档
├── uploads/                     # 文件存储目录
│   ├── videos/
│   ├── audio/
│   ├── images/
│   ├── subtitles/
│   └── metadata/
├── requirements-api.txt         # API 依赖
├── start.sh                     # 启动脚本
└── docs/
    └── API.md                   # API 文档
```

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-api.txt
```

### 2. 启动服务

```bash
./start.sh
```

或手动启动：

```bash
source venv/bin/activate
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 15321 --reload
```

### 3. 访问 API 文档

启动后访问：http://localhost:15321/docs

## API 接口

### 文件管理模块

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/v1/files/upload | POST | 上传文件 |
| /api/v1/files | GET | 获取文件列表 |
| /api/v1/files/:id | GET | 获取文件详情 |
| /api/v1/files/:id/download | GET | 下载文件 |
| /api/v1/files/:id | DELETE | 删除文件 |
| /api/v1/files/batch-delete | POST | 批量删除 |

### 系统接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/v1/health | GET | 健康检查 |

## 运行测试

```bash
source venv/bin/activate
python -m pytest tests/test_file_management.py -v
```

## 开发进度

### 迭代 1 - 文件管理模块 ✅

- [x] 搭建 FastAPI 开发环境
- [x] 实现文件上传接口
- [x] 实现文件列表接口
- [x] 实现文件详情接口
- [x] 实现文件下载接口
- [x] 实现文件删除接口
- [x] 实现批量删除接口
- [x] 编写单元测试（16 个用例，100% 通过）
- [x] 代码提交到 Git

**测试结果**: 16/16 通过  
**发现 Bug**: 0 个

## 错误码

| 错误码 | 说明 | HTTP 状态 |
|--------|------|----------|
| 1001 | 文件格式不支持 | 400 |
| 1002 | 文件大小超限 | 400 |
| 1003 | 文件损坏 | 400 |
| 1004 | 文件类型不匹配 | 400 |
| 1005 | 文件不存在 | 404 |
| 5003 | 内部服务器错误 | 500 |

## 下一步计划

### 迭代 2 - 任务管理模块

- [ ] GET /tasks/:id - 查询任务进度
- [ ] DELETE /tasks/:id - 取消任务
- [ ] POST /tasks/batch-query - 批量查询任务

### 迭代 3 - 视频处理模块

- [ ] POST /video/concat - 视频拼接
- [ ] POST /video/text-overlay - 添加文字特效
- [ ] POST /video/image-overlay - 添加图片水印
- [ ] POST /video/add-music - 添加背景音乐

## 技术栈

- **Web 框架**: FastAPI 0.80+
- **Python**: 3.10+
- **异步**: asyncio
- **数据验证**: Pydantic
- **测试**: pytest + pytest-asyncio
- **视频处理**: moviepy, ffmpeg-python
