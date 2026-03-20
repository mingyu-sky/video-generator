# Video Generator 文档中心

**项目**: Sora Video Generator  
**版本**: v3.1  
**最后更新**: 2026-03-21

---

## 📚 文档目录

### 1. 需求文档 (`requirements/`)

| 文档 | 说明 | 状态 |
|------|------|------|
| [PHASED_PRD_v3.md](PHASED_PRD_v3.md) | 四阶段发展规划 (v3.1) | ✅ 已确认 |
| [PRODUCTER_REVIEW.md](PRODUCTER_REVIEW.md) | 产品评估报告 | ✅ 已完成 |
| [CODER_REVIEW.md](CODER_REVIEW.md) | 技术评估报告 | ✅ 已完成 |
| [CONFIG_DECISIONS.md](CONFIG_DECISIONS.md) | 配置决策确认单 | ✅ 已确认 |
| [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | 详细产品需求 | ✅ 已完成 |

### 2. 技术文档 (`docs/`)

| 文档 | 说明 | 负责人 | 状态 |
|------|------|--------|------|
| [API.md](API.md) | API 接口文档 | 后端开发 | ⏳ 待编写 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构设计 | 架构师 | ⏳ 待编写 |
| [DEPLOY.md](DEPLOY.md) | 部署文档 | 运维 | ⏳ 待编写 |
| [DATABASE.md](DATABASE.md) | 数据库设计 | 后端开发 | ⏳ 待编写 |

### 3. 测试文档 (`tests/`)

| 文档 | 说明 | 负责人 | 状态 |
|------|------|--------|------|
| [TESTING.md](TESTING.md) | 测试规范 | 测试工程师 | ⏳ 待编写 |
| [test_plan.md](test_plan.md) | 测试计划 | 测试工程师 | ⏳ 待编写 |
| [test_cases/](test_cases/) | 测试用例集 | 测试工程师 | ⏳ 待编写 |

### 4. 用户文档 (`docs/`)

| 文档 | 说明 | 负责人 | 状态 |
|------|------|--------|------|
| [USER_GUIDE.md](USER_GUIDE.md) | 用户使用手册 | 产品 | ⏳ 待编写 |
| [FAQ.md](FAQ.md) | 常见问题解答 | 客服 | ⏳ 待编写 |

---

## 📋 文档管理规范

### 版本控制

- **需求文档**: `vX.Y.Z` (主版本。次版本。修订版)
- **技术文档**: 跟随对应模块版本
- **变更日志**: 每个文档末尾记录变更历史

### 文档评审流程

```
起草 → 内部评审 → 修改 → 老板确认 → 归档 → 执行
```

### 文档更新规则

1. **需求变更**: 必须更新 PRD 并重新评审
2. **接口变更**: 必须同步更新 API 文档
3. **Bug 修复**: 记录到测试用例库
4. **版本发布**: 更新所有相关文档

### 文档存放规则

```
video-generator/
├── requirements/        # 需求文档（评审后不可随意修改）
├── docs/               # 技术和用户文档
├── tests/              # 测试文档和用例
├── src/                # 源代码
└── README.md           # 项目总览
```

---

## 🎯 研发流程

### 第一阶段开发流程

```
1. 阅读需求文档 (requirements/PHASED_PRD_v3.md)
   ↓
2. 技术方案设计 (docs/ARCHITECTURE.md)
   ↓
3. API 接口定义 (docs/API.md)
   ↓
4. 编码实现 (src/)
   ↓
5. 单元测试 (tests/)
   ↓
6. 集成测试
   ↓
7. 文档更新
   ↓
8. 提交评审
```

### 测试流程

```
1. 阅读测试规范 (tests/TESTING.md)
   ↓
2. 编写测试用例 (tests/test_cases/)
   ↓
3. 执行测试
   ↓
4. 提交 Bug 报告
   ↓
5. 验证修复
   ↓
6. 测试报告
```

---

## 📝 文档模板

### 需求变更申请

```markdown
## 变更申请

**变更内容**: 
**变更原因**: 
**影响范围**: 
**工作量评估**: 
**申请人**: 
**日期**: 
```

### API 文档格式

```markdown
## 接口名称

### 请求
- **URL**: `/api/v1/xxx`
- **Method**: `POST`
- **Body**: `{ "field": "value" }`

### 响应
```json
{
  "code": 200,
  "data": {},
  "message": "success"
}
```

### 错误码
| 码 | 说明 |
|---|------|
| 1001 | 文件格式不支持 |
```

### 测试用例格式

```markdown
## 测试用例 ID: TC-001

**功能**: 视频上传
**前置条件**: 无
**步骤**:
1. 上传 MP4 文件
2. 验证响应

**预期结果**: 返回 taskId
**实际结果**: 
**状态**: Pass/Fail
```

---

## 🔗 相关链接

- **GitHub 仓库**: https://github.com/mingyu-sky/video-generator
- **API 测试**: (待部署后补充)
- **项目管理**: (待补充)

---

**维护人**: 王秘书  
**最后更新**: 2026-03-21
