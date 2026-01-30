# 报告生成架构优化总结

## 问题分析

### 原有问题

**数据流问题**：

```text
旧版数据流（问题）:
validator → 返回完整验证结果（可能几千字）
timeline-builder → 返回完整时间轴结果（可能几千字）
predictor → 返回完整预测结果（可能几千字）
         ↓
event-analyzer 接收所有完整结果（上下文累积）
         ↓
report-assembler 再次接收所有完整结果
         ↓
问题：上下文过长 → 信息丢失
```

**具体问题**：

1. **上下文过长**：验证、时间轴、预测结果都在上下文中传递，占用大量 token
2. **信息丢失**：上下文过长导致关键信息被截断
3. **各部分无链接**：时间轴、预测、验证之间没有建立关联关系
4. **模板分割不彻底**：虽然 report-section-generator 是独立的，但 report-assembler 仍然需要读取所有数据并分发

## 优化方案

### 新版架构

**数据流**：

```text
新版数据流（优化）:
validator → 分析 → 保存到数据库 → 返回状态
timeline-builder → 分析 → 保存到数据库 → 返回状态
predictor → 分析 → 保存到数据库 → 返回状态
                      ↓
                report-assembler
                      ↓
         按需从数据库读取数据
                      ↓
         每个部分生成器只读自己需要的数据
```

**核心改进**：

1. **数据库存储**：各环节的结果保存到 `report_sections` 表
2. **按需读取**：报告生成时按需读取数据，避免上下文过长
3. **独立上下文**：每个部分生成器都有完整的独立上下文
4. **相互引用**：各部分可以通过 section_id 相互引用

## 实现内容

### 1. 数据库表结构

**report_sections 表**：

```sql
CREATE TABLE report_sections (
    section_id TEXT PRIMARY KEY,        -- 部分唯一标识
    section_type TEXT NOT NULL,         -- 部分类型
    session_id TEXT NOT NULL,           -- 会话ID
    event_name TEXT NOT NULL,           -- 事件名称
    category TEXT NOT NULL,             -- 类别
    content_data TEXT NOT NULL,         -- 内容数据（JSON）
    created_at TIMESTAMP,               -- 创建时间
    updated_at TIMESTAMP,               -- 更新时间
    status TEXT DEFAULT 'pending',      -- 状态
    error_message TEXT                  -- 错误信息
);
```

**支持的部分类型**：

- `validation`: 真实性验证结果
- `timeline`: 事件时间轴
- `prediction`: 趋势预测
- `summary`: 事件摘要
- `news`: 新闻列表
- `images`: 图片列表

### 2. 新增文件

**核心文件**：

1. `mcp_server/news_storage/core/report_sections_model.py`
   - 定义 `ReportSection` 数据模型
   - 提供内容模板（`ContentTemplates`）

2. `mcp_server/news_storage/core/report_sections_database.py`
   - 实现 `ReportSectionsDatabase` 类
   - 提供数据库操作方法

3. `mcp_server/news_storage/tools/report_sections_tools.py`
   - 提供 MCP 工具函数
   - 支持保存、读取、查询操作

### 3. 新增 MCP 工具

**工具列表**：

1. `save_report_section` - 保存报告部分到数据库
2. `get_report_section` - 获取单个报告部分
3. `get_all_report_sections` - 获取所有报告部分
4. `get_report_sections_summary` - 获取报告部分摘要（状态）
5. `mark_section_failed` - 标记部分失败

### 4. 更新的智能体提示词

**更新的文件**：

1. `prompts/event-validator.md`
   - 保存验证结果到数据库
   - 返回状态而非完整结果

2. `prompts/event-timeline.md`
   - 保存时间轴到数据库
   - 返回状态而非完整结果

3. `prompts/event-predictor.md`
   - 保存预测结果到数据库
   - 返回状态而非完整结果

4. `prompts/event-analyzer.md`
   - 并发启动三个分析任务
   - 使用 `get_report_sections_summary` 检查状态
   - 不再接收完整结果

5. `prompts/report-assembler.md`
   - 按需从数据库读取数据
   - 每个部分生成器只接收自己需要的数据
   - 完全避免上下文传递大量数据

## 使用示例

### Validator 保存结果

```python
# validator 完成验证后
await save_report_section(
    section_type="validation",
    session_id="20260130-abc123",
    event_name="美国大选",
    category="政治",
    content_data=json.dumps({
        "credibility_score": 85,
        "confidence_level": "高",
        "evidence_chain": [...],
        "analysis": "...",
        "sources": [...]
    })
)

# 返回
{
    "success": true,
    "section_id": "20260130-abc123_美国大选_validation",
    "message": "报告部分已保存: validation"
}
```

### Report-Assembler 按需读取

```python
# 1. 检查状态
summary = await get_report_sections_summary(
    session_id="20260130-abc123",
    event_name="美国大选"
)

# 2. 按需读取 validation
validation_data = await get_report_section(
    session_id="20260130-abc123",
    event_name="美国大选",
    section_type="validation"
)

# 3. 传递给部分生成器
await Task(
    "@report-section-generator",
    section_type="validation",
    raw_data=validation_data["content"],
    output_mode="write_to_file",
    output_file="./output/.../.parts/03-validation.md"
)
```

## 优势对比

| 特性 | 旧版本 | 新版本 |
|------|--------|--------|
| 数据传递 | 返回完整结果 | 保存到数据库，返回状态 |
| 上下文占用 | 高（所有结果在上下文） | 低（只传递状态） |
| 信息丢失 | 容易丢失 | 完整保留 |
| 数据读取 | 一次性读取所有 | 按需读取 |
| 部分独立性 | 低（共享上下文） | 高（独立上下文） |
| 相互引用 | 不支持 | 支持（通过 section_id） |
| 错误处理 | 一个失败全部失败 | 错误隔离，部分成功 |

## 后续建议

### 1. 部分之间相互引用

现在各部分可以通过 section_id 相互引用，例如：

- 时间轴可以引用验证结果：`验证可信度：85% (section_id: xxx_validation)`
- 预测可以引用时间轴：`基于时间轴中的关键节点 (section_id: xxx_timeline)`

### 2. 增量更新

如果某个部分的数据需要更新，可以直接更新数据库：

```python
await save_report_section(
    section_type="validation",
    ...,
    content_data=json.dumps(new_validation_data)
)
```

### 3. 数据复用

同一个事件的分析结果可以被多个报告复用，无需重复生成。

## 测试建议

1. **单元测试**：测试各个数据库操作函数
2. **集成测试**：测试完整的数据流（从 validator 到 report-assembler）
3. **性能测试**：对比旧版本和新版本的 token 使用量
4. **质量测试**：检查生成的报告是否完整，信息是否丢失

## 总结

这次优化从根本上解决了报告生成架构中的上下文过长问题：

1. **核心改变**：从"传递数据"改为"存储数据，按需读取"
2. **关键优势**：避免信息丢失，提高质量，降低成本
3. **架构改进**：各部分独立，可相互引用，易于扩展

这是一个**数据库驱动的报告生成架构**，是更可持续和可扩展的解决方案。
