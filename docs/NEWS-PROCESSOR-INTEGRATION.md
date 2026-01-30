# News-Processor 集成说明

## 概述

新增 `@news-processor` 智能体，负责单条新闻数据的预处理和时间格式化，确保所有新闻数据格式统一。

## 核心职责

**@news-processor 的主要任务**：

1. ⭐ **时间格式化**（最重要）
   - 将任意格式的 `publish_time` 转换为标准格式：`YYYY-MM-DD HH:MM:SS`
   - 处理相对时间（"2小时前"、"30分钟前"）
   - 处理中文日期（"2026年1月30日"）
   - 补全缺失的时间部分（"2026-01-30" → "2026-01-30 00:00:00"）

2. **数据清洗**
   - 标题：去除装饰符号、合并空格、去除来源前缀
   - 摘要：去除 HTML 标签、限制长度
   - 来源：标准化网站名称
   - 作者：去除"记者"、"编辑"等前缀
   - 关键词和标签：去重

## 集成位置

### 1. category-handler.md

**在阶段1（搜索新闻并保存）中集成**：

- 搜索到新闻后，对每条新闻调用 `@news-processor` 进行预处理
- 确保时间格式统一后再保存到数据库

**调用方式**：

```text
@news-processor 处理这条新闻：
{
  "title": "...",
  "url": "...",
  "publish_time": "2026年1月30日 14:30",
  "source": "新华网"
}
session_id={session_id}
category={category}
```

### 2. event-validator.md

**主动探索型智能体**：

- 每轮搜索后必须调用 `@news-processor` 处理搜索结果
- 确保验证性数据的时间格式统一

### 3. event-predictor.md

**主动探索型智能体**：

- 每轮搜索后必须调用 `@news-processor` 处理搜索结果
- 确保预测性数据的时间格式统一

### 4. event-timeline.md

**主动探索型智能体**：

- 每轮搜索后必须调用 `@news-processor` 处理搜索结果
- 确保时间轴数据的时间格式统一

## 数据流

```
搜索结果
  ↓
@news-processor (时间格式化 + 数据清洗)
  ↓
news-storage_save (保存到数据库)
  ↓
后续分析（聚合、验证、时间轴、预测）
```

## 为什么需要 news-processor

### 问题

不同来源的新闻时间格式不统一：
- "2026-01-30"
- "2026年1月30日"
- "2小时前"
- "今天 14:30"

### 影响

- 数据库无法正确按日期筛选
- 时间轴构建不准确
- 趋势预测偏差

### 解决方案

在数据保存前统一格式化为：`YYYY-MM-DD HH:MM:SS`

## 使用原则

1. **必须使用** - 所有新闻数据在保存前必须经过 `@news-processor` 处理
2. **时间优先** - 时间格式化是最重要的任务
3. **批量处理** - 可以并发处理多条新闻
4. **错误容忍** - 处理失败时记录原因但继续

## 注意事项

- `@news-processor` 是 subagent，通过 Task 工具调用
- 必须传递 `session_id` 和 `category` 参数
- 输入可以是原始数据对象或 URL
- 返回处理结果包含变更记录和清洗后的数据

## 示例工作流

```
1. 搜索新闻 → 获取 30 条结果
2. 对每条新闻调用 @news-processor
3. 等待所有处理完成
4. 批量保存到数据库
5. 继续后续流程（聚合、分析等）
```

## 配置文件

- **定义**: `prompts/news-processor.md`
- **备份**: `prompts/backup/news-processor.md`
- **集成位置**:
  - `prompts/category-handler.md`
  - `prompts/event-validator.md`
  - `prompts/event-predictor.md`
  - `prompts/event-timeline.md`
