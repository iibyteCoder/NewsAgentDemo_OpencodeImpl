"""
News Storage MCP Server - 新闻存储管理器

提供新闻数据的持久化存储和检索功能
"""

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

# 初始化服务器
server = FastMCP("news_storage")

logger.info("🚀 News Storage MCP Server 启动")
logger.info("   数据库: ./data/news_storage.db")


# ========== 注册工具函数 ==========


@server.tool(name="news_storage_save")
async def save_news(
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
    local_images: str = "[]",
    tags: str = "[]",
) -> str:
    """保存单条新闻（URL唯一，已存在则更新）

    Args:
        title: 标题（必填）
        url: URL（必填，唯一标识）
        summary: 摘要
        source: 来源
        publish_time: 发布时间
        author: 作者
        event_name: 事件名称
        content: 纯文本内容
        html_content: HTML内容
        keywords: 关键词JSON数组
        images: 图片URL JSON数组（远程图片URL）
        local_images: 本地图片路径 JSON数组（下载后的本地路径）
        tags: 标签JSON数组

    Returns:
        JSON格式：{success, action, message, url}

    Examples:
        >>> # 保存带本地路径的新闻
        >>> save_news_tool(
        ...     title="AI技术突破",
        ...     url="https://example.com/news/123",
        ...     images='["https://example.com/img1.jpg"]',
        ...     local_images='["./report/科技/2026-01-29/资讯汇总与摘要/事件1/img1.jpg"]'
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
        images=images,
        local_images=local_images,
        tags=tags,
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
async def get_news_by_url(url: str) -> str:
    """根据URL获取新闻

    Args:
        url: 新闻URL

    Returns:
        JSON格式的新闻数据，不存在返回null
    """
    return await get_news_by_url_tool(url=url)


@server.tool(name="news_storage_search")
async def search_news(
    search: str = None,
    source: str = None,
    event_name: str = None,
    start_date: str = None,
    end_date: str = None,
    tags: str = None,
    limit: int = 100,
    offset: int = 0,
) -> str:
    """搜索新闻（支持多词空格分隔，自动分词搜索所有字段）

    Args:
        search: 搜索词（多词空格分隔）
        source: 来源筛选
        event_name: 事件名称筛选
        start_date: 开始日期
        end_date: 结束日期
        tags: 标签JSON数组
        limit: 返回数量
        offset: 偏移量

    Returns:
        JSON格式：{success, count, results, filters}
    """
    return await search_news_tool(
        search=search,
        source=source,
        event_name=event_name,
        start_date=start_date,
        end_date=end_date,
        tags=tags,
        limit=limit,
        offset=offset,
    )


@server.tool(name="news_storage_get_recent")
async def get_recent_news(limit: int = 100, offset: int = 0) -> str:
    """获取最近添加的新闻（按添加时间倒序）

    Args:
        limit: 返回数量
        offset: 偏移量

    Returns:
        JSON格式的新闻列表
    """
    return await get_recent_news_tool(limit=limit, offset=offset)


@server.tool(name="news_storage_update_content")
async def update_news_content(
    url: str, content: str, html_content: str = ""
) -> str:
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
async def get_news_stats() -> str:
    """获取统计信息

    Returns:
        JSON格式的统计数据
    """
    return await get_news_stats_tool()


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
