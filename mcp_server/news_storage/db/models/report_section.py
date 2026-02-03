"""
报告部分数据模型 - SQLAlchemy 2.0 规范
"""

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin


# 部分类型常量
class SectionType:
    """报告部分类型常量"""

    VALIDATION = "validation"
    TIMELINE = "timeline"
    PREDICTION = "prediction"
    SUMMARY = "summary"
    NEWS = "news"
    IMAGES = "images"

    @classmethod
    def all(cls) -> list[str]:
        """获取所有部分类型"""
        return [
            cls.VALIDATION,
            cls.TIMELINE,
            cls.PREDICTION,
            cls.SUMMARY,
            cls.NEWS,
            cls.IMAGES,
        ]

    @classmethod
    def descriptions(cls) -> dict[str, str]:
        """获取类型描述"""
        return {
            cls.VALIDATION: "真实性验证",
            cls.TIMELINE: "事件时间轴",
            cls.PREDICTION: "趋势预测",
            cls.SUMMARY: "事件摘要",
            cls.NEWS: "新闻来源",
            cls.IMAGES: "相关图片",
        }

    @classmethod
    def is_valid(cls, section_type: str) -> bool:
        """验证部分类型是否有效"""
        return section_type in cls.all()


# 状态常量
class SectionStatus:
    """报告部分状态常量"""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportSection(Base, TimestampMixin):
    """报告部分数据模型"""

    __tablename__ = "report_sections"

    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 唯一标识（组合键的字符串形式）
    section_id: Mapped[str] = mapped_column(
        String(500), unique=True, index=True, nullable=False
    )

    # 分类字段
    section_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)

    # 数据和状态（TEXT 类型，支持任意格式数据）
    content_data: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SectionStatus.PENDING, index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ReportSection(id={self.id}, section_id={self.section_id!r}, "
            f"type={self.section_type!r})>"
        )

    @classmethod
    def generate_section_id(cls, session_id: str, event_name: str, section_type: str) -> str:
        """生成唯一的 section_id"""
        # 替换特殊字符以避免文件系统问题
        safe_name = (
            event_name.replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
            .replace(":", "_")
        )
        return f"{session_id}_{safe_name}_{section_type}"

    def to_dict(self) -> dict:
        """转换为字典（用于 API 响应）"""
        return {
            "id": self.id,
            "section_id": self.section_id,
            "section_type": self.section_type,
            "session_id": self.session_id,
            "event_name": self.event_name,
            "category": self.category,
            "content_data": self.content_data,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> dict:
        """转换为摘要字典（不包含完整内容）"""
        return {
            "section_type": self.section_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "error_message": self.error_message,
        }
