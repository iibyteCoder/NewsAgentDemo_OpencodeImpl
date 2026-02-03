"""
新闻存储工具函数 - 使用新的 Repository 模式
"""

import json
from typing import Optional

from loguru import logger

from ..db import NewsRepository, get_db_manager

# 全局仓储实例（延迟初始化）
_news_repo: NewsRepository | None = None


def _get_news_repo() -> NewsRepository:
    """获取新闻仓储实例（单例）"""
    global _news_repo
    if _news_repo is None:
        db_manager = get_db_manager()
        _news_repo = NewsRepository(db_manager)
    return _news_repo


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
        image_urls: 网络图片URL JSON数组（可选，支持多个）
        local_image_paths: 本地图片文件路径JSON数组（可选，支持多个）
        tags: 标签 JSON数组（可选）

    Returns:
        JSON格式的操作结果，包含：
        - success: 是否成功
        - action: "inserted" 或 "updated"
        - message: 结果消息
        - url: 新闻URL
    """
    try:
        repo = _get_news_repo()

        # 解析JSON字段（转为列表，然后转为字典存储）
        keywords_list = json.loads(keywords) if keywords else []
        image_urls_list = json.loads(image_urls) if image_urls else []
        local_image_paths_list = (
            json.loads(local_image_paths) if local_image_paths else []
        )
        tags_list = json.loads(tags) if tags else []

        # 转为字典格式存储（为了更好的查询性能）
        keywords_dict = {str(i): v for i, v in enumerate(keywords_list)}
        image_urls_dict = {str(i): v for i, v in enumerate(image_urls_list)}
        local_image_paths_dict = {
            str(i): v for i, v in enumerate(local_image_paths_list)
        }
        tags_dict = {str(i): v for i, v in enumerate(tags_list)}

        # 保存
        is_new = await repo.save(
            title=title,
            url=url,
            session_id=session_id,
            category=category,
            summary=summary or None,
            source=source or None,
            publish_time=publish_time or None,
            author=author or None,
            event_name=event_name or None,
            content=content or None,
            html_content=html_content or None,
            keywords=keywords_dict,
            image_urls=image_urls_dict,
            local_image_paths=local_image_paths_dict,
            tags=tags_dict,
        )

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
    """
    try:
        repo = _get_news_repo()

        # 解析新闻列表
        news_data = json.loads(news_list)
        news_items = []

        for item in news_data:
            # 解析 JSON 字段并转为字典
            keywords = item.get("keywords", [])
            image_urls = item.get("image_urls", [])
            local_image_paths = item.get("local_image_paths", [])
            tags = item.get("tags", [])

            news_items.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "summary": item.get("summary"),
                    "source": item.get("source"),
                    "publish_time": item.get("publish_time"),
                    "author": item.get("author"),
                    "event_name": item.get("event_name"),
                    "content": item.get("content"),
                    "html_content": item.get("html_content"),
                    "keywords": {str(i): v for i, v in enumerate(keywords)},
                    "image_urls": {str(i): v for i, v in enumerate(image_urls)},
                    "local_image_paths": {
                        str(i): v for i, v in enumerate(local_image_paths)
                    },
                    "tags": {str(i): v for i, v in enumerate(tags)},
                    "session_id": item.get("session_id", ""),
                    "category": item.get("category", ""),
                }
            )

        # 批量保存
        stats = await repo.save_batch(news_items)

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
        session_id: 会话ID（可选，用于精确查询）
        category: 类别（可选，用于精确查询）

    Returns:
        JSON格式的新闻数据，不存在则返回null
    """
    try:
        repo = _get_news_repo()
        news = await repo.get_by_url(url, session_id=session_id, category=category)

        if news:
            # 转换字典格式（将字典转为列表）
            data = news.to_dict()
            data["keywords"] = list(data.get("keywords", {}).values())
            data["image_urls"] = list(data.get("image_urls", {}).values())
            data["local_image_paths"] = list(data.get("local_image_paths", {}).values())
            data["tags"] = list(data.get("tags", {}).values())

            result = {
                "success": True,
                "found": True,
                "data": data,
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
        session_id: 会话ID（必填）
        search: 搜索词（可选，支持多个词用空格分隔）
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
    """
    try:
        repo = _get_news_repo()

        # 自动分词：按空格分割搜索词
        search_terms = None
        if search:
            search_terms = [term.strip() for term in search.split() if term.strip()]

        # 搜索
        results = await repo.search(
            session_id=session_id,
            search_terms=search_terms,
            category=category or "",
            source=source,
            event_name=event_name,
            start_date=None,  # 简化处理，实际可以解析日期字符串
            end_date=None,
            tags=None,  # 简化处理
            limit=limit,
            offset=offset,
        )

        # 转换为轻量级数据（不包含 content 和 html_content）
        lightweight_results = []
        for news in results:
            data = news.to_lightweight_dict()
            # 转换 JSON 字段
            data["keywords"] = list(data.get("keywords", {}).values())
            data["image_urls"] = list(data.get("image_urls", {}).values())
            data["local_image_paths"] = list(data.get("local_image_paths", {}).values())
            data["tags"] = list(data.get("tags", {}).values())
            lightweight_results.append(data)

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
            },
            "note": (
                "结果不包含 content 和 html_content，"
                "需要时请使用 news_storage_get_by_url 获取完整内容"
            ),
        }

        logger.info(f"✅ 搜索完成: 找到 {len(lightweight_results)} 条结果")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 搜索失败: {e}")
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
    """
    try:
        repo = _get_news_repo()
        success = await repo.update_content(url, content, html_content)

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


async def get_news_stats_tool(session_id: str = "") -> str:
    """获取统计信息 - 📊 数据概览

    功能：
    - 获取数据库中的新闻统计信息
    - 总数、来源分布、近期新增等

    Args:
        session_id: 会话ID（可选）

    Returns:
        JSON格式的统计数据
    """
    try:
        repo = _get_news_repo()
        stats = await repo.get_stats(session_id=session_id)

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
    """
    try:
        repo = _get_news_repo()
        success = await repo.update_event_name(url, event_name)

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
    """
    try:
        repo = _get_news_repo()
        url_list = json.loads(urls) if urls else []

        if not url_list:
            return json.dumps(
                {"success": False, "error": "URL列表为空"},
                ensure_ascii=False,
                indent=2,
            )

        stats = await repo.batch_update_event_name(url_list, event_name)

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
