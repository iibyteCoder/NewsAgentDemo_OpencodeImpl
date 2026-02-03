"""
报告部分数据访问层 - Repository 模式

封装所有与 ReportSection 相关的数据库操作
"""

from typing import Any

from loguru import logger
from sqlalchemy import select

from ..models.report_section import ReportSection, SectionStatus, SectionType
from ..session import DatabaseManager


class ReportSectionRepository:
    """报告部分数据访问层"""

    def __init__(self, db_manager: DatabaseManager):
        """初始化仓储

        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager

    async def save(
        self,
        section_type: str,
        session_id: str,
        event_name: str,
        category: str,
        content_data: str,
    ) -> str:
        """保存报告部分

        Args:
            section_type: 部分类型
            session_id: 会话ID
            event_name: 事件名称
            category: 类别
            content_data: 内容数据

        Returns:
            section_id
        """
        async with self.db_manager.session() as session:
            # 生成 section_id
            section_id = ReportSection.generate_section_id(
                session_id, event_name, section_type
            )

            # 查询是否已存在
            result = await session.execute(
                select(ReportSection).where(ReportSection.section_id == section_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # 更新现有记录
                existing.content_data = content_data
                existing.status = SectionStatus.COMPLETED
                existing.category = category
            else:
                # 创建新记录
                db_section = ReportSection(
                    section_id=section_id,
                    section_type=section_type,
                    session_id=session_id,
                    event_name=event_name,
                    category=category,
                    content_data=content_data,
                    status=SectionStatus.COMPLETED,
                )
                session.add(db_section)

            logger.info(f"✅ Saved report section: {section_type} - {event_name}")
            return section_id

    async def get(
        self, session_id: str, event_name: str, section_type: str
    ) -> ReportSection | None:
        """获取单个报告部分

        Args:
            session_id: 会话ID
            event_name: 事件名称
            section_type: 部分类型

        Returns:
            ReportSection 对象，不存在则返回 None
        """
        async with self.db_manager.session() as session:
            section_id = ReportSection.generate_section_id(
                session_id, event_name, section_type
            )

            result = await session.execute(
                select(ReportSection).where(ReportSection.section_id == section_id)
            )
            return result.scalar_one_or_none()

    async def get_all(
        self, session_id: str, event_name: str
    ) -> list[ReportSection]:
        """获取事件的所有报告部分

        Args:
            session_id: 会话ID
            event_name: 事件名称

        Returns:
            ReportSection 对象列表
        """
        async with self.db_manager.session() as session:
            stmt = (
                select(ReportSection)
                .where(
                    ReportSection.session_id == session_id,
                    ReportSection.event_name == event_name,
                )
                .order_by(ReportSection.section_type)
            )

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_summary(
        self, session_id: str, event_name: str
    ) -> dict[str, dict[str, Any]]:
        """获取事件各部分的摘要（不包含完整内容）

        Args:
            session_id: 会话ID
            event_name: 事件名称

        Returns:
            摘要字典：{section_type: {status, created_at, ...}}
        """
        async with self.db_manager.session() as session:
            stmt = (
                select(
                    ReportSection.section_type,
                    ReportSection.status,
                    ReportSection.created_at,
                    ReportSection.updated_at,
                    ReportSection.error_message,
                )
                .where(
                    ReportSection.session_id == session_id,
                    ReportSection.event_name == event_name,
                )
                .order_by(ReportSection.section_type)
            )

            result = await session.execute(stmt)
            return {
                row.section_type: {
                    "status": row.status,
                    "created_at": row.created_at.isoformat()
                    if row.created_at
                    else None,
                    "updated_at": row.updated_at.isoformat()
                    if row.updated_at
                    else None,
                    "error_message": row.error_message,
                }
                for row in result.all()
            }

    async def mark_failed(
        self, session_id: str, event_name: str, section_type: str, error_message: str
    ) -> None:
        """标记部分为失败状态

        Args:
            session_id: 会话ID
            event_name: 事件名称
            section_type: 部分类型
            error_message: 错误信息
        """
        async with self.db_manager.session() as session:
            section_id = ReportSection.generate_section_id(
                session_id, event_name, section_type
            )

            result = await session.execute(
                select(ReportSection).where(ReportSection.section_id == section_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # 更新现有记录
                existing.status = SectionStatus.FAILED
                existing.error_message = error_message
            else:
                # 创建新记录
                db_section = ReportSection(
                    section_id=section_id,
                    section_type=section_type,
                    session_id=session_id,
                    event_name=event_name,
                    category="",  # 失败时可能没有类别信息
                    content_data="",
                    status=SectionStatus.FAILED,
                    error_message=error_message,
                )
                session.add(db_section)

            logger.warning(
                f"⚠️ Marked section failed: {section_type} - {event_name}: {error_message}"
            )

    async def delete_event(self, session_id: str, event_name: str) -> None:
        """删除事件的所有部分

        Args:
            session_id: 会话ID
            event_name: 事件名称
        """
        async with self.db_manager.session() as session:
            stmt = select(ReportSection).where(
                ReportSection.session_id == session_id,
                ReportSection.event_name == event_name,
            )
            result = await session.execute(stmt)
            sections = result.scalars().all()

            for section in sections:
                await session.delete(section)

            logger.info(f"🗑️ Deleted all sections for event: {event_name}")

    @staticmethod
    def get_all_section_types() -> list[dict[str, str]]:
        """获取所有可用的 section_type

        Returns:
            类型列表：[{"type": "...", "description": "..."}, ...]
        """
        return [
            {"type": st, "description": desc}
            for st, desc in SectionType.descriptions().items()
        ]
