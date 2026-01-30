"""
报告部分数据库扩展

添加 report_sections 表和相关操作，用于存储各个环节生成的报告数据。
"""

import aiosqlite
import json
from typing import List, Optional
from loguru import logger

from .report_sections_model import ReportSection, ContentTemplates


class ReportSectionsDatabase:
    """报告部分数据库管理器（扩展功能）"""

    def __init__(self, news_db):
        """初始化报告部分数据库

        Args:
            news_db: NewsDatabase 实例（共享连接）
        """
        self.news_db = news_db

    async def _ensure_report_sections_table(self):
        """确保 report_sections 表存在"""
        conn = await self.news_db._ensure_connection()
        cursor = await conn.cursor()

        # 创建 report_sections 表
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS report_sections (
                section_id TEXT PRIMARY KEY,
                section_type TEXT NOT NULL,
                session_id TEXT NOT NULL,
                event_name TEXT NOT NULL,
                category TEXT NOT NULL,
                content_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                error_message TEXT DEFAULT ''
            )
        """
        )

        # 创建索引
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_sections_session_event ON report_sections(session_id, event_name)"""
        )
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_sections_type ON report_sections(section_type)"""
        )
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_sections_status ON report_sections(status)"""
        )

        await conn.commit()
        logger.debug("📊 report_sections 表创建完成")

    async def save_section(
        self,
        section_type: str,
        session_id: str,
        event_name: str,
        category: str,
        content_data: dict,
    ) -> str:
        """保存报告部分

        Args:
            section_type: 部分类型（validation/timeline/prediction/summary/news/images）
            session_id: 会话ID
            event_name: 事件名称
            category: 类别
            content_data: 内容数据（字典）

        Returns:
            section_id
        """
        await self._ensure_report_sections_table()

        conn = await self.news_db._ensure_connection()
        cursor = await conn.cursor()

        # 生成 section_id
        section_id = f"{session_id}_{event_name}_{section_type}".replace("/", "_").replace("\\", "_")

        # 转换为 JSON
        content_json = json.dumps(content_data, ensure_ascii=False, indent=2)

        # 插入或更新
        await cursor.execute(
            """
            INSERT OR REPLACE INTO report_sections
            (section_id, section_type, session_id, event_name, category, content_data, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP)
        """,
            (section_id, section_type, session_id, event_name, category, content_json),
        )

        await conn.commit()
        logger.info(f"✅ 保存报告部分: {section_type} - {event_name}")
        return section_id

    async def get_section(
        self, session_id: str, event_name: str, section_type: str
    ) -> Optional[ReportSection]:
        """获取单个报告部分

        Args:
            session_id: 会话ID
            event_name: 事件名称
            section_type: 部分类型

        Returns:
            ReportSection 对象，不存在则返回 None
        """
        await self._ensure_report_sections_table()

        conn = await self.news_db._ensure_connection()
        cursor = await conn.cursor()

        await cursor.execute(
            """
            SELECT section_id, section_type, session_id, event_name, category,
                   content_data, created_at, updated_at, status, error_message
            FROM report_sections
            WHERE session_id = ? AND event_name = ? AND section_type = ?
        """,
            (session_id, event_name, section_type),
        )

        row = await cursor.fetchone()
        if row:
            return ReportSection(
                section_id=row[0],
                section_type=row[1],
                session_id=row[2],
                event_name=row[3],
                category=row[4],
                content_data=row[5],
                created_at=row[6],
                updated_at=row[7],
                status=row[8],
                error_message=row[9],
            )
        return None

    async def get_all_sections(
        self, session_id: str, event_name: str
    ) -> List[ReportSection]:
        """获取事件的所有报告部分

        Args:
            session_id: 会话ID
            event_name: 事件名称

        Returns:
            ReportSection 对象列表
        """
        await self._ensure_report_sections_table()

        conn = await self.news_db._ensure_connection()
        cursor = await conn.cursor()

        await cursor.execute(
            """
            SELECT section_id, section_type, session_id, event_name, category,
                   content_data, created_at, updated_at, status, error_message
            FROM report_sections
            WHERE session_id = ? AND event_name = ?
            ORDER BY section_type
        """,
            (session_id, event_name),
        )

        rows = await cursor.fetchall()
        return [
            ReportSection(
                section_id=row[0],
                section_type=row[1],
                session_id=row[2],
                event_name=row[3],
                category=row[4],
                content_data=row[5],
                created_at=row[6],
                updated_at=row[7],
                status=row[8],
                error_message=row[9],
            )
            for row in rows
        ]

    async def get_sections_summary(
        self, session_id: str, event_name: str
    ) -> dict:
        """获取事件各部分的摘要（不包含完整内容）

        Args:
            session_id: 会话ID
            event_name: 事件名称

        Returns:
            摘要字典：{section_type: {status, created_at, ...}}
        """
        await self._ensure_report_sections_table()

        conn = await self.news_db._ensure_connection()
        cursor = await conn.cursor()

        await cursor.execute(
            """
            SELECT section_type, status, created_at, updated_at, error_message
            FROM report_sections
            WHERE session_id = ? AND event_name = ?
        """,
            (session_id, event_name),
        )

        rows = await cursor.fetchall()
        return {
            row[0]: {
                "status": row[1],
                "created_at": row[2],
                "updated_at": row[3],
                "error_message": row[4],
            }
            for row in rows
        }

    async def mark_section_failed(
        self, session_id: str, event_name: str, section_type: str, error_message: str
    ):
        """标记部分为失败状态

        Args:
            session_id: 会话ID
            event_name: 事件名称
            section_type: 部分类型
            error_message: 错误信息
        """
        await self._ensure_report_sections_table()

        conn = await self.news_db._ensure_connection()
        cursor = await conn.cursor()

        section_id = f"{session_id}_{event_name}_{section_type}".replace("/", "_").replace("\\", "_")

        await cursor.execute(
            """
            INSERT OR REPLACE INTO report_sections
            (section_id, section_type, session_id, event_name, category, content_data, status, error_message, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'failed', ?, CURRENT_TIMESTAMP)
        """,
            (section_id, section_type, session_id, event_name, "", "{}", error_message),
        )

        await conn.commit()
        logger.warning(f"⚠️ 标记部分失败: {section_type} - {event_name}: {error_message}")

    async def delete_event_sections(self, session_id: str, event_name: str):
        """删除事件的所有部分

        Args:
            session_id: 会话ID
            event_name: 事件名称
        """
        await self._ensure_report_sections_table()

        conn = await self.news_db._ensure_connection()
        cursor = await conn.cursor()

        await cursor.execute(
            "DELETE FROM report_sections WHERE session_id = ? AND event_name = ?",
            (session_id, event_name),
        )

        await conn.commit()
        logger.info(f"🗑️ 删除事件的所有部分: {event_name}")
