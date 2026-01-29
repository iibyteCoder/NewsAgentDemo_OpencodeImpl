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
    """下载单个文件

    Args:
        url: 文件URL
        save_path: 保存目录（可选）
        filename: 保存的文件名（可选）

    Returns:
        JSON格式：{success, url, filepath, filename, size, message}
    """
    return await download_file(url, save_path, filename)


@server.tool(name="downloader_download_files")
async def download_files_tool(
    urls: list[str],
    save_path: Optional[str] = None,
    max_concurrent: Optional[int] = None,
) -> str:
    """批量下载文件（支持并发）

    Args:
        urls: 文件URL列表
        save_path: 保存目录（可选）
        max_concurrent: 最大并发数（可选）

    Returns:
        JSON格式：{total, success, failed, results[{url, success, filepath, message}]}
    """
    return await download_files(urls, save_path, max_concurrent)


@server.tool(name="downloader_download_images_from_html")
async def download_images_from_html_tool(
    html_content: str,
    base_url: Optional[str] = None,
    save_path: Optional[str] = None,
    max_concurrent: Optional[int] = None,
) -> str:
    """从HTML中提取并下载所有图片

    Args:
        html_content: HTML内容
        base_url: 基础URL（处理相对路径，可选）
        save_path: 保存目录（可选）
        max_concurrent: 最大并发数（可选）

    Returns:
        JSON格式：{total, success, failed, results[{url, success, filepath, message}]}
    """
    return await download_images_from_html(html_content, base_url, save_path, max_concurrent)


@server.tool(name="downloader_download_images_from_url")
async def download_images_from_url_tool(
    page_url: str,
    save_path: Optional[str] = None,
    max_concurrent: Optional[int] = None,
) -> str:
    """从网页URL中提取并下载所有图片

    Args:
        page_url: 网页URL
        save_path: 保存目录（可选）
        max_concurrent: 最大并发数（可选）

    Returns:
        JSON格式：{total, success, failed, results[{url, success, filepath, message}]}
    """
    return await download_images_from_url(page_url, save_path, max_concurrent)


if __name__ == "__main__":
    server.run()
