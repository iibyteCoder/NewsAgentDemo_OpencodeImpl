# 调用参数验证文档

## 报告生成器参数需求对比

### 1. summary-report-generator

**期望的输入参数**：
- event_name: 事件名称
- session_id: 会话标识符
- category: 类别名称
- output_mode: 输出模式（return_content 或 write_to_file）
- output_file: 输出文件路径（write_to_file 模式需要）

**report-assembler 调用方式**（需要修正）：
```text
@summary-report-generator
event_name: {event_name}
session_id: {session_id}
category: {category}
output_mode: write_to_file
output_file: ./output/{report_timestamp}/{category}新闻/{date}/资讯汇总与摘要/.parts/01-summary.md
```

✅ **正确** - 参数完全匹配

---

### 2. news-report-generator

**期望的输入参数**：
- event_name: 事件名称
- session_id: 会话标识符
- category: 类别名称
- date: 日期
- output_mode: 输出模式
- output_file: 输出文件路径

**report-assembler 调用方式**（需要检查）：
```text
@news-report-generator
event_name: {event_name}
session_id: {session_id}
category: {category}
date: {date}
output_mode: write_to_file
output_file: ./output/{report_timestamp}/{category}新闻/{date}/资讯汇总与摘要/.parts/02-news.md
```

✅ **正确** - 参数完全匹配

---

### 3. validation-report-generator

**期望的输入参数**：
- event_name: 事件名称
- session_id: 会话标识符
- category: 类别名称
- output_mode: 输出模式
- output_file: 输出文件路径

**report-assembler 调用方式**：
```text
@validation-report-generator
event_name: {event_name}
session_id: {session_id}
category: {category}
output_mode: write_to_file
output_file: ./output/{report_timestamp}/{category}新闻/{date}/资讯汇总与摘要/.parts/03-validation.md
```

✅ **正确** - 参数完全匹配

---

### 4. timeline-report-generator

**期望的输入参数**：
- event_name: 事件名称
- session_id: 会话标识符
- category: 类别名称
- output_mode: 输出模式
- output_file: 输出文件路径

**report-assembler 调用方式**：
```text
@timeline-report-generator
event_name: {event_name}
session_id: {session_id}
category: {category}
output_mode: write_to_file
output_file: ./output/{report_timestamp}/{category}新闻/{date}/资讯汇总与摘要/.parts/04-timeline.md
```

✅ **正确** - 参数完全匹配

---

### 5. prediction-report-generator

**期望的输入参数**：
- event_name: 事件名称
- session_id: 会话标识符
- category: 类别名称
- output_mode: 输出模式
- output_file: 输出文件路径

**report-assembler 调用方式**：
```text
@prediction-report-generator
event_name: {event_name}
session_id: {session_id}
category: {category}
output_mode: write_to_file
output_file: ./output/{report_timestamp}/{category}新闻/{date}/资讯汇总与摘要/.parts/05-prediction.md
```

✅ **正确** - 参数完全匹配

---

### 6. images-report-generator

**期望的输入参数**：
- event_name: 事件名称
- session_id: 会话标识符
- category: 类别名称
- report_timestamp: 报告时间戳
- date: 日期
- news_data: 新闻数据（包含图片URL）
- output_mode: 输出模式
- output_file: 输出文件路径

**report-assembler 调用方式**：
```text
@images-report-generator
event_name: {event_name}
session_id: {session_id}
category: {category}
report_timestamp: {report_timestamp}
date: {date}
news_data: {从数据库读取的新闻数据}
output_mode: write_to_file
output_file: ./output/{report_timestamp}/{category}新闻/{date}/资讯汇总与摘要/.parts/06-images.md
```

✅ **正确** - 参数完全匹配，但需要实际传递 news_data

---

## 关键检查点

### ✅ 已验证正确的部分

1. **opencode.json 权限配置** - report-assembler 有权限调用所有6个报告生成智能体
2. **参数名称匹配** - 所有调用参数与期望参数名称一致
3. **文件路径格式** - 输出文件路径符合预期结构

### ⚠️ 需要确保的部分

1. **占位符替换** - report-assembler 需要将占位符替换为实际值
2. **并行调用** - 使用 Task 工具并行调用6个智能体
3. **news_data传递** - images-report-generator 需要实际传递新闻数据

---

## 推荐的调用实现

report-assembler 应该这样实现并行调用：

```python
# 阶段3：并行生成各部分文件

parts_to_generate = []

# 必须生成的部分
parts_to_generate.append({
    "agent": "summary-report-generator",
    "params": {
        "event_name": event_name,
        "session_id": session_id,
        "category": category,
        "output_mode": "write_to_file",
        "output_file": f"./output/{report_timestamp}/{category}新闻/{date}/资讯汇总与摘要/.parts/01-summary.md"
    }
})

parts_to_generate.append({
    "agent": "news-report-generator",
    "params": {
        "event_name": event_name,
        "session_id": session_id,
        "category": category,
        "date": date,
        "output_mode": "write_to_file",
        "output_file": f"./output/{report_timestamp}/{category}新闻/{date}/资讯汇总与摘要/.parts/02-news.md"
    }
})

# 可选部分（根据数据状态）
if validation_exists:
    parts_to_generate.append({...})

if timeline_exists:
    parts_to_generate.append({...})

if prediction_exists:
    parts_to_generate.append({...})

# 如果有新闻数据，生成图片部分
if news_data:
    parts_to_generate.append({
        "agent": "images-report-generator",
        "params": {
            "event_name": event_name,
            "session_id": session_id,
            "category": category,
            "report_timestamp": report_timestamp,
            "date": date,
            "news_data": news_data,
            "output_mode": "write_to_file",
            "output_file": f"./output/{report_timestamp}/{category}新闻/{date}/资讯汇总与摘要/.parts/06-images.md"
        }
    })

# 并行调用所有部分
for part in parts_to_generate:
    task(f"@{part['agent']} {format_params(part['params'])}")
```

---

## 完整的调用示例

假设实际参数为：
- event_name = "国际金价剧烈波动"
- session_id = "20260130-abc12345"
- category = "国际金融"
- report_timestamp = "report_20260130_153000"
- date = "2026-01-30"

**实际调用**：

```
@summary-report-generator
event_name: 国际金价剧烈波动
session_id: 20260130-abc12345
category: 国际金融
output_mode: write_to_file
output_file: ./output/report_20260130_153000/国际金融新闻/2026-01-30/资讯汇总与摘要/.parts/01-summary.md
```

这个调用方式：
1. ✅ 符合 OpenCode 的 @agent 调用语法
2. ✅ 参数名称与智能体期望一致
3. ✅ 文件路径结构正确
4. ✅ opencode.json 已授权此调用

---

*验证完成时间：2026-01-30*
