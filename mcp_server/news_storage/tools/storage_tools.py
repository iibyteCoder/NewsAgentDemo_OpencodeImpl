"""
新闻存储工具函数
"""

import json
from typing import Optional
from loguru import logger

from ..core.database import get_database
from ..core.models import NewsItem, SearchFilter


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
    images: str = "[]",
    tags: str = "[]",
) -> str:
    """保存单条新闻 - 💾 自动去重（基于URL）

    功能：
    - 保存新闻的完整信息到SQLite数据库
    - 自动检测URL是否已存在，存在则更新
    - 支持保存标题、摘要、来源、时间、内容等完整信息
    - 支持关键词、图片URL（多个）、标签等扩展信息
    - 支持事件名称归类

    Args:
        title: 新闻标题（必填）
        url: 新闻URL（必填，用作唯一标识）
        summary: 新闻摘要（可选）
        source: 新闻来源（可选，如"新华网"）
        publish_time: 发布时间（可选，原始字符串）
        author: 作者（可选）
        event_name: 事件名称（可选，用于归类同一事件的新闻）
        content: 完整内容-纯文本（可选）
        html_content: HTML内容（原文）（可选）
        keywords: 关键词JSON数组（可选，如 '["AI", "技术"]'）
        images: 图片URL JSON数组（可选，支持多个图片）
        tags: 标签 JSON数组（可选）

    Returns:
        JSON格式的操作结果，包含：
        - success: 是否成功
        - action: "inserted" 或 "updated"
        - message: 结果消息
        - url: 新闻URL

    Examples:
        >>> # 保存基本新闻信息
        >>> save_news_tool(
        ...     title="AI技术突破",
        ...     url="https://example.com/news/123",
        ...     summary="人工智能取得重大突破",
        ...     source="科技日报"
        ... )
        >>> # 保存完整新闻（包括内容、图片、事件名称）
        >>> save_news_tool(
        ...     title="AI技术突破",
        ...     url="https://example.com/news/123",
        ...     summary="人工智能取得重大突破",
        ...     source="科技日报",
        ...     event_name="2026年AI技术突破事件",
        ...     content="完整的新闻内容...",
        ...     html_content="<p>HTML原文</p>",
        ...     keywords='["AI", "技术"]',
        ...     images='["https://example.com/img1.jpg", "https://example.com/img2.jpg"]',
        ...     tags='["科技", "前沿"]'
        ... )
    """
    try:
        db = get_database()

        # 解析JSON字段
        keywords_list = json.loads(keywords) if keywords else []
        images_list = json.loads(images) if images else []
        tags_list = json.loads(tags) if tags else []

        # 创建新闻对象
        news = NewsItem(
            title=title,
            url=url,
            summary=summary,
            source=source,
            publish_time=publish_time,
            author=author,
            event_name=event_name,
            content=content,
            html_content=html_content,
            keywords=keywords_list,
            images=images_list,
            tags=tags_list,
        )

        # 保存
        is_new = db.save_news(news)

        action = "inserted" if is_new else "updated"
        message = f"新闻已{action}" if is_new else "新闻已更新"

        result = {
            "success": True,
            "action": action,
            "message": message,
            "url": url,
        }

        logger.info(f"✅ {message}: {title[:50]}")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 保存新闻失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def save_news_batch_tool(news_list: str) -> str:
    """批量保存新闻 - 📦 高效批量导入

    功能：
    - 一次性保存多条新闻
    - 自动去重，已存在的URL会更新而非报错
    - 返回详细的统计信息

    Args:
        news_list: 新闻列表JSON字符串，格式为：
            [
                {
                    "title": "标题",
                    "url": "https://...",
                    "summary": "摘要",
                    "source": "来源",
                    ...
                },
                ...
            ]

    Returns:
        JSON格式的批量操作结果，包含：
        - success: 是否成功
        - added: 新增数量
        - updated: 更新数量
        - failed: 失败数量
        - total: 总数

    Examples:
        >>> news_data = '''[
        ...     {"title": "新闻1", "url": "https://example.com/1", "source": "新华网"},
        ...     {"title": "新闻2", "url": "https://example.com/2", "source": "人民网"}
        ... ]'''
        >>> save_news_batch_tool(news_data)
    """
    try:
        db = get_database()

        # 解析新闻列表
        news_data = json.loads(news_list)
        news_items = []

        for item in news_data:
            news = NewsItem(
                title=item.get("title", ""),
                url=item.get("url", ""),
                summary=item.get("summary", ""),
                source=item.get("source", ""),
                publish_time=item.get("publish_time", ""),
                author=item.get("author", ""),
                content=item.get("content", ""),
                html_content=item.get("html_content", ""),
                keywords=item.get("keywords", []),
                images=item.get("images", []),
                tags=item.get("tags", []),
            )
            news_items.append(news)

        # 批量保存
        stats = db.save_news_batch(news_items)

        result = {
            "success": True,
            "added": stats["added"],
            "updated": stats["updated"],
            "failed": stats["failed"],
            "total": stats["added"] + stats["updated"] + stats["failed"],
        }

        logger.info(f"✅ 批量保存完成: {result}")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 批量保存失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def get_news_by_url_tool(url: str) -> str:
    """根据URL获取新闻 - 🔍 精确查询

    功能：
    - 根据新闻URL精确查询
    - 返回完整的新闻信息

    Args:
        url: 新闻URL

    Returns:
        JSON格式的新闻数据，不存在则返回null

    Examples:
        >>> get_news_by_url_tool("https://example.com/news/123")
    """
    try:
        db = get_database()
        news = db.get_news_by_url(url)

        if news:
            result = {
                "success": True,
                "found": True,
                "data": news.to_dict(),
            }
            logger.info(f"✅ 找到新闻: {news.title[:50]}")
        else:
            result = {
                "success": True,
                "found": False,
                "data": None,
            }
            logger.info(f"⚠️ 未找到新闻: {url[:50]}")

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 查询失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def search_news_tool(
    keyword: Optional[str] = None,
    source: Optional[str] = None,
    event_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> str:
    """搜索新闻 - 🔎 支持多条件筛选

    功能：
    - 根据关键词模糊搜索（标题、事件名称、摘要、内容）
    - 按来源筛选
    - 按事件名称精确筛选（查找同一事件的所有新闻）
    - 按日期范围筛选
    - 按标签筛选（支持多标签）
    - 支持分页

    Args:
        keyword: 搜索关键词（可选，模糊匹配标题、事件名称、摘要、内容）
        source: 来源筛选（可选，如"新华网"）
        event_name: 事件名称精确筛选（可选）
        start_date: 开始日期（可选，ISO格式）
        end_date: 结束日期（可选，ISO格式）
        tags: 标签JSON数组（可选，如 '["科技", "AI"]'）
        limit: 返回数量（默认100）
        offset: 偏移量（默认0，用于分页）

    Returns:
        JSON格式的搜索结果，包含：
        - success: 是否成功
        - count: 结果数量
        - results: 新闻列表
        - filters: 使用的筛选条件

    Examples:
        >>> # 关键词搜索（模糊匹配标题和事件名称）
        >>> search_news_tool(keyword="AI", limit=10)
        >>> # 按来源搜索
        >>> search_news_tool(source="新华网", limit=20)
        >>> # 按事件名称精确搜索
        >>> search_news_tool(event_name="2026年AI技术突破事件")
        >>> # 组合搜索
        >>> search_news_tool(
        ...     keyword="技术",
        ...     source="科技日报",
        ...     event_name="2026年AI技术突破事件",
        ...     tags='["科技", "前沿"]',
        ...     limit=50
        ... )
    """
    try:
        db = get_database()

        # 解析标签
        tags_list = json.loads(tags) if tags else None

        # 构建过滤器
        search_filter = SearchFilter(
            keyword=keyword,
            source=source,
            event_name=event_name,
            start_date=start_date,
            end_date=end_date,
            tags=tags_list,
            limit=limit,
            offset=offset,
        )

        # 搜索
        results = db.search_news(search_filter)

        result = {
            "success": True,
            "count": len(results),
            "results": [news.to_dict() for news in results],
            "filters": {
                "keyword": keyword,
                "source": source,
                "event_name": event_name,
                "start_date": start_date,
                "end_date": end_date,
                "tags": tags_list,
            },
        }

        logger.info(f"✅ 搜索完成: 找到 {len(results)} 条结果")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 搜索失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def get_recent_news_tool(limit: int = 100, offset: int = 0) -> str:
    """获取最近添加的新闻 - 📰 最新资讯

    功能：
    - 获取最近添加的新闻列表
    - 按添加时间倒序排列
    - 支持分页

    Args:
        limit: 返回数量（默认100）
        offset: 偏移量（默认0，用于分页）

    Returns:
        JSON格式的新闻列表

    Examples:
        >>> # 获取最近100条新闻
        >>> get_recent_news_tool(limit=100)
        >>> # 分页获取
        >>> get_recent_news_tool(limit=20, offset=20)  # 第2页
    """
    try:
        db = get_database()
        results = db.get_recent_news(limit, offset)

        result = {
            "success": True,
            "count": len(results),
            "results": [news.to_dict() for news in results],
        }

        logger.info(f"✅ 获取最近新闻: {len(results)} 条")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def update_news_content_tool(
    url: str, content: str, html_content: str = ""
) -> str:
    """更新新闻内容 - ✏️ 补充完整内容

    功能：
    - 更新已存在新闻的内容
    - 用于后续补充完整正文内容

    Args:
        url: 新闻URL
        content: 纯文本内容
        html_content: HTML内容（可选）

    Returns:
        JSON格式的操作结果

    Examples:
        >>> update_news_content_tool(
        ...     url="https://example.com/news/123",
        ...     content="这是完整的新闻正文内容...",
        ...     html_content="<p>这是HTML内容</p>"
        ... )
    """
    try:
        db = get_database()
        success = db.update_news_content(url, content, html_content)

        result = {
            "success": success,
            "message": "内容已更新" if success else "未找到该新闻",
        }

        if success:
            logger.info(f"✅ 更新内容成功: {url[:50]}")
        else:
            logger.warning(f"⚠️ 更新失败: {url[:50]}")

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 更新失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def delete_news_tool(url: str) -> str:
    """删除新闻 - 🗑️ 从数据库删除

    功能：
    - 根据URL删除新闻
    - 不可恢复

    Args:
        url: 新闻URL

    Returns:
        JSON格式的操作结果

    Examples:
        >>> delete_news_tool("https://example.com/news/123")
    """
    try:
        db = get_database()
        success = db.delete_news(url)

        result = {
            "success": success,
            "message": "删除成功" if success else "未找到该新闻",
        }

        if success:
            logger.info(f"✅ 删除成功: {url[:50]}")
        else:
            logger.warning(f"⚠️ 删除失败: {url[:50]}")

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 删除失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def get_news_stats_tool() -> str:
    """获取统计信息 - 📊 数据概览

    功能：
    - 获取数据库中的新闻统计信息
    - 总数、来源分布、近期新增等

    Returns:
        JSON格式的统计数据

    Examples:
        >>> get_news_stats_tool()
    """
    try:
        db = get_database()
        stats = db.get_stats()

        result = {
            "success": True,
            "stats": stats,
        }

        logger.info(f"✅ 统计信息: 总数 {stats['total']}")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取统计失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def update_event_name_tool(url: str, event_name: str) -> str:
    """更新新闻的事件名称 - 🏷️ 聚合后归类

    功能：
    - 单独更新新闻的事件名称字段
    - 用于新闻聚合后添加事件分类
    - 不会影响其他字段

    Args:
        url: 新闻URL
        event_name: 事件名称

    Returns:
        JSON格式的操作结果

    Examples:
        >>> # 为新闻添加事件名称
        >>> update_event_name_tool(
        ...     url="https://example.com/news/123",
        ...     event_name="2026年AI技术突破事件"
        ... )
    """
    try:
        db = get_database()
        success = db.update_event_name(url, event_name)

        result = {
            "success": success,
            "message": "事件名称已更新" if success else "未找到该新闻",
            "url": url,
            "event_name": event_name,
        }

        if success:
            logger.info(f"✅ 更新事件名称成功: {url[:50]} -> {event_name}")
        else:
            logger.warning(f"⚠️ 更新失败: {url[:50]}")

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 更新事件名称失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def batch_update_event_name_tool(urls: str, event_name: str) -> str:
    """批量更新新闻的事件名称 - 📦 批量归类

    功能：
    - 批量为多条新闻设置相同的事件名称
    - 用于将聚合后的新闻归类到同一事件
    - 返回详细的更新统计

    Args:
        urls: URL列表JSON字符串（如 '["url1", "url2"]'）
        event_name: 事件名称

    Returns:
        JSON格式的批量操作结果，包含：
        - success: 是否成功
        - updated: 更新数量
        - failed: 失败数量
        - event_name: 事件名称

    Examples:
        >>> urls = '["https://example.com/news/1", "https://example.com/news/2"]'
        >>> batch_update_event_name_tool(
        ...     urls=urls,
        ...     event_name="2026年AI技术突破事件"
        ... )
    """
    try:
        db = get_database()
        url_list = json.loads(urls) if urls else []

        if not url_list:
            return json.dumps(
                {"success": False, "error": "URL列表为空"},
                ensure_ascii=False,
                indent=2,
            )

        stats = db.batch_update_event_name(url_list, event_name)

        result = {
            "success": True,
            "updated": stats["updated"],
            "failed": stats["failed"],
            "total": len(url_list),
            "event_name": event_name,
        }

        logger.info(f"✅ 批量更新事件名称完成: {stats}")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 批量更新事件名称失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )

