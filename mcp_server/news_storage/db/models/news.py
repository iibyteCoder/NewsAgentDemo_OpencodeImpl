"""
新闻数据模型 - SQLAlchemy 2.0 规范
"""

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin


class NewsItem(Base, TimestampMixin):
    """新闻数据模型"""

    __tablename__ = "news"
    __table_args__ = (
        # 检查约束：确保关键字段不为空
        # 在 SQLAlchemy 2.0 中使用 Check
    )

    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 必填字段
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # 可选字段
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    publish_time: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    event_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON 字段（SQLite 原生支持）
    keywords: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    image_urls: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    local_image_paths: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    tags: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 复合索引
    __mapper_args__ = {
        "eager_defaults": True,
    }

    def __repr__(self) -> str:
        return f"<NewsItem(id={self.id}, title={self.title[:30]!r}, url={self.url[:50]!r})>"

    def to_dict(self) -> dict:
        """转换为字典（用于 API 响应）"""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "source": self.source,
            "publish_time": self.publish_time,
            "author": self.author,
            "event_name": self.event_name,
            "session_id": self.session_id,
            "category": self.category,
            "content": self.content,
            "html_content": self.html_content,
            "keywords": self.keywords,
            "image_urls": self.image_urls,
            "local_image_paths": self.local_image_paths,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_lightweight_dict(self) -> dict:
        """转换为轻量级字典（不包含 content 和 html_content）"""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "source": self.source,
            "publish_time": self.publish_time,
            "author": self.author,
            "event_name": self.event_name,
            "session_id": self.session_id,
            "category": self.category,
            "keywords": self.keywords,
            "image_urls": self.image_urls,
            "local_image_paths": self.local_image_paths,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
