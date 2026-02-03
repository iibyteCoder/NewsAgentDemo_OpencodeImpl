"""
News Storage MCP Server - 新闻存储管理器

公共接口：
- DatabaseManager: 数据库管理器
- NewsRepository, ReportSectionRepository: 数据访问层
- NewsItem, ReportSection: 数据模型
"""

from .db import (
    DatabaseManager,
    NewsItem,
    NewsRepository,
    ReportSection,
    ReportSectionRepository,
    SectionStatus,
    SectionType,
    get_db_manager,
)

__all__ = [
    # 数据库管理
    "DatabaseManager",
    "get_db_manager",
    # 仓储
    "NewsRepository",
    "ReportSectionRepository",
    # 模型
    "NewsItem",
    "ReportSection",
    "SectionType",
    "SectionStatus",
]
