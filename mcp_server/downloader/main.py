"""
Downloader MCP Server - 文件下载器

提供图片、文档等文件的下载功能：
- 单个文件下载
- 批量下载
- 从文章/网页中提取并下载图片
- 支持自定义保存路径和文件名
- 支持并发下载和重试机制
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP
from loguru import logger

from .core.config import get_settings
from .tools.download_tools import (
    download_file,
    download_files,
    download_images_from_html,
    download_images_from_url,
)

# 初始化配置
settings = get_settings()
logger.info(f"🚀 Downloader MCP Server 启动")
logger.info(f"   默认下载目录: {settings.default_download_dir.absolute()}")
logger.info(f"   最大并发下载数: {settings.max_concurrent_downloads}")

# 创建 FastMCP 服务器
server = FastMCP("downloader")


# ========== 注册工具函数 ==========


@server.tool(name="downloader_download_file")
async def download_file_tool(
    url: str,
    save_path: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    """下载单个文件 - 🔍 支持图片、文档等各类文件

    功能：
    - 从URL下载单个文件到本地
    - 自动处理文件名（可自定义）
    - 支持重试机制
    - 自动创建保存目录

    Args:
        url: 文件URL（如 "https://example.com/image.jpg"）
        save_path: 保存目录路径（可选，默认使用 ./downloads 目录）
        filename: 保存的文件名（可选，默认从URL中提取）

    Returns:
        JSON格式的下载结果，包含：
        - success: 是否成功
        - url: 原始URL
        - filepath: 保存的完整路径
        - filename: 文件名
        - size: 文件大小（字节）
        - message: 结果消息

    Examples:
        >>> # 下载图片到默认目录
        >>> download_file_tool("https://example.com/photo.jpg")
        >>> # 下载到指定目录并指定文件名
        >>> download_file_tool(
        ...     "https://example.com/document.pdf",
        ...     save_path="./documents",
        ...     filename="报告.pdf"
        ... )
    """
    return await download_file(url, save_path, filename)


@server.tool(name="downloader_download_files")
async def download_files_tool(
    urls: list[str],
    save_path: Optional[str] = None,
    max_concurrent: Optional[int] = None,
) -> str:
    """批量下载文件 - ⚡ 支持并发下载多个文件

    功能：
    - 同时下载多个文件
    - 支持自定义并发数量
    - 自动重试失败的下载
    - 返回详细的下载统计

    Args:
        urls: 文件URL列表（如 ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]）
        save_path: 保存目录路径（可选，默认使用 ./downloads 目录）
        max_concurrent: 最大并发下载数（可选，默认为5）

    Returns:
        JSON格式的批量下载结果，包含：
        - total: 总数
        - success: 成功数量
        - failed: 失败数量
        - results: 每个文件的详细结果列表

    Examples:
        >>> # 批量下载图片
        >>> download_files_tool([
        ...     "https://example.com/photo1.jpg",
        ...     "https://example.com/photo2.jpg",
        ...     "https://example.com/photo3.jpg"
        ... ])
        >>> # 自定义并发数
        >>> download_files_tool(
        ...     urls,
        ...     save_path="./images",
        ...     max_concurrent=10
        ... )
    """
    return await download_files(urls, save_path, max_concurrent)


@server.tool(name="downloader_download_images_from_html")
async def download_images_from_html_tool(
    html_content: str,
    base_url: Optional[str] = None,
    save_path: Optional[str] = None,
    max_concurrent: Optional[int] = None,
) -> str:
    """从HTML内容中提取并下载所有图片 - 🖼️ 智能图片提取

    功能：
    - 从HTML代码中智能提取所有图片URL
    - 支持<img>标签、<picture>标签、CSS背景图
    - 自动处理相对路径
    - 批量下载所有图片

    Args:
        html_content: HTML内容字符串
        base_url: 基础URL（用于处理相对路径，可选）
        save_path: 保存目录路径（可选，默认使用 ./downloads 目录）
        max_concurrent: 最大并发下载数（可选）

    Returns:
        JSON格式的下载结果，包含：
        - total: 找到的图片总数
        - success: 成功下载的数量
        - failed: 下载失败的数量
        - results: 每个图片的详细结果列表

    Examples:
        >>> # 从HTML中提取并下载图片
        >>> html = '<html><body><img src="photo.jpg"></body></html>'
        >>> download_images_from_html_tool(html, base_url="https://example.com")
        >>> # 指定保存目录
        >>> download_images_from_html_tool(
        ...     html,
        ...     base_url="https://example.com",
        ...     save_path="./downloaded_images"
        ... )
    """
    return await download_images_from_html(html_content, base_url, save_path, max_concurrent)


@server.tool(name="downloader_download_images_from_url")
async def download_images_from_url_tool(
    page_url: str,
    save_path: Optional[str] = None,
    max_concurrent: Optional[int] = None,
) -> str:
    """从网页URL中提取并下载所有图片 - 🌐 一键下载网页图片

    功能：
    - 自动访问网页并获取HTML内容
    - 智能提取网页中的所有图片
    - 批量下载到本地目录

    Args:
        page_url: 网页URL（如 "https://blog.example.com/article/123"）
        save_path: 保存目录路径（可选，默认使用 ./downloads 目录）
        max_concurrent: 最大并发下载数（可选）

    Returns:
        JSON格式的下载结果，包含：
        - total: 找到的图片总数
        - success: 成功下载的数量
        - failed: 下载失败的数量
        - results: 每个图片的详细结果列表

    Examples:
        >>> # 下载网页中的所有图片
        >>> download_images_from_url_tool("https://blog.example.com/article/123")
        >>> # 指定保存目录和并发数
        >>> download_images_from_url_tool(
        ...     "https://news.example.com/story/456",
        ...     save_path="./news_images",
        ...     max_concurrent=10
        ... )
    """
    return await download_images_from_url(page_url, save_path, max_concurrent)


if __name__ == "__main__":
    server.run()
