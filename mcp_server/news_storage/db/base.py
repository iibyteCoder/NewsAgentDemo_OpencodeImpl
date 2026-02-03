"""
数据库基础配置 - SQLAlchemy 2.0

包含：
- Base 类声明
- 通用的 JSON 类型处理
- 时间戳处理
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有模型的基类"""

    pass


class TimestampMixin:
    """时间戳混入类 - 自动管理 created_at 和 updated_at"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def get_datetime_utc() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.now(timezone.utc)
