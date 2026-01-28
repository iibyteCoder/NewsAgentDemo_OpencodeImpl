"""搜索引擎基类 - 定义统一的接口"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse


@dataclass
class EngineConfig:
    """搜索引擎配置"""
    name: str  # 显示名称
    search_url: str  # 搜索URL模板，使用 {query} 和 {num}
    news_url: str  # 新闻搜索URL模板
    enabled: bool = True  # 是否启用


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    summary: str = ""
    source: str = ""
    time: str = ""


@dataclass
class SearchResultWithStatus:
    """带状态的搜索结果"""
    results: List[SearchResult] = field(default_factory=list)
    blocked: bool = False
    block_reason: str = ""

    def __len__(self):
        return len(self.results)

    def is_empty(self):
        """是否为空（包括被拦截的情况）"""
        return self.blocked or len(self.results) == 0


class BaseEngine(ABC):
    """搜索引擎基类"""

    def __init__(self, config: EngineConfig):
        self.config = config
        self.name = config.name

    @property
    def engine_id(self) -> str:
        """引擎ID（用于配置等）"""
        return self.__class__.__name__.replace("Engine", "").lower()

    @abstractmethod
    async def search(
        self,
        page,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行搜索

        Args:
            page: Playwright Page 对象
            query: 搜索关键词
            num_results: 返回结果数量
            search_type: 搜索类型 ("web" 或 "news")

        Returns:
            搜索结果列表
        """
        pass

    def get_search_url(self, query: str, num_results: int, search_type: str = "web") -> str:
        """构建搜索URL"""
        import urllib.parse

        encoded_query = urllib.parse.quote(query)

        if search_type == "news":
            return self.config.news_url.format(query=encoded_query)
        else:
            return self.config.search_url.format(query=encoded_query, num=num_results)

    @staticmethod
    def extract_domain(url: str) -> str:
        """从URL中提取域名"""
        try:
            parsed = urlparse(url)
            return parsed.netloc or "unknown"
        except Exception:
            return "unknown"

    @staticmethod
    def normalize_url(url: str, base_url: Optional[str] = None) -> str:
        """URL标准化 - 补全相对路径"""
        if not url:
            return url

        import urllib.parse

        # 如果是相对路径，加上域名
        if url.startswith('/') and base_url:
            try:
                parsed_base = urllib.parse.urlparse(base_url)
                return f"{parsed_base.scheme}://{parsed_base.netloc}{url}"
            except Exception:
                pass

        return url
