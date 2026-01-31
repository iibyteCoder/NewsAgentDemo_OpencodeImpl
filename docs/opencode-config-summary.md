# OpenCode 配置总结

## 智能体架构总览

### 数据生成智能体（3个）

负责收集数据并保存到数据库：

| 智能体 | opencode.json key | prompt文件 | 工具权限 |
|--------|------------------|-----------|---------|
| **validator** | `validator` | `event-validator.md` | web-browser_multi_search_tool, news-storage* |
| **timeline-builder** | `timeline-builder` | `event-timeline.md` | web-browser_multi_search_tool, news-storage* |
| **predictor** | `predictor` | `event-predictor.md` | web-browser_multi_search_tool, news-storage* |

**特点**：
- 主动搜索型（使用web-browser_multi_search_tool）
- 保存结果到数据库（使用news-storage*）
- **没有** fetch_article_content权限（必须通过news-processor）

---

### 报告生成智能体（6个）

负责从数据库读取数据并生成报告部分：

| 智能体 | opencode.json key | prompt文件 | maxSteps | 工具权限 |
|--------|------------------|-----------|----------|---------|
| **summary-report-generator** | `summary-report-generator` | `summary-report-generator.md` | 6 | write, read, news-storage* |
| **news-report-generator** | `news-report-generator` | `news-report-generator.md` | 8 | write, read, news-storage* |
| **validation-report-generator** | `validation-report-generator` | `validation-report-generator.md` | 8 | write, read, news-storage* |
| **timeline-report-generator** | `timeline-report-generator` | `timeline-report-generator.md` | 8 | write, read, news-storage* |
| **prediction-report-generator** | `prediction-report-generator` | `prediction-report-generator.md` | 8 | write, read, news-storage* |
| **images-report-generator** | `images-report-generator` | `images-report-generator.md` | 10 | write, bash, read, downloader*, news-storage* |

**特点**：
- 从数据库读取数据（使用news-storage*）
- 直接写入文件（使用write）
- **没有**搜索权限（不进行搜索）

---

### 核心协调智能体

| 智能体 | opencode.json key | prompt文件 | 职责 |
|--------|------------------|-----------|------|
| **report-assembler** | `report-assembler` | `report-assembler.md` | 并行调用6个报告生成智能体，组装最终报告 |
| **event-processor** | `event-processor` | `event-analyzer.md` | 并发处理单个事件的验证、时间轴、预测 |

---

## 调用链路

### 完整工作流程

```
1. category-processor
   └─> event-aggregator
       └─> event-processor
           ├─> validator (数据生成) → 保存到数据库
           ├─> timeline-builder (数据生成) → 保存到数据库
           └─> predictor (数据生成) → 保存到数据库
           └─> event-report-generator
               └─> report-assembler
                   ├─> summary-report-generator (报告生成)
                   ├─> news-report-generator (报告生成)
                   ├─> validation-report-generator (报告生成)
                   ├─> timeline-report-generator (报告生成)
                   ├─> prediction-report-generator (报告生成)
                   └─> images-report-generator (报告生成)
```

---

## report-assembler 的权限配置

### task权限（已更新）

```json
"permission": {
  "task": {
    "summary-report-generator": "allow",
    "news-report-generator": "allow",
    "validation-report-generator": "allow",
    "timeline-report-generator": "allow",
    "prediction-report-generator": "allow",
    "images-report-generator": "allow"
  }
}
```

**说明**：
- ✅ 允许调用所有6个专门的报告生成智能体
- ❌ 不再允许调用通用的 `report-section-generator`

### bash权限

```json
"bash": {
  "mkdir *": "allow",
  "python *": "allow",
  "cat *": "allow",
  "echo *": "allow"
}
```

**用途**：
- `mkdir *` - 创建.parts文件夹和图片文件夹
- `python *` - 执行Python脚本合并文件
- `cat *` - 查看文件内容
- `echo *` - 输出内容到文件

---

## 工具权限矩阵

### news-storage* 权限

| 智能体 | news-storage_search | news-storage_save | news-storage_get_report_section |
|--------|-------------------|------------------|-------------------------------|
| category-processor | ✅ | ✅ | ❌ |
| news-processor | ❌ | ✅ | ❌ |
| validator | ✅ | ❌ | ✅ |
| timeline-builder | ✅ | ❌ | ✅ |
| predictor | ✅ | ❌ | ✅ |
| event-processor | ✅ | ❌ | ✅ |
| report-assembler | ✅ | ❌ | ✅ |
| summary-report-generator | ✅ | ❌ | ❌ |
| news-report-generator | ✅ | ❌ | ❌ |
| validation-report-generator | ❌ | ❌ | ✅ |
| timeline-report-generator | ❌ | ❌ | ✅ |
| prediction-report-generator | ❌ | ❌ | ✅ |
| images-report-generator | ❌ | ❌ | ❌ |

### web-browser* 权限

| 工具 | 允许的智能体 |
|------|-------------|
| web-browser_multi_search_tool | validator, timeline-builder, predictor |
| web-browser_fetch_article_content | **仅** news-processor |

**关键设计**：
- 数据生成智能体（validator等）**没有** fetch_article_content权限
- 必须通过 @news-processor 获取文章内容
- news-processor 是唯一可以直接获取文章正文的智能体

---

## 环境变量

所有智能体共享的环境变量：

```json
"env": {
  "OPENCODE_SESSION_ID": "{date:YYYYMMDD}-{uuid:8}",
  "OPENCODE_REPORT_TIMESTAMP": "report_{date:YYYYMMDD}_{time:HHMMSS}"
}
```

**用途**：
- `OPENCODE_SESSION_ID` - 会话标识符，用于区分不同的收集任务
- `OPENCODE_REPORT_TIMESTAMP` - 报告时间戳，用于生成报告文件夹名称

---

## 验证检查清单

- ✅ 6个报告生成智能体已添加到 opencode.json
- ✅ report-assembler 的 task 权限已更新
- ✅ 所有智能体的工具权限配置正确
- ✅ 数据生成智能体只能通过 news-processor 获取文章内容
- ✅ 报告生成智能体从数据库读取数据，不进行搜索
- ✅ report-assembler 有权限调用所有6个报告生成智能体
- ✅ 环境变量配置正确

---

## 关键设计原则

1. **职责分离** - 数据生成和报告生成完全分离
2. **权限最小化** - 每个智能体只拥有必需的工具权限
3. **强制使用模板** - 每个报告生成智能体必须遵循特定模板
4. **强制来源引用** - 所有结论必须包含具体新闻来源
5. **并行执行** - 6个报告生成智能体并行调用，提高效率
6. **错误隔离** - 某个部分失败不影响其他部分

---

*最后更新：2026-01-30*
