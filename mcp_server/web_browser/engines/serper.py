"""Serper.dev 搜索引擎 - 使用 Google Search API（不依赖浏览器）"""

import os
from dataclasses import dataclass
from typing import List, Optional

import httpx
from loguru import logger


@dataclass
class SearchResult:
    """搜索结果"""

    title: str
    url: str
    summary: str = ""
    source: str = ""
    time: str = ""


@dataclass
class SerperConfig:
    """Serper 配置"""

    api_key: str
    search_url: str = "https://google.serper.dev/search"
    news_url: str = "https://google.serper.dev/news"
    timeout: int = 30


class SerperEngine:
    """Serper.dev 搜索引擎 - 使用 API 而非浏览器

    特点：
    - 不需要 Playwright 浏览器
    - 直接通过 HTTP API 调用 Google 搜索
    - 速度快，稳定性高
    - 需要 API Key（从 https://serper.dev 获取）
    """

    def __init__(self, api_key: Optional[str] = None):
        """初始化 Serper 引擎

        Args:
            api_key: Serper API Key，如果不提供则从环境变量读取
        """
        # 尝试从多个来源获取 API Key
        self.api_key = api_key or os.getenv("SERPER_API_KEY")

        if not self.api_key:
            logger.warning("⚠️ SERPER_API_KEY 未配置，Serper 搜索将不可用")

        self.name = "Serper"

    @property
    def engine_id(self) -> str:
        """引擎ID"""
        return "serper"

    def is_available(self) -> bool:
        """检查引擎是否可用"""
        return bool(self.api_key)

    async def search(
        self,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行搜索

        Args:
            query: 搜索关键词
            num_results: 返回结果数量（最大100）
            search_type: 搜索类型 ("web" 或 "news")

        Returns:
            搜索结果列表
        """
        if not self.api_key:
            logger.error("❌ SERPER_API_KEY 未配置")
            return []

        # 构建请求 URL
        url = self.config.news_url if search_type == "news" else self.config.search_url

        # 构建请求参数
        payload = {
            "q": query,
            "num": min(num_results, 100),  # Serper 最大支持 100
        }

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        logger.info(f"   🔍 [Serper] {query} ({search_type})")

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                # 解析结果
                results = []

                # 处理普通搜索结果
                if "organic" in data:
                    for item in data["organic"][:num_results]:
                        results.append(
                            SearchResult(
                                title=item.get("title", ""),
                                url=item.get("link", ""),
                                summary=item.get("snippet", ""),
                                source=self._extract_domain(item.get("link", "")),
                                time="",
                            )
                        )

                # 处理新闻结果
                elif "news" in data:
                    for item in data["news"][:num_results]:
                        results.append(
                            SearchResult(
                                title=item.get("title", ""),
                                url=item.get("link", ""),
                                summary=item.get("snippet", ""),
                                source=item.get("source", ""),
                                time=item.get("date", ""),
                            )
                        )

                logger.info(f"   ✅ [Serper] 成功获取 {len(results)} 条结果")
                return results

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("❌ [Serper] API 认证失败，请检查 API Key")
            elif e.response.status_code == 429:
                logger.error("❌ [Serper] API 请求超限，请稍后重试")
            elif e.response.status_code == 403:
                logger.error("❌ [Serper] API 访问被拒绝，可能需要付费计划")
            else:
                logger.error(f"❌ [Serper] API 错误: {e.response.status_code}")
            return []

        except httpx.RequestError as e:
            logger.error(f"❌ [Serper] 请求失败: {e}")
            return []

        except Exception as e:
            logger.error(f"❌ [Serper] 搜索失败: {e}")
            return []

    @property
    def config(self) -> SerperConfig:
        """获取配置"""
        return SerperConfig(api_key=self.api_key or "")

    @staticmethod
    def _extract_domain(url: str) -> str:
        """从 URL 中提取域名"""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.netloc or "unknown"
        except Exception:
            return "unknown"

    def extract_domain(self, url: str) -> str:
        """从 URL 中提取域名（公开方法）"""
        return self._extract_domain(url)

    def get_search_url(
        self, _query: str, _num_results: int, search_type: str = "web"
    ) -> str:
        """构建搜索 URL（用于兼容，实际不使用）"""
        return self.config.news_url if search_type == "news" else self.config.search_url
