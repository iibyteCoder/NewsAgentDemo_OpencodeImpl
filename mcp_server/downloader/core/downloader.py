"""核心下载器"""

import asyncio
import re
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

import httpx
from loguru import logger

from .config import get_settings


class Downloader:
    """文件下载器"""

    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            headers = {
                "User-Agent": self.settings.user_agent,
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
            timeout = httpx.Timeout(self.settings.request_timeout)
            self._client = httpx.AsyncClient(
                headers=headers, timeout=timeout, follow_redirects=True
            )
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def download(
        self,
        url: str,
        save_path: Optional[Path] = None,
        filename: Optional[str] = None,
        retry_count: int = 0,
    ) -> dict[str, str]:
        """下载单个文件

        Args:
            url: 文件URL
            save_path: 保存目录（默认使用配置的默认目录）
            filename: 保存的文件名（默认从URL提取）
            retry_count: 当前重试次数

        Returns:
            下载结果字典，包含 success, url, filepath, message 等字段
        """
        client = await self._get_client()

        # 确定保存目录
        if save_path is None:
            save_path = self.settings.default_download_dir
        else:
            save_path = Path(save_path)
            save_path.mkdir(parents=True, exist_ok=True)

        # 确定文件名
        if filename is None:
            filename = self._extract_filename_from_url(url)
            if not filename:
                # 使用时间戳作为文件名
                import time

                filename = f"file_{int(time.time())}"

        # 完整文件路径
        filepath = save_path / filename

        try:
            logger.info(f"开始下载: {url} -> {filepath}")
            response = await client.get(url)
            response.raise_for_status()

            # 写入文件
            filepath.write_bytes(response.content)

            logger.success(f"下载成功: {filepath}")
            return {
                "success": True,
                "url": url,
                "filepath": str(filepath),
                "filename": filename,
                "size": len(response.content),
                "message": f"成功下载到 {filepath}",
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误: {e.response.status_code} - {url}")
            if retry_count < self.settings.max_retries:
                logger.info(f"重试 {retry_count + 1}/{self.settings.max_retries}")
                await asyncio.sleep(self.settings.retry_delay)
                return await self.download(url, save_path, filename, retry_count + 1)
            return {
                "success": False,
                "url": url,
                "message": f"HTTP错误 {e.response.status_code}",
            }

        except Exception as e:
            logger.error(f"下载失败: {url} - {e}")
            if retry_count < self.settings.max_retries:
                logger.info(f"重试 {retry_count + 1}/{self.settings.max_retries}")
                await asyncio.sleep(self.settings.retry_delay)
                return await self.download(url, save_path, filename, retry_count + 1)
            return {
                "success": False,
                "url": url,
                "message": str(e),
            }

    async def download_batch(
        self,
        urls: list[str],
        save_path: Optional[Path] = None,
        max_concurrent: Optional[int] = None,
    ) -> list[dict[str, str]]:
        """批量下载文件

        Args:
            urls: URL列表
            save_path: 保存目录
            max_concurrent: 最大并发数（默认使用配置值）

        Returns:
            下载结果列表
        """
        if max_concurrent is None:
            max_concurrent = self.settings.max_concurrent_downloads

        logger.info(f"开始批量下载 {len(urls)} 个文件，并发数: {max_concurrent}")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def download_with_semaphore(url: str) -> dict[str, str]:
            async with semaphore:
                return await self.download(url, save_path)

        tasks = [download_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    {
                        "success": False,
                        "url": urls[i],
                        "message": f"异常: {str(result)}",
                    }
                )
            else:
                final_results.append(result)

        # 统计
        success_count = sum(1 for r in final_results if r.get("success"))
        logger.info(
            f"批量下载完成: 成功 {success_count}/{len(urls)}，失败 {len(urls) - success_count}"
        )

        return final_results

    def _extract_filename_from_url(self, url: str) -> Optional[str]:
        """从URL中提取文件名"""
        try:
            parsed = urlparse(url)
            path = parsed.path

            # 从路径中提取文件名
            filename = Path(path).name

            # 如果没有扩展名，尝试从查询参数中获取
            if not filename or "." not in filename:
                query_params = parse_qs(parsed.query)
                # 常见的文件名参数
                for param in ["filename", "file", "name", "title"]:
                    if param in query_params:
                        filename = query_params[param][0]
                        break

            # 清理文件名
            if filename:
                # 移除查询参数
                filename = filename.split("?")[0]
                # URL解码
                from urllib.parse import unquote

                filename = unquote(filename)
                return filename

        except Exception as e:
            logger.warning(f"提取文件名失败: {url} - {e}")

        return None


# 全局下载器实例
_downloader: Optional[Downloader] = None


def get_downloader() -> Downloader:
    """获取下载器单例"""
    global _downloader
    if _downloader is None:
        _downloader = Downloader()
    return _downloader
