"""数据库模块导出

公共接口：
- get_db_manager: 获取数据库管理器
- NewsRepository: 新闻数据访问层
- ReportSectionRepository: 报告部分数据访问层
- 所有模型类
"""

from .base import Base
from .models import NewsItem, ReportSection, SectionStatus, SectionType
from .repositories import NewsRepository, ReportSectionRepository
from .session import DatabaseManager, get_db_manager

__all__ = [
    # 基础
    "Base",
    # 模型
    "NewsItem",
    "ReportSection",
    "SectionType",
    "SectionStatus",
    # 会话管理
    "DatabaseManager",
    "get_db_manager",
    # 仓储
    "NewsRepository",
    "ReportSectionRepository",
]
