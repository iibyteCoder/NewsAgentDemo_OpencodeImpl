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
    session_id: str,
    category: str,
    summary: str = "",
    source: str = "",
    publish_time: str = "",
    author: str = "",
    event_name: str = "",
    content: str = "",
    html_content: str = "",
    keywords: str = "[]",
    image_urls: str = "[]",
    local_image_paths: str = "[]",
    tags: str = "[]",
) -> str:
    """保存单条新闻 - 💾 自动去重（基于URL）

    功能：
    - 保存新闻的完整信息到SQLite数据库
    - 自动检测URL是否已存在，存在则更新
    - 支持保存标题、摘要、来源、时间、内容等完整信息
    - 支持关键词、网络图片URL、本地图片文件路径、标签等扩展信息
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
        image_urls: 网络图片URL JSON数组（可选，支持多个，如 '["https://example.com/img1.jpg", "https://example.com/img2.jpg"]'）
        local_image_paths: 本地图片文件路径JSON数组（可选，支持多个，如 '["./data/images/img1.jpg", "./data/images/img2.jpg"]'）
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
        ...     image_urls='["https://example.com/img1.jpg", "https://example.com/img2.jpg"]',
        ...     local_image_paths='["./report/images/img1.jpg", "./report/images/img2.jpg"]',
        ...     tags='["科技", "前沿"]'
        ... )
    """
    try:
        db = await get_database()

        # 解析JSON字段
        keywords_list = json.loads(keywords) if keywords else []
        image_urls_list = json.loads(image_urls) if image_urls else []
        local_image_paths_list = (
            json.loads(local_image_paths) if local_image_paths else []
        )
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
            image_urls=image_urls_list,
            local_image_paths=local_image_paths_list,
            tags=tags_list,
        )

        # 保存（传入 session_id 和 category）
        is_new = await db.save_news(news, session_id=session_id, category=category)

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
        db = await get_database()

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
                image_urls=item.get("image_urls", []),
                local_image_paths=item.get("local_image_paths", []),
                tags=item.get("tags", []),
            )
            news_items.append(news)

        # 批量保存
        stats = await db.save_news_batch(news_items)

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


async def get_news_by_url_tool(
    url: str, session_id: str = "", category: str = ""
) -> str:
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
        db = await get_database()
        news = await db.get_news_by_url(url, session_id=session_id, category=category)

        if news:
            # 返回用户友好的格式（列表字段保持为列表，不是JSON字符串）
            result = {
                "success": True,
                "found": True,
                "data": {
                    "title": news.title,
                    "url": news.url,
                    "summary": news.summary,
                    "source": news.source,
                    "publish_time": news.publish_time,
                    "author": news.author,
                    "event_name": news.event_name,
                    "session_id": news.session_id,
                    "category": news.category,
                    "content": news.content,
                    "html_content": news.html_content,
                    "keywords": news.keywords,
                    "image_urls": news.image_urls,
                    "local_image_paths": news.local_image_paths,
                    "tags": news.tags,
                    "created_at": news.created_at,
                    "updated_at": news.updated_at,
                },
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
    session_id: str,
    search: Optional[str] = None,
    source: Optional[str] = None,
    event_name: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> str:
    """搜索新闻 - 🔎 智能搜索，一个参数搞定所有

    【核心特性】
    - 自动分词：多个空格分隔的词会被分别搜索
    - 全字段匹配：搜索标题、摘要、keywords字段、内容
    - 宽松匹配：只要匹配任意一个词就返回该新闻（OR关系）
    - 结果最大化：尽可能多返回相关内容

    Args:
        search: 搜索词（可选，支持多个词用空格分隔）
            - 单个词："欧冠"
            - 多个词："皇马 巴黎圣日耳曼 淘汰赛"
            - 系统会自动分词，每个词独立搜索所有字段
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
        >>> # 【最简单】单个词搜索
        >>> search_news_tool(search="欧冠")

        >>> # 【常用】多个词搜索（自动分词，OR关系）
        >>> search_news_tool(search="皇马 巴黎圣日耳曼 淘汰赛 恢复能力")

        >>> # 【精准】按来源筛选
        >>> search_news_tool(search="AI", source="科技日报")

        >>> # 【专业】组合筛选
        >>> search_news_tool(
        ...     search="AI 技术 突破",
        ...     source="科技日报",
        ...     event_name="2026年AI技术突破事件",
        ...     start_date="2026-01-01"
        ... )

        >>> # 【高级】按标签筛选
        >>> search_news_tool(
        ...     search="欧冠",
        ...     tags='["体育", "足球"]'
        ... )
    """
    try:
        db = await get_database()

        # 自动分词：按空格分割搜索词
        search_terms = None
        if search:
            # 去除首尾空格，按空格分割，过滤空字符串
            search_terms = [term.strip() for term in search.split() if term.strip()]

        # 解析标签
        tags_list = json.loads(tags) if tags else None

        # 构建过滤器
        search_filter = SearchFilter(
            session_id=session_id,
            category=category or "",
            search_terms=search_terms,
            source=source,
            event_name=event_name,
            start_date=start_date,
            end_date=end_date,
            tags=tags_list,
            limit=limit,
            offset=offset,
        )

        # 搜索
        results = await db.search_news(search_filter)

        # 转换为轻量级数据（不包含 content 和 html_content）
        lightweight_results = []
        for news in results:
            lightweight_results.append(
                {
                    "title": news.title,
                    "url": news.url,
                    "summary": news.summary,
                    "source": news.source,
                    "publish_time": news.publish_time,
                    "author": news.author,
                    "event_name": news.event_name,
                    "keywords": news.keywords,
                    "image_urls": news.image_urls,
                    "local_image_paths": news.local_image_paths,
                    "tags": news.tags,
                    "created_at": news.created_at,
                }
            )

        result = {
            "success": True,
            "count": len(lightweight_results),
            "results": lightweight_results,
            "filters": {
                "search": search,
                "search_terms": search_terms,
                "source": source,
                "event_name": event_name,
                "category": category,
                "start_date": start_date,
                "end_date": end_date,
                "tags": tags_list,
            },
            "note": "结果不包含 content 和 html_content，需要时请使用 news_storage_get_by_url 获取完整内容",
        }

        logger.info(f"✅ 搜索完成: 找到 {len(lightweight_results)} 条结果")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 搜索失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def get_recent_news_tool(
    session_id: str, limit: int = 100, offset: int = 0
) -> str:
    """获取最近添加的新闻（轻量级，不包含 content）- 📰 最新资讯

    功能：
    - 获取最近添加的新闻列表
    - 按添加时间倒序排列
    - 支持分页
    - 返回轻量级数据（不含 content 和 html_content）

    Args:
        session_id: 会话ID（必填）
        limit: 返回数量（默认100）
        offset: 偏移量（默认0，用于分页）

    Returns:
        JSON格式的新闻列表（轻量级）

    Examples:
        >>> # 获取最近100条新闻
        >>> get_recent_news_tool(session_id="xxx", limit=100)
        >>> # 分页获取
        >>> get_recent_news_tool(session_id="xxx", limit=20, offset=20)  # 第2页
    """
    try:
        db = await get_database()
        results = await db.get_recent_news(limit, offset, session_id=session_id)

        # 转换为轻量级数据（不包含 content 和 html_content）
        lightweight_results = []
        for news in results:
            lightweight_results.append(
                {
                    "title": news.title,
                    "url": news.url,
                    "summary": news.summary,
                    "source": news.source,
                    "publish_time": news.publish_time,
                    "author": news.author,
                    "event_name": news.event_name,
                    "keywords": news.keywords,
                    "image_urls": news.image_urls,
                    "local_image_paths": news.local_image_paths,
                    "tags": news.tags,
                    "created_at": news.created_at,
                }
            )

        result = {
            "success": True,
            "count": len(lightweight_results),
            "results": lightweight_results,
            "note": "结果不包含 content 和 html_content，需要时请使用 news_storage_get_by_url 获取完整内容",
        }

        logger.info(f"✅ 获取最近新闻: {len(lightweight_results)} 条")
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
        db = await get_database()
        success = await db.update_news_content(url, content, html_content)

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
        db = await get_database()
        success = await db.delete_news(url)

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


async def get_news_stats_tool(session_id: str = "") -> str:
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
        db = await get_database()
        stats = await db.get_stats(session_id=session_id)

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
        db = await get_database()
        success = await db.update_event_name(url, event_name)

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
        db = await get_database()
        url_list = json.loads(urls) if urls else []

        if not url_list:
            return json.dumps(
                {"success": False, "error": "URL列表为空"},
                ensure_ascii=False,
                indent=2,
            )

        stats = await db.batch_update_event_name(url_list, event_name)

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
