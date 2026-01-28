"""
Web Browser MCP Server - 智能浏览器与搜索工具

提供智能多引擎搜索功能，支持10个搜索引擎（百度、必应、搜狗、谷歌、360、今日头条、腾讯、网易、新浪、搜狐）
支持网页内容获取、文章解析、热点追踪等功能
使用 Playwright 浏览器自动化，智能检测并自动禁用被拦截的引擎

架构：
- config/: 配置管理（基于 Pydantic）
- core/: 核心功能（浏览器池、速率限制器）
- engines/: 搜索引擎实现（基类 + 具体引擎）
- tools/: 浏览与搜索工具（统一的接口）
- utils/: 辅助函数

智能特性：
- 自动检测反爬虫拦截
- 自动禁用被拦截的引擎（30分钟）
- 自动选择最佳可用引擎
- 智能降级，确保高可用性
"""

from mcp.server.fastmcp import FastMCP
from loguru import logger

from .config.settings import get_settings
from .tools import multi_search, fetch_article_content, baidu_hot_search

# 初始化配置
settings = get_settings()
logger.info("🚀 Web Browser MCP Server 启动")
logger.info(f"   启用的搜索引擎: {', '.join(settings.enabled_engines)}")
logger.info("   智能反爬虫检测: ✅ 已启用")
logger.info("   自动引擎禁用: ✅ 已启用（5-30分钟递增）")

# 创建 FastMCP 服务器
server = FastMCP("web_browser")


# ========== 注册工具函数 ==========


@server.tool(name="web-browser_multi_search_tool")
async def multi_search_tool(
    query: str,
    engine: str = "auto",
    num_results: int = 30,
    search_type: str = "web",
) -> str:
    """智能多引擎搜索 - 🔥 推荐使用（自动选择最佳可用引擎）

    支持10个搜索引擎，智能检测并自动禁用被拦截的引擎，确保高可用性。

    **智能特性**：
    - 自动检测反爬虫拦截
    - 被拦截的引擎自动禁用30分钟
    - 智能降级，自动切换到可用引擎
    - 随机引擎选择，避免单点故障

    Args:
        query: 搜索关键词（如 "人工智能"、"科技新闻"）
        engine: 搜索引擎选择 ("auto", "baidu", "bing", "sogou", "google", "360", "toutiao", "tencent", "wangyi", "sina", "sohu")
               - auto: 智能选择（推荐，自动选择可用引擎）
               - baidu: 百度搜索
               - bing: 必应搜索
               - sogou: 搜狗搜索
               - google: 谷歌搜索
               - 360: 360搜索
               - toutiao: 今日头条（推荐）
               - tencent: 腾讯新闻（推荐）
               - wangyi: 网易新闻（推荐）
               - sina: 新浪新闻（推荐）
               - sohu: 搜狐新闻（推荐）
        num_results: 返回结果数量（默认 30，建议 20-50）
        search_type: 搜索类型 ("web" 网页搜索, "news" 新闻搜索)

    Returns:
        JSON 格式的搜索结果，包含：
        - engine: 使用的引擎ID
        - engine_name: 使用的引擎名称
        - total: 结果数量
        - results: 搜索结果列表
        - available_engines: 当前可用引擎数量
        - blocked: 是否被拦截（仅在发生拦截时）

    Examples:
        - multi_search_tool("人工智能", "auto", 30, "news")  # 智能搜索新闻
        - multi_search_tool("科技新闻", "toutiao", 20, "news")  # 使用今日头条
        - multi_search_tool("股市行情", "tencent", 30, "web")  # 使用腾讯新闻

    Note:
        推荐使用 "auto" 模式，系统会自动选择最佳可用引擎。
        如果某个引擎被拦截，系统会自动禁用它并切换到其他引擎。
        被禁用的引擎将在30分钟后自动解禁。
    """
    result = await multi_search(query, engine, num_results, search_type)

    # 记录统计信息
    import json
    result_data = json.loads(result)
    available = result_data.get("available_engines", "?")
    banned = result_data.get("banned_engines", "?")

    if result_data.get("total", 0) > 0:
        logger.info(f"   ✅ 搜索成功: {result_data.get('engine_name')} 返回 {result_data.get('total')} 条结果")
        logger.info(f"   📊 引擎状态: 可用 {available} 个, 被禁用 {banned} 个")
    else:
        logger.warning(f"   ⚠️ 搜索失败或返回0条结果")
        logger.warning(f"   📊 引擎状态: 可用 {available} 个, 被禁用 {banned} 个")

    return result


@server.tool(name="web-browser_fetch_article_content_tool")
async def fetch_article_content_tool(
    url: str,
    include_images: bool = True,
) -> str:
    """访问网页并提取内容 - 🔥 使用浏览器池复用浏览器实例

    功能：
    - 访问任意网页并提取正文内容
    - 自动处理动态加载的内容
    - 智能提取标题、正文、图片链接等
    - ⭐ 始终检测页面状态和质量（包含HTTP状态、内容质量评估）
    - 支持配合 downloader 工具下载图片

    Args:
        url: 网页链接（支持各类网站）
        include_images: 是否提取图片链接（默认True，提取后可用downloader下载）

    Returns:
        JSON 格式的网页内容，包含：
        - url: 原始URL
        - title: 文章标题
        - content: 正文内容（纯文本）
        - content_length: 内容长度
        - images: 图片链接列表（每个包含url、alt、width、height）
        - image_count: 图片数量
        - status: 页面状态信息（始终包含）
          - status: "ok" | "warning" | "error"
          - reason: 状态原因
          - quality: 内容质量评估（good/acceptable/warning/poor）
          - checks: 检查项列表
          - suggestions: 改进建议列表

    Examples:
        >>> # 获取文章内容（自动包含状态检测和图片）
        >>> fetch_article_content_tool("https://news.example.com/article/123")
        >>> # 只获取文本，不提取图片
        >>> fetch_article_content_tool("https://blog.example.com/post/456", False)

    Note:
        状态检测始终启用，无法关闭。这有助于判断页面质量并做出相应决策。
    """
    return await fetch_article_content(url, include_images)


@server.tool(name="web-browser_baidu_hot_search_tool")
async def baidu_hot_search_tool() -> str:
    """获取百度热搜榜 - 使用 Playwright 浏览器自动化

    Returns:
        JSON 格式的热搜榜单（前50条）
    """
    return await baidu_hot_search()


if __name__ == "__main__":
    server.run()
