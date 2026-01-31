# 新闻来源模板

## 模板格式

## 今日新闻

{today_news}

## 相关新闻

{related_news}

---

**统计信息**：

- 今日新闻：{today_count}条
- 相关新闻：{related_count}条
- 总计：{total_count}条
- 主要来源：{main_sources}

---

## 说明

### 单条新闻格式

```markdown
### {sequence}. [{title}]({url})

- **来源**：{source}
- **时间**：{publish_time}
- **摘要**：{summary}
```

### 占位符说明

- `{today_news}` - 今日新闻内容列表
- `{related_news}` - 相关新闻内容列表
- `{today_count}` - 今日新闻数量
- `{related_count}` - 相关新闻数量
- `{total_count}` - 总新闻数量
- `{main_sources}` - 主要来源列表

### 单条新闻字段

- `{sequence}` - 序号（1、2、3...）
- `{title}` - 新闻标题
- `{url}` - 新闻链接
- `{source}` - 媒体名称
- `{publish_time}` - 发布时间
- `{summary}` - 新闻摘要
