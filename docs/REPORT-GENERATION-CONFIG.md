# 报告生成系统配置验证文档

## 架构概述

本文档验证分步报告生成系统的配置和任务分配。

## 调用链

```
用户请求
  ↓
news-coordinator (coordinator.md)
  ↓
category-processor (category-handler.md)
  ↓
event-processor (event-analyzer.md)
  ↓
event-report-generator (report-generator.md) ← 入口点
  ↓
report-assembler (report-assembler.md) ← 协调器
  ↓
report-section-generator (report-section-generator.md) × N ← 部分生成器
```

## Agent 配置验证

### 1. event-report-generator

**文件**: [prompts/report-generator.md](../prompts/report-generator.md)
**配置**: `opencode.json`

```json
{
  "mode": "subagent",
  "description": "事件报告生成器（新版）- 生成单个事件的 Markdown 报告文件",
  "prompt": "{file:./prompts/report-generator.md}",
  "tools": {
    "write": true,
    "bash": false,
    "read": true
  },
  "permission": {
    "task": {
      "report-assembler": "allow"  ✓
    }
  }
}
```

**职责**:
- 接收报告生成请求
- 委托给 `report-assembler` 处理
- 返回最终结果

**调用**:
```text
@report-assembler 生成完整报告
```

---

### 2. report-assembler

**文件**: [prompts/report-assembler.md](../prompts/report-assembler.md)
**配置**: `opencode.json`

```json
{
  "mode": "subagent",
  "description": "报告组装器 - 分步生成并组装完整报告（纯文件操作）",
  "prompt": "{file:./prompts/report-assembler.md}",
  "tools": {
    "write": true,
    "bash": true,
    "read": true,
    "news-storage*": true,
    "downloader*": true
  },
  "permission": {
    "bash": {
      "mkdir *": "allow",
      "python *": "allow",
      "cat *": "allow",
      "echo *": "allow"
    },
    "task": {
      "report-section-generator": "allow"  ✓
    }
  }
}
```

**职责**:
- 读取事件的所有数据（新闻、验证、时间轴、预测）
- 创建 `.parts/` 临时文件夹
- 并行调用多个 `report-section-generator` 生成各部分
- 使用文件操作合并各部分为最终报告

**调用**:
```text
@report-section-generator 生成报告部分文件
```

**生成的部分**:
1. `01-summary.md` - 事件摘要
2. `02-news.md` - 新闻来源
3. `03-validation.md` - 真实性验证（可选）
4. `04-timeline.md` - 事件时间轴（可选）
5. `05-prediction.md` - 趋势预测（可选）
6. `06-images.md` - 相关图片（可选）

---

### 3. report-section-generator

**文件**: [prompts/report-section-generator.md](../prompts/report-section-generator.md)
**配置**: `opencode.json`

```json
{
  "mode": "subagent",
  "description": "报告部分生成器 - 独立生成报告的某个部分",
  "prompt": "{file:./prompts/report-section-generator.md}",
  "tools": {
    "write": true,
    "bash": true,
    "read": true
  },
  "permission": {
    "bash": {
      "mkdir *": "allow",
      "python *": "allow"
    }
  }
}
```

**职责**:
- 独立生成报告的**一个部分**
- 支持两种输出模式：
  - `return_content` - 返回内容（调试用）
  - `write_to_file` - 直接写入文件（生产环境推荐）

**支持的部分类型**:
- `summary-section` - 事件摘要
- `news-section` - 新闻来源
- `validation-section` - 真实性验证
- `timeline-section` - 事件时间轴
- `prediction-section` - 趋势预测
- `images-section` - 相关图片

---

## 目录结构

```
./output/{report_timestamp}/{category}新闻/{date}/资讯汇总与摘要/
├── {event_name}.md       ← 最终报告文件（通过文件合并生成）
├── {event_name}/         ← 事件图片文件夹
│   ├── 图片1.png
│   └── 图片2.png
└── .parts/               ← 临时部分文件夹（可删除）
    ├── 01-summary.md
    ├── 02-news.md
    ├── 03-validation.md
    ├── 04-timeline.md
    ├── 05-prediction.md
    ├── 06-images.md
    └── _merge_script.py  ← 合并脚本
```

---

## 权限链验证

### event-processor → event-report-generator

```json
// event-processor 权限
"permission": {
  "task": {
    "*": "allow"  ✓ 可以调用任何 agent
  }
}
```

### event-report-generator → report-assembler

```json
// event-report-generator 权限
"permission": {
  "task": {
    "report-assembler": "allow"  ✓ 可以调用 report-assembler
  }
}
```

### report-assembler → report-section-generator

```json
// report-assembler 权限
"permission": {
  "task": {
    "report-section-generator": "allow"  ✓ 可以调用 report-section-generator
  }
}
```

---

## 关键原则验证

### 1. 独立上下文 ✓

每个 `report-section-generator` 有独立的上下文，不会互相干扰。

### 2. 纯文件操作 ✓

- `report-section-generator` 写入文件，不返回内容
- `report-assembler` 使用文件合并，不读取内容到上下文

### 3. 并行执行 ✓

```python
# report-assembler 中并行启动所有任务
tasks = [
    Task(...),  # summary
    Task(...),  # news
    Task(...),  # validation
    Task(...),  # timeline
    Task(...),  # prediction
]
# 所有任务同时执行
```

### 4. 错误隔离 ✓

- 某个部分生成失败不影响其他部分
- 使用条件判断 `if parts_data["validation"]:` 来决定是否生成

### 5. 跨平台兼容 ✓

使用 Python 脚本进行文件合并，避免命令行差异：

```python
# 写入临时脚本文件
script_path = f"{parts_dir}/_merge_script.py"
write(script_path, merge_script)
bash(f'python "{script_path}"')
```

---

## 配置检查清单

- [x] `event-report-generator` 配置在 `opencode.json` 中
- [x] `report-assembler` 配置在 `opencode.json` 中
- [x] `report-section-generator` 配置在 `opencode.json` 中
- [x] 所有 agent 的 `prompt` 路径正确
- [x] 权限链完整：event-processor → event-report-generator → report-assembler → report-section-generator
- [x] `event-report-generator` 有调用 `report-assembler` 的权限
- [x] `report-assembler` 有调用 `report-section-generator` 的权限
- [x] `report-assembler` 有必要的 bash 权限（mkdir, python, cat, echo）
- [x] `report-section-generator` 有写入文件的权限
- [x] 所有调用名称正确（`@report-assembler`, `@report-section-generator`）
- [x] Python 脚本字符串转义正确
- [x] 跨平台兼容性问题已解决

---

## 测试建议

1. **单元测试**: 单独测试 `report-section-generator` 的每个部分类型
2. **集成测试**: 测试 `report-assembler` 的并行生成和文件合并
3. **端到端测试**: 测试从 `event-report-generator` 到最终报告的完整流程
4. **跨平台测试**: 在 Windows 和 Linux/macOS 上测试文件合并

---

## 故障排查

### 如果报告生成失败

1. 检查 `.parts/` 文件夹，查看哪些部分文件成功生成
2. 检查 `_merge_script.py` 是否正确创建
3. 手动执行合并脚本，查看错误信息
4. 检查权限配置是否正确

### 如果某个部分缺失

1. 检查输入数据是否包含该部分（validation/timeline/prediction）
2. 检查对应的 `report-section-generator` 任务是否失败
3. 查看 `.parts/` 文件夹确认部分文件是否存在

### 如果内容为空

1. 检查 `news-storage_search` 返回的数据
2. 检查传递给 `report-section-generator` 的原始数据
3. 调试时使用 `return_content` 模式查看生成内容

---

## 版本历史

- **v2.0** (2026-01-30): 分步生成架构
  - 新增 `report-assembler`
  - 新增 `report-section-generator`
  - 重构 `event-report-generator` 为委托模式
- **v1.0** (之前): 一次性生成架构（已废弃）
