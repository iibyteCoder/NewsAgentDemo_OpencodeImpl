"""
Web Browser MCP Server - 智能浏览器与搜索工具

提供多个搜索引擎的搜索功能（百度、必应、搜狗、谷歌、360）
支持网页内容获取、文章解析、热点追踪等功能
使用 Playwright 浏览器自动化，完美解决反爬虫问题

架构：
- config/: 配置管理（基于 Pydantic）
- core/: 核心功能（浏览器池、速率限制器）
- engines/: 搜索引擎实现（基类 + 具体引擎）
- tools/: 浏览与搜索工具（统一的接口）
- utils/: 辅助函数
"""

__version__ = "0.2.0"

from .config.settings import Settings, get_settings
from .core import RateLimiter, BrowserPool, get_browser_pool
from .engines import BaseEngine, EngineFactory

__all__ = [
    "Settings",
    "get_settings",
    "RateLimiter",
    "BrowserPool",
    "get_browser_pool",
    "BaseEngine",
    "EngineFactory",
]
