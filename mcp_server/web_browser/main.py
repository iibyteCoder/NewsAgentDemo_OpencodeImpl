"""
Web Browser MCP Server - 智能浏览器与搜索工具

提供智能多引擎搜索功能，支持10个浏览器搜索引擎 + 1个API搜索引擎（Serper）
浏览器引擎：百度、必应、搜狗、谷歌、360、今日头条、腾讯、网易、新浪、搜狐
API引擎：Serper.dev（Google Search API，无需浏览器）

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

from loguru import logger
from mcp.server.fastmcp import FastMCP

from mcp_server.web_browser.config.settings import get_settings
from mcp_server.web_browser.tools import (
    fetch_article_content,
    multi_search,
)

# 初始化配置
settings = get_settings()

# 创建 FastMCP 服务器
server = FastMCP(
    name="web_browser",
    # 可用性配置
    retry_interval=5,  # 连接重试间隔（秒）
    stateless_http=True,  # 无状态 HTTP 模式（提高可扩展性）
    json_response=True,  # 使用 JSON 响应格式
    # 监控配置
    log_level="INFO",
    debug=False,
)


# ========== 注册工具函数 ==========


@server.tool(name="web-browser_multi_search_tool")
async def multi_search_tool(
    query: str,
    engine: str = "auto",
    num_results: int = 30,
    search_type: str = "web",
) -> str:
    """智能多引擎搜索（支持11个搜索引擎，自动切换）

    Args:
        query: 搜索关键词
        engine: 搜索引擎 (auto|baidu|bing|sogou|google|360|toutiao|tencent|wangyi|sina|sohu|serper)
        num_results: 返回数量（默认30）
        search_type: 搜索类型 (web|news)

    Returns:
        JSON格式，包含：engine, engine_name, total, results[{title, url, snippet, source}]

    推荐使用 auto 模式自动选择可用引擎。
    serper 为 API 引擎（无需浏览器），需要配置 SERPER_API_KEY 环境变量。
    返回结构详见: docs/MCP工具使用说明.md
    """
    result = await multi_search(query, engine, num_results, search_type)

    # 记录统计信息
    import json

    result_data = json.loads(result)
    available = result_data.get("available_engines", "?")
    banned = result_data.get("banned_engines", "?")

    if result_data.get("total", 0) > 0:
        logger.info(
            f"   ✅ 搜索成功: {result_data.get('engine_name')} 返回 {result_data.get('total')} 条结果"
        )
        logger.info(f"   📊 引擎状态: 可用 {available} 个, 被禁用 {banned} 个")
    else:
        logger.warning("   ⚠️ 搜索失败或返回0条结果")
        logger.warning(f"   📊 引擎状态: 可用 {available} 个, 被禁用 {banned} 个")

    return result


@server.tool(name="web-browser_fetch_article_content_tool")
async def fetch_article_content_tool(
    url: str,
    include_images: bool = True,
) -> str:
    """获取网页文章内容和图片链接

    使用浏览器访问网页，智能提取文章正文、标题和图片链接。
    自动处理动态内容，包含页面质量检测。

    Args:
        url: 文章URL
        include_images: 是否提取图片链接（默认True）

    Returns:
        JSON格式，包含：url, title, content, content_length,
        images[{url, alt, width, height}], image_count, status

    返回结构详见: docs/MCP工具使用说明.md
    """
    return await fetch_article_content(url, include_images)


if __name__ == "__main__":
    server.run()
