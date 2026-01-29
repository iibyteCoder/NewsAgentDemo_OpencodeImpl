# 图片保存问题诊断报告

## 问题描述

数据库中的新闻记录，`images` 字段全部为空数组 `[]`，但实际上：
- ✅ 网页中存在图片
- ✅ `web-browser_fetch_article_content_tool` 能成功提取图片链接
- ✅ `news-storage_save_news_tool` 能正确保存图片到数据库

## 根本原因

**智能体在调用 `save_news_tool` 时，没有传递 `images` 参数。**

### 完整的保存流程应该是：

```python
# 1. 使用 fetch_article_content_tool 提取内容（包含图片）
result = web-browser_fetch_article_content_tool(
    url="https://...",
    include_images=True
)

# 解析返回的 JSON
data = json.loads(result)
images_list = data.get("images", [])  # 提取图片列表
image_urls = [img["url"] for img in images_list]

# 2. 保存到数据库时，必须传递 images 参数
news-storage_save_news_tool(
    title=data["title"],
    url=data["url"],
    content=data["content"],
    images=json.dumps(image_urls),  # ⭐ 关键：传递图片URL列表
    # ... 其他参数
)
```

### 实际智能体的错误调用：

```python
# ❌ 错误示例（当前智能体可能这样调用）
news-storage_save_news_tool(
    title=data["title"],
    url=data["url"],
    content=data["content"],
    # images 参数被遗漏了！
)
```

## 测试验证

运行测试脚本：
```bash
python scripts/debug/check_images_issue.py
```

测试结果证明：
- ✅ 图片提取成功：提取到 11 个图片链接
- ✅ 数据库保存成功：传递 `images` 参数后正确保存

## 解决方案

### 方案1：修改智能体提示词（推荐）

在 `prompts/news-collector.txt` 中，明确强调传递 `images` 参数：

```markdown
### 保存新闻的完整示例

```python
# 1. 提取文章内容（包含图片）
fetch_result = web-browser_fetch_article_content_tool(
    url="https://example.com/news/123",
    include_images=True
)

fetch_data = json.loads(fetch_result)

# 2. 保存到数据库（⭐ 必须传递 images 参数）
news-storage_save_news_tool(
    title=fetch_data["title"],
    url=fetch_data["url"],
    summary=fetch_data.get("summary", ""),
    source=fetch_data.get("source", ""),
    publish_time=fetch_data.get("publish_time", ""),
    content=fetch_data.get("content", ""),
    html_content=fetch_data.get("html_content", ""),
    images=json.dumps([img["url"] for img in fetch_data.get("images", [])]),  # ⭐
    local_images="[]",
    tags="[]"
)
```
```

### 方案2：修改 save_news_tool 默认行为（不推荐）

修改 `mcp_server/news_storage/tools/storage_tools.py`，但这会破坏 API 设计。

## 数据修复脚本

对于已保存的新闻，可以重新抓取并更新图片字段：

```python
# scripts/tools/update_news_images.py
import asyncio
import json
from mcp_server.web_browser.tools.search_tools import fetch_article_content
from mcp_server.news_storage.tools.storage_tools import (
    get_recent_news_tool,
    update_news_content_tool
)

async def update_images():
    # 获取最近100条新闻
    result = await get_recent_news_tool(limit=100)
    data = json.loads(result)

    for news in data["results"]:
        url = news["url"]

        # 重新抓取图片
        fetch_result = await fetch_article_content(url, include_images=True)
        fetch_data = json.loads(fetch_result)

        if fetch_data.get("images"):
            # 更新数据库（需要添加 update_images_tool）
            await update_news_images_tool(
                url=url,
                images=json.dumps([img["url"] for img in fetch_data["images"]])
            )
            print(f"✅ 更新图片: {news['title'][:50]}")

if __name__ == "__main__":
    asyncio.run(update_images())
```

## 工具参数说明

### web-browser_fetch_article_content_tool

```python
async def fetch_article_content(
    url: str,
    include_images: bool = True
) -> str:
    """返回 JSON 格式：

    {
        "url": "...",
        "title": "...",
        "content": "...",
        "images": [  # ⭐ 注意这个字段
            {
                "index": 1,
                "url": "https://...",
                "alt": "...",
                "width": 0,
                "height": 0
            },
            ...
        ],
        "image_count": 11,  # 图片数量
        ...
    }
    """
```

### news-storage_save_news_tool

```python
async def save_news_tool(
    title: str,
    url: str,
    summary: str = "",
    source: str = "",
    publish_time: str = "",
    author: str = "",
    event_name: str = "",
    content: str = "",
    html_content: str = "",
    keywords: str = "[]",
    images: str = "[]",  # ⭐ 默认为空数组
    local_images: str = "[]",
    tags: str = "[]"
) -> str:
    """
    images 参数说明：
    - 类型：JSON 字符串格式的数组
    - 示例：'["url1", "url2"]' 或 '[]'
    - 默认值："[]"（空数组）
    """
```

## 总结

1. **问题确认**：智能体没有传递 `images` 参数给 `save_news_tool`
2. **代码无误**：`fetch_article_content` 和 `save_news_tool` 本身工作正常
3. **解决方案**：修改智能体提示词，明确要求传递 `images` 参数
4. **数据修复**：需要编写脚本重新抓取已保存新闻的图片信息

## 验证步骤

1. 修改智能体提示词
2. 重新运行新闻收集任务
3. 检查数据库：
   ```bash
   python -c "
   import sqlite3, json
   conn = sqlite3.connect('data/news_storage.db')
   cursor = conn.cursor()
   cursor.execute('SELECT url, title, images FROM news LIMIT 5')
   for row in cursor.fetchall():
       images = json.loads(row[2]) if row[2] else []
       has_images = len(images) > 0
       print(f'{\"✅\" if has_images else \"❌\"} {row[1][:50]}... ({len(images)} images)')
   "
   ```
