"""速率限制器 - 基于域名和搜索引擎的速率限制"""

import asyncio
import time
from typing import Optional

from loguru import logger


class RateLimiter:
    """速率限制器 - 支持域名和搜索引擎两个维度的速率限制"""

    def __init__(
        self,
        time_window: float = 1.0,
        max_domain_requests: int = 2,
        max_engine_requests: int = 2,
    ):
        """
        Args:
            time_window: 时间窗口（秒）
            max_domain_requests: 同一域名时间窗口内最大请求数
            max_engine_requests: 同一搜索引擎时间窗口内最大请求数
        """
        self.time_window = time_window
        self.max_domain_requests = max_domain_requests
        self.max_engine_requests = max_engine_requests

        # 域名维度的请求记录 {domain: [timestamps]}
        self.domain_requests: dict = {}

        # 搜索引擎维度的请求记录 {engine_name: [timestamps]}
        self.engine_requests: dict = {}

        self._lock = asyncio.Lock()

    def _extract_domain(self, url: str) -> str:
        """从URL中提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or "unknown"
        except Exception:
            return "unknown"

    async def acquire(
        self,
        domain: Optional[str] = None,
        engine: Optional[str] = None,
    ) -> None:
        """获取访问许可（支持域名和引擎两个维度的速率限制）

        Args:
            domain: 域名（可选，用于域名级别的限流）
            engine: 搜索引擎名称（可选，用于引擎级别的限流）

        Note:
            移除了全局限制，允许不同域名/引擎的并发请求
        """
        async with self._lock:
            now = time.time()

            # 1. 域名级别速率限制
            if domain:
                await self._acquire_domain(now, domain)

            # 2. 搜索引擎级别速率限制
            if engine:
                await self._acquire_engine(now, engine)

    async def _acquire_domain(self, now: float, domain: str) -> None:
        """域名级别的速率限制"""
        if domain not in self.domain_requests:
            self.domain_requests[domain] = []

        # 清理过期记录
        self.domain_requests[domain] = [
            t for t in self.domain_requests[domain] if now - t < self.time_window
        ]

        if len(self.domain_requests[domain]) >= self.max_domain_requests:
            sleep_time = self.time_window - (now - self.domain_requests[domain][0])
            if sleep_time > 0:
                logger.debug(f"⏸️ [域名限制 {domain}] 等待 {sleep_time:.2f} 秒")
                await asyncio.sleep(sleep_time)
                now = time.time()
                self.domain_requests[domain] = [
                    t for t in self.domain_requests[domain] if now - t < self.time_window
                ]

        self.domain_requests[domain].append(now)

    async def _acquire_engine(self, now: float, engine: str) -> None:
        """搜索引擎级别的速率限制"""
        if engine not in self.engine_requests:
            self.engine_requests[engine] = []

        # 清理过期记录
        self.engine_requests[engine] = [
            t for t in self.engine_requests[engine] if now - t < self.time_window
        ]

        if len(self.engine_requests[engine]) >= self.max_engine_requests:
            sleep_time = self.time_window - (now - self.engine_requests[engine][0])
            if sleep_time > 0:
                logger.debug(f"⏸️ [引擎限制 {engine}] 等待 {sleep_time:.2f} 秒")
                await asyncio.sleep(sleep_time)
                now = time.time()
                self.engine_requests[engine] = [
                    t for t in self.engine_requests[engine] if now - t < self.time_window
                ]

        self.engine_requests[engine].append(now)
