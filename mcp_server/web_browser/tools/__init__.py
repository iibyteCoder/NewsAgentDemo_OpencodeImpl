"""工具模块 - 统一的搜索工具"""

from .search_tools import (
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

__all__ = [
    "baidu_search",
    "baidu_news_search",
    "bing_search",
    "bing_news_search",
    "sogou_search",
    "sogou_news_search",
    "google_search",
    "google_news_search",
    "search_360",
    "search_360_news",
    "multi_search",
    "fetch_article_content",
    "baidu_hot_search",
]
