"""下载工具函数"""

import json
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from ..core.config import get_settings
from ..core.downloader import Downloader
from ..utils.helpers import extract_image_urls, sanitize_filename


async def download_file(
    url: str,
    save_path: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    """下载单个文件

    Args:
        url: 文件URL
        save_path: 保存目录路径（可选，默认使用downloads目录）
        filename: 保存的文件名（可选，默认从URL提取）

    Returns:
        JSON格式的下载结果
    """
    async with Downloader() as downloader:
        save_dir = Path(save_path) if save_path else None
        result = await downloader.download(url, save_dir, filename)
        return json.dumps(result, ensure_ascii=False, indent=2)


async def download_files(
    urls: list[str],
    save_path: Optional[str] = None,
    max_concurrent: Optional[int] = None,
) -> str:
    """批量下载文件

    Args:
        urls: 文件URL列表
        save_path: 保存目录路径（可选）
        max_concurrent: 最大并发下载数（可选）

    Returns:
        JSON格式的批量下载结果
    """
    async with Downloader() as downloader:
        save_dir = Path(save_path) if save_path else None
        results = await downloader.download_batch(urls, save_dir, max_concurrent)

        # 添加统计信息
        success_count = sum(1 for r in results if r.get("success"))
        summary = {
            "total": len(urls),
            "success": success_count,
            "failed": len(urls) - success_count,
            "results": results,
        }

        return json.dumps(summary, ensure_ascii=False, indent=2)


async def download_images_from_html(
    html_content: str,
    base_url: Optional[str] = None,
    save_path: Optional[str] = None,
    max_concurrent: Optional[int] = None,
) -> str:
    """从HTML内容中提取并下载所有图片

    Args:
        html_content: HTML内容
        base_url: 基础URL（用于处理相对路径）
        save_path: 保存目录路径（可选）
        max_concurrent: 最大并发下载数（可选）

    Returns:
        JSON格式的下载结果
    """
    logger.info("开始从HTML中提取图片URL")

    # 提取图片URL
    image_urls = extract_image_urls(html_content, base_url)

    if not image_urls:
        return json.dumps(
            {
                "total": 0,
                "success": 0,
                "failed": 0,
                "message": "未找到图片URL",
                "results": [],
            },
            ensure_ascii=False,
            indent=2,
        )

    logger.info(f"找到 {len(image_urls)} 个图片URL")

    # 批量下载
    async with Downloader() as downloader:
        save_dir = Path(save_path) if save_path else None
        results = await downloader.download_batch(image_urls, save_dir, max_concurrent)

        # 添加统计信息
        success_count = sum(1 for r in results if r.get("success"))
        summary = {
            "total": len(image_urls),
            "success": success_count,
            "failed": len(image_urls) - success_count,
            "results": results,
        }

        return json.dumps(summary, ensure_ascii=False, indent=2)


async def download_images_from_url(
    page_url: str,
    save_path: Optional[str] = None,
    max_concurrent: Optional[int] = None,
) -> str:
    """从网页URL中提取并下载所有图片

    Args:
        page_url: 网页URL
        save_path: 保存目录路径（可选）
        max_concurrent: 最大并发下载数（可选）

    Returns:
        JSON格式的下载结果
    """
    import httpx

    logger.info(f"正在获取网页内容: {page_url}")

    async with Downloader() as downloader:
        client = await downloader._get_client()

        try:
            response = await client.get(page_url)
            response.raise_for_status()
            html_content = response.text

            logger.info("网页内容获取成功，开始提取图片")

            # 使用提取的URL作为base_url
            return await download_images_from_html(
                html_content, page_url, save_path, max_concurrent
            )

        except Exception as e:
            logger.error(f"获取网页内容失败: {e}")
            return json.dumps(
                {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "error": str(e),
                    "message": f"获取网页内容失败: {e}",
                },
                ensure_ascii=False,
                indent=2,
            )
