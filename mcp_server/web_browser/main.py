"""
Web Browser MCP Server - 智能浏览器与搜索工具

提供多个搜索引擎的搜索功能（百度、必应、搜狗、谷歌、360）
支持网页内容获取、文章解析、热点追踪等功能
使用 Playwright 浏览器自动化，完美解决反爬虫问题

架构：
- config/: 配置管理（基于 Pydantic）
- core/: 核心功能（浏览器池、速率限制器）
- engines/: 搜索引擎实现（基类 + 具体引擎）
- tools/: 浏览与搜索工具（统一的接口）
- utils/: 辅助函数
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP
from loguru import logger

from .config.settings import get_settings
from .tools import (
    baidu_search,
    baidu_news_search,
    bing_search,
    bing_news_search,
    sogou_search,
    sogou_news_search,
    google_search,
    google_news_search,
    search_360,
    search_360_news,
    multi_search,
    fetch_article_content,
    baidu_hot_search,
)

# 初始化配置
settings = get_settings()
logger.info(f"🚀 Web Browser MCP Server 启动")
logger.info(f"   启用的搜索引擎: {', '.join(settings.enabled_engines)}")

# 创建 FastMCP 服务器
server = FastMCP("web_browser")


# ========== 注册工具函数 ==========


@server.tool(name="web-browser_baidu_search_tool")
async def baidu_search_tool(
    query: str,
    num_results: int = 30,
    time_range: Optional[str] = None,
) -> str:
    """百度搜索 - 🔥 主要的网页搜索与数据获取工具

    使用 Playwright 浏览器自动化，支持：
    - 搜索最新新闻、热点话题
    - 查找特定关键词的网页内容
    - 获取各类资讯和数据

    Args:
        query: 搜索查询（支持中文，如 "人工智能最新进展"）
        num_results: 返回结果数量（默认 30，建议 20-50）
        time_range: 时间范围过滤（暂不支持，保留参数）

    Returns:
        JSON 格式的搜索结果，包含标题、链接、摘要、来源等

    Examples:
        - baidu_search_tool("人工智能最新消息", 30)  # 搜索AI相关新闻
        - baidu_search_tool("股市今日行情", 40)     # 搜索股市行情
        - baidu_search_tool("Python教程", 20)       # 搜索编程教程
    """
    return await baidu_search(query, num_results, time_range)


@server.tool(name="web-browser_baidu_news_search_tool")
async def baidu_news_search_tool(
    query: str,
    num_results: int = 30,
) -> str:
    """百度新闻搜索 - 专门搜索新闻内容

    使用 Playwright 浏览器自动化，完美解决反爬虫问题

    Args:
        query: 搜索查询（如 "人工智能"、"科技新闻"）
        num_results: 返回结果数量（默认 30，建议 30-50）

    Returns:
        JSON 格式的新闻搜索结果
    """
    return await baidu_news_search(query, num_results)


@server.tool(name="web-browser_bing_search_tool")
async def bing_search_tool(
    query: str,
    num_results: int = 30,
) -> str:
    """必应搜索 - 使用微软必应搜索引擎

    Args:
        query: 搜索关键词（如 "人工智能"、"科技新闻"）
        num_results: 返回结果数量（默认 30，建议 20-40）

    Returns:
        JSON 格式的搜索结果

    Examples:
        - bing_search_tool("人工智能最新消息", 30)
        - bing_search_tool("Python编程教程", 20)
    """
    return await bing_search(query, num_results)


@server.tool(name="web-browser_bing_news_search_tool")
async def bing_news_search_tool(
    query: str,
    num_results: int = 30,
) -> str:
    """必应新闻搜索 - 使用微软必应新闻搜索

    Args:
        query: 搜索关键词（如 "人工智能"、"科技"）
        num_results: 返回结果数量（默认 30，建议 20-50）

    Returns:
        JSON 格式的新闻搜索结果

    Examples:
        - bing_news_search_tool("科技", 30)
        - bing_news_search_tool("人工智能", 40)
    """
    return await bing_news_search(query, num_results)


@server.tool(name="web-browser_sogou_search_tool")
async def sogou_search_tool(
    query: str,
    num_results: int = 30,
) -> str:
    """搜狗搜索 - 使用搜狗搜索引擎

    Args:
        query: 搜索关键词（如 "人工智能"、"科技新闻"）
        num_results: 返回结果数量（默认 30，建议 20-40）

    Returns:
        JSON 格式的搜索结果

    Examples:
        - sogou_search_tool("人工智能最新消息", 30)
        - sogou_search_tool("Python编程教程", 20)
    """
    return await sogou_search(query, num_results)


@server.tool(name="web-browser_sogou_news_search_tool")
async def sogou_news_search_tool(
    query: str,
    num_results: int = 30,
) -> str:
    """搜狗新闻搜索 - 使用搜狗新闻搜索

    Args:
        query: 搜索关键词（如 "人工智能"、"科技"）
        num_results: 返回结果数量（默认 30，建议 20-50）

    Returns:
        JSON 格式的新闻搜索结果

    Examples:
        - sogou_news_search_tool("科技", 30)
        - sogou_news_search_tool("人工智能", 40)
    """
    return await sogou_news_search(query, num_results)


@server.tool(name="web-browser_google_search_tool")
async def google_search_tool(
    query: str,
    num_results: int = 30,
) -> str:
    """谷歌搜索 - 使用谷歌搜索引擎

    Args:
        query: 搜索关键词（如 "人工智能"、"科技新闻"）
        num_results: 返回结果数量（默认 30，建议 20-40）

    Returns:
        JSON 格式的搜索结果

    Examples:
        - google_search_tool("人工智能最新消息", 30)
        - google_search_tool("Python编程教程", 20)
    """
    return await google_search(query, num_results)


@server.tool(name="web-browser_google_news_search_tool")
async def google_news_search_tool(
    query: str,
    num_results: int = 30,
) -> str:
    """谷歌新闻搜索 - 使用谷歌新闻搜索

    Args:
        query: 搜索关键词（如 "人工智能"、"科技"）
        num_results: 返回结果数量（默认 30，建议 20-50）

    Returns:
        JSON 格式的新闻搜索结果

    Examples:
        - google_news_search_tool("科技", 30)
        - google_news_search_tool("人工智能", 40)
    """
    return await google_news_search(query, num_results)


@server.tool(name="web-browser_search_360_tool")
async def search_360_tool(
    query: str,
    num_results: int = 30,
) -> str:
    """360搜索 - 使用360搜索引擎

    Args:
        query: 搜索关键词（如 "人工智能"、"科技新闻"）
        num_results: 返回结果数量（默认 30，建议 20-40）

    Returns:
        JSON 格式的搜索结果

    Examples:
        - search_360_tool("人工智能最新消息", 30)
        - search_360_tool("Python编程教程", 20)
    """
    return await search_360(query, num_results)


@server.tool(name="web-browser_search_360_news_tool")
async def search_360_news_tool(
    query: str,
    num_results: int = 30,
) -> str:
    """360新闻搜索 - 使用360新闻搜索

    Args:
        query: 搜索关键词（如 "人工智能"、"科技"）
        num_results: 返回结果数量（默认 30，建议 20-50）

    Returns:
        JSON 格式的新闻搜索结果

    Examples:
        - search_360_news_tool("科技", 30)
        - search_360_news_tool("人工智能", 40)
    """
    return await search_360_news(query, num_results)


@server.tool(name="web-browser_multi_search_tool")
async def multi_search_tool(
    query: str,
    engine: str = "auto",
    num_results: int = 30,
    search_type: str = "web",
) -> str:
    """多搜索引擎 - 支持百度、必应、搜狗、谷歌、360等多个搜索引擎

    Args:
        query: 搜索关键词（如 "人工智能"、"科技新闻"）
        engine: 搜索引擎选择 ("auto", "baidu", "bing", "sogou", "google", "360")
               - auto: 随机选择引擎（推荐，增加成功率）
               - baidu: 百度搜索
               - bing: 必应搜索
               - sogou: 搜狗搜索
               - google: 谷歌搜索
               - 360: 360搜索
        num_results: 返回结果数量（默认 30）
        search_type: 搜索类型 ("web" 网页搜索, "news" 新闻搜索)

    Returns:
        JSON 格式的搜索结果，包含引擎名称、标题、链接、摘要、来源等

    Examples:
        - multi_search_tool("人工智能", "auto", 30, "web")  # 随机引擎搜索
        - multi_search_tool("科技新闻", "bing", 20, "news")  # 必应新闻搜索
        - multi_search_tool("股市行情", "sogou", 30, "web")  # 搜狗网页搜索
    """
    return await multi_search(query, engine, num_results, search_type)


@server.tool(name="web-browser_fetch_article_content_tool")
async def fetch_article_content_tool(url: str) -> str:
    """访问网页并提取内容 - 🔥 使用浏览器池复用浏览器实例

    功能：
    - 访问任意网页并提取正文内容
    - 自动处理动态加载的内容
    - 智能提取标题、正文、发布时间等

    Args:
        url: 网页链接（支持各类网站）

    Returns:
        JSON 格式的网页内容，包含标题、正文、来源等

    Examples:
        >>> fetch_article_content_tool("https://news.example.com/article/123")
        >>> fetch_article_content_tool("https://blog.example.com/post/456")
    """
    return await fetch_article_content(url)


@server.tool(name="web-browser_baidu_hot_search_tool")
async def baidu_hot_search_tool() -> str:
    """获取百度热搜榜 - 使用 Playwright 浏览器自动化

    Returns:
        JSON 格式的热搜榜单（前50条）
    """
    return await baidu_hot_search()


if __name__ == "__main__":
    server.run()
