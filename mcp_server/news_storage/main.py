"""
News Storage MCP Server - 新闻存储管理器

提供新闻数据的持久化存储和检索功能
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP
from loguru import logger

from .tools.storage_tools import (
    batch_update_event_name_tool,
    delete_news_tool,
    get_news_by_url_tool,
    get_news_stats_tool,
    get_recent_news_tool,
    save_news_batch_tool,
    save_news_tool,
    search_news_tool,
    update_event_name_tool,
    update_news_content_tool,
)
from .tools.navigation_tools import (
    list_categories_tool,
    list_events_by_category_tool,
    list_news_by_event_tool,
    get_images_by_event_tool,
)

# 初始化服务器
server = FastMCP("news_storage")

logger.info("🚀 News Storage MCP Server 启动")
logger.info("   数据库: ./data/news_storage.db")


# ========== 注册工具函数 ==========


# ========== 分层导航工具 ==========


@server.tool(name="news_storage_list_categories")
async def list_categories(session_id: str) -> str:
    """列出本次会话中的所有新闻类别 - 第一步：了解数据维度

    【何时使用】
    - 开始探索数据库时首先调用
    - 了解本次会话中有哪些类别（科技/体育/财经/...）

    【使用流程】
    1. 调用此工具获取类别列表
    2. 选择感兴趣的类别
    3. 调用 news_storage_list_events_by_category 查看该类别的事件

    Args:
        session_id: 会话ID（必须传入）

    Returns:
        JSON格式：{"success": true, "categories": [{"name": "科技", "count": 85, "events": 12}]}
    """
    return await list_categories_tool(session_id=session_id)


@server.tool(name="news_storage_list_events_by_category")
async def list_events_by_category(
    session_id: str, category: str, limit: int = 20
) -> str:
    """列出某个类别下的所有事件 - 第二步：按类别浏览事件

    【何时使用】
    - 已调用 news_storage_list_categories 了解有哪些类别
    - 想查看某个类别下有哪些事件

    【使用流程】
    1. 从 list_categories 的返回值中选择一个 category
    2. 调用此工具获取该类别下的事件列表
    3. 选择感兴趣的事件，调用 news_storage_list_news_by_event 查看新闻

    Args:
        session_id: 会话ID（必须传入）
        category: 类别名称（从 list_categories 获取）
        limit: 最大返回数量（默认20）

    Returns:
        JSON格式：{"success": true, "category": "科技", "events": [...]}
    """
    return await list_events_by_category_tool(
        session_id=session_id, category=category, limit=limit
    )


@server.tool(name="news_storage_list_news_by_event")
async def list_news_by_event(session_id: str, event_name: str, limit: int = 50) -> str:
    """列出某个事件下的新闻（轻量级）- 第三步：查看新闻列表

    【何时使用】
    - 已调用 news_storage_list_events_by_category 了解有哪些事件
    - 想查看某个事件下的具体新闻

    【使用流程】
    1. 从 list_events_by_category 的返回值中选择一个 event_name
    2. 调用此工具获取该事件下的新闻列表（轻量级，包含图片URL）
    3. 根据标题和摘要，选择感兴趣的新闻
    4. 调用 news_storage_get_by_url 获取完整内容（包括 content）

    Args:
        session_id: 会话ID（必须传入）
        event_name: 事件名称（从 list_events_by_category 获取）
        limit: 最大返回数量（默认50）

    Returns:
        JSON格式：{"success": true, "event_name": "...", "news": [...]}
    """
    return await list_news_by_event_tool(
        session_id=session_id, event_name=event_name, limit=limit
    )


@server.tool(name="news_storage_get_images_by_event")
async def get_images_by_event(session_id: str, event_name: str) -> str:
    """获取事件下所有新闻的图片URL - 用于报告生成

    【何时使用】
    - 生成报告时需要获取某个事件的所有图片
    - 需要下载事件相关的图片素材

    【使用流程】
    1. 调用此工具获取事件的所有图片URL
    2. 使用 downloader 工具批量下载图片
    3. 在报告中引用本地图片路径

    Args:
        session_id: 会话ID（必须传入）
        event_name: 事件名称（从 list_events_by_category 获取）

    Returns:
        JSON格式：{
            "success": true,
            "event_name": "AI技术突破",
            "count": 25,
            "images": [
                {
                    "url": "https://example.com/img1.jpg",
                    "source_news_title": "AI芯片技术重大突破",
                    "source_news_url": "https://example.com/news/1"
                },
                ...
            ]
        }
    """
    return await get_images_by_event_tool(session_id=session_id, event_name=event_name)


# ========== 原有工具 ==========


@server.tool(name="news_storage_save")
async def save_news(
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
    """保存单条新闻（URL唯一，已存在则更新）

    Args:
        title: 标题（必填）
        url: URL（必填，唯一标识）
        session_id: 会话ID（必填）
        category: 类别（必填，如：科技/体育/财经/...）
        summary: 摘要
        source: 来源
        publish_time: 发布时间
        author: 作者
        event_name: 事件名称
        content: 纯文本内容
        html_content: HTML内容
        keywords: 关键词JSON数组
        image_urls: 网络图片URL JSON数组（远程图片URL）
        local_image_paths: 本地图片路径 JSON数组（下载后的本地路径）
        tags: 标签JSON数组

    Returns:
        JSON格式：{success, action, message, url}

    Examples:
        >>> # 保存带本地路径的新闻
        >>> save_news(
        ...     title="AI技术突破",
        ...     url="https://example.com/news/123",
        ...     session_id="20260130-abc123",
        ...     category="科技",
        ...     event_name="AI技术突破事件"
        ... )
    """
    return await save_news_tool(
        title=title,
        url=url,
        summary=summary,
        source=source,
        publish_time=publish_time,
        author=author,
        event_name=event_name,
        content=content,
        html_content=html_content,
        keywords=keywords,
        image_urls=image_urls,
        local_image_paths=local_image_paths,
        tags=tags,
        session_id=session_id,
        category=category,
    )


@server.tool(name="news_storage_save_batch")
async def save_news_batch(news_list: str) -> str:
    """批量保存新闻

    Args:
        news_list: 新闻列表JSON字符串

    Returns:
        JSON格式：{success, added, updated, failed, total}
    """
    return await save_news_batch_tool(news_list=news_list)


@server.tool(name="news_storage_get_by_url")
async def get_news_by_url(
    url: str, session_id: str = "", category: str = ""
) -> str:
    """根据URL获取新闻

    Args:
        url: 新闻URL
        session_id: 会话ID（可选，用于精确查询）
        category: 类别（可选，用于精确查询）

    Returns:
        JSON格式的新闻数据，不存在返回null
    """
    return await get_news_by_url_tool(
        url=url, session_id=session_id, category=category
    )


@server.tool(name="news_storage_search")
async def search_news(
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
    """搜索新闻（支持多词空格分隔，自动分词搜索所有字段）

    Args:
        session_id: 会话ID（必填）
        search: 搜索词（多词空格分隔）
        source: 来源筛选
        event_name: 事件名称筛选
        category: 类别筛选
        start_date: 开始日期
        end_date: 结束日期
        tags: 标签JSON数组
        limit: 返回数量
        offset: 偏移量

    Returns:
        JSON格式：{success, count, results, filters}
    """
    return await search_news_tool(
        session_id=session_id,
        search=search,
        source=source,
        event_name=event_name,
        category=category,
        start_date=start_date,
        end_date=end_date,
        tags=tags,
        limit=limit,
        offset=offset,
    )


@server.tool(name="news_storage_get_recent")
async def get_recent_news(
    session_id: str, limit: int = 100, offset: int = 0
) -> str:
    """获取最近添加的新闻（按添加时间倒序）

    Args:
        session_id: 会话ID（必填）
        limit: 返回数量
        offset: 偏移量

    Returns:
        JSON格式的新闻列表
    """
    return await get_recent_news_tool(
        session_id=session_id, limit=limit, offset=offset
    )


@server.tool(name="news_storage_update_content")
async def update_news_content(url: str, content: str, html_content: str = "") -> str:
    """更新新闻内容

    Args:
        url: 新闻URL
        content: 纯文本内容
        html_content: HTML内容

    Returns:
        JSON格式的操作结果
    """
    return await update_news_content_tool(
        url=url, content=content, html_content=html_content
    )


@server.tool(name="news_storage_delete")
async def delete_news(url: str) -> str:
    """删除新闻

    Args:
        url: 新闻URL

    Returns:
        JSON格式的操作结果
    """
    return await delete_news_tool(url=url)


@server.tool(name="news_storage_stats")
async def get_news_stats(session_id: str) -> str:
    """获取统计信息

    Args:
        session_id: 会话ID（必填）

    Returns:
        JSON格式的统计数据
    """
    return await get_news_stats_tool(session_id=session_id)


@server.tool(name="news_storage_update_event_name")
async def update_event_name(url: str, event_name: str) -> str:
    """更新新闻的事件名称

    Args:
        url: 新闻URL
        event_name: 事件名称

    Returns:
        JSON格式的操作结果
    """
    return await update_event_name_tool(url=url, event_name=event_name)


@server.tool(name="news_storage_batch_update_event_name")
async def batch_update_event_name(urls: str, event_name: str) -> str:
    """批量更新新闻的事件名称

    Args:
        urls: URL列表JSON字符串
        event_name: 事件名称

    Returns:
        JSON格式：{success, updated, failed, event_name}
    """
    return await batch_update_event_name_tool(urls=urls, event_name=event_name)


if __name__ == "__main__":
    server.run()
