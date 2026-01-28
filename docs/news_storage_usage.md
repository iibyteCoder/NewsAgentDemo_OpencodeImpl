# News Storage MCP Server - 使用指南

## 功能概述

新闻存储MCP服务器提供SQLite数据库持久化存储和检索功能。

## 新增功能 ✨

### 1. 模糊查询
- `keyword` 参数支持对**标题、事件名称、摘要、内容**的模糊匹配
- 使用 `LIKE %keyword%` 进行模糊查询

**示例：**
```python
# 搜索标题或事件名称中包含"AI"的新闻
news_storage_search(keyword="AI")

# 搜索事件名称中包含"AI技术"的新闻
news_storage_search(keyword="AI技术")
```

### 2. 更新事件名称
提供两个工具来更新新闻的事件名称：

#### `news_storage_update_event_name`
更新单条新闻的事件名称

```python
news_storage_update_event_name(
    url="https://example.com/news/123",
    event_name="2026年AI技术突破事件"
)
```

#### `news_storage_batch_update_event_name`
批量更新多条新闻的事件名称

```python
urls = '["url1", "url2", "url3"]'
news_storage_batch_update_event_name(
    urls=urls,
    event_name="2026年AI技术突破事件"
)
```

## 完整工具列表

| 工具名 | 功能 | 关键参数 |
|--------|------|----------|
| `news_storage_save` | 保存单条新闻 | title, url, event_name, content, html_content, images |
| `news_storage_save_batch` | 批量保存新闻 | news_list (JSON数组) |
| `news_storage_get_by_url` | 根据URL查询 | url |
| `news_storage_search` | 搜索新闻 | keyword (模糊), event_name (精确), source, tags |
| `news_storage_get_recent` | 获取最近新闻 | limit, offset |
| `news_storage_update_event_name` | 更新事件名称 | url, event_name |
| `news_storage_batch_update_event_name` | 批量更新事件名称 | urls (JSON数组), event_name |
| `news_storage_update_content` | 更新新闻内容 | url, content, html_content |
| `news_storage_delete` | 删除新闻 | url |
| `news_storage_stats` | 获取统计信息 | - |

## 数据结构

### 新闻对象字段
```json
{
  "title": "新闻标题",
  "url": "新闻URL（唯一标识）",
  "summary": "摘要",
  "source": "来源",
  "publish_time": "发布时间",
  "author": "作者",
  "event_name": "事件名称",  // ✨ 新增
  "content": "纯文本内容",
  "html_content": "HTML原文",  // ✨ 明确
  "keywords": ["关键词1", "关键词2"],
  "images": ["图片1", "图片2"],  // ✨ 支持多个
  "tags": ["标签1", "标签2"],
  "created_at": "创建时间",
  "updated_at": "更新时间"
}
```

## 使用场景

### 场景1: 收集新闻
```python
# 保存新闻（初始时可能没有事件名称）
news_storage_save(
    title="AI技术取得重大突破",
    url="https://example.com/news/123",
    summary="人工智能领域迎来重大技术突破",
    source="科技日报",
    content="完整的新闻内容...",
    images='["img1.jpg", "img2.jpg"]'
)
```

### 场景2: 事件聚合后归类
```python
# 聚合后将相关新闻归类到同一事件
urls = '["url1", "url2", "url3"]'
news_storage_batch_update_event_name(
    urls=urls,
    event_name="2026年AI技术突破事件"
)
```

### 场景3: 模糊查询
```python
# 通过关键词模糊搜索标题或事件名称
news_storage_search(keyword="AI技术")

# 通过事件名称精确查询
news_storage_search(event_name="2026年AI技术突破事件")

# 组合搜索
news_storage_search(
    keyword="突破",
    source="科技日报",
    event_name="2026年AI技术突破事件"
)
```

### 场景4: 获取完整原文
```python
# 获取新闻详情（包含HTML原文）
result = news_storage_get_by_url("https://example.com/news/123")
# 返回包含 html_content 字段的完整数据
```

## 数据库位置

默认数据库路径：`./data/news_storage.db`

可通过代码修改：
```python
from mcp_server.news_storage.core.database import get_database

db = get_database("./custom/path/news.db")
```

## 注意事项

1. **自动去重**：基于URL唯一标识，重复URL会自动更新而非报错
2. **模糊查询**：`keyword` 参数匹配标题、事件名称、摘要、内容
3. **精确查询**：`event_name` 参数需要完全匹配
4. **批量操作**：推荐使用批量工具提高效率
5. **图片支持**：`images` 字段支持多个图片URL的JSON数组
