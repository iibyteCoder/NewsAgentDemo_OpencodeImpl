"""
数据库管理器 - SQLite (异步版本)
"""

import aiosqlite
import json
from pathlib import Path
from typing import List, Optional
from loguru import logger

from .models import NewsItem, SearchFilter


class NewsDatabase:
    """新闻数据库管理器 (异步)"""

    def __init__(self, db_path: str = "./data/news_storage.db"):
        """初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn: Optional[aiosqlite.Connection] = None
        self._initialized = False

    async def _ensure_connection(self) -> aiosqlite.Connection:
        """确保数据库已连接和初始化"""
        if not self._initialized or self.conn is None:
            await self._connect()
            await self._create_tables()
            self._initialized = True
            logger.info(f"✅ NewsDatabase 初始化完成: {self.db_path}")
        # 类型断言：此时 conn 一定不为 None
        assert self.conn is not None
        return self.conn

    async def _connect(self):
        """连接数据库"""
        self.conn = await aiosqlite.connect(self.db_path, timeout=30)
        self.conn.row_factory = aiosqlite.Row  # 支持字典式访问

    async def _create_tables(self):
        """创建数据表"""
        cursor = await self.conn.cursor()

        # 主表
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                summary TEXT,
                source TEXT,
                publish_time TEXT,
                author TEXT,
                event_name TEXT,
                content TEXT,
                html_content TEXT,
                keywords TEXT,
                image_urls TEXT,
                local_image_paths TEXT,
                tags TEXT,
                session_id TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 创建索引
        await cursor.execute("""CREATE INDEX IF NOT EXISTS idx_news_url ON news(url)""")
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_source ON news(source)"""
        )
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_created_at ON news(created_at)"""
        )
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_publish_time ON news(publish_time)"""
        )
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_event_name ON news(event_name)"""
        )
        # 新增索引：会话和类别
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_session ON news(session_id)"""
        )
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_category ON news(category)"""
        )
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_session_category ON news(session_id, category)"""
        )

        await self.conn.commit()
        logger.debug("📊 数据表创建完成")

    async def save_news(self, news: NewsItem, session_id: str = "", category: str = "") -> bool:
        """保存单条新闻（允许重复）

        Args:
            news: 新闻对象
            session_id: 会话ID
            category: 类别

        Returns:
            是否插入新记录
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()

        try:
            news_dict = news.to_dict()
            # 覆盖 session_id 和 category
            news_dict["session_id"] = session_id
            news_dict["category"] = category

            # 直接插入（允许重复URL）
            await cursor.execute(
                """
                INSERT INTO news (
                    title, url, summary, source, publish_time, author, event_name,
                    content, html_content, keywords, image_urls, local_image_paths, tags,
                    session_id, category, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    news_dict["title"],
                    news_dict["url"],
                    news_dict["summary"],
                    news_dict["source"],
                    news_dict["publish_time"],
                    news_dict["author"],
                    news_dict["event_name"],
                    news_dict["content"],
                    news_dict["html_content"],
                    news_dict["keywords"],
                    news_dict["image_urls"],
                    news_dict["local_image_paths"],
                    news_dict["tags"],
                    session_id,
                    category,
                    news_dict["created_at"],
                    news_dict["updated_at"],
                ),
            )
            logger.debug(f"✅ 新增新闻: {news.title[:50]}")
            await conn.commit()
            return True

        except aiosqlite.Error as e:
            logger.error(f"❌ 保存新闻失败: {e}")
            await conn.rollback()
            raise

    async def save_news_batch(self, news_list: List[NewsItem]) -> dict:
        """批量保存新闻

        Args:
            news_list: 新闻对象列表

        Returns:
            统计结果 {"added": 数量, "updated": 数量, "failed": 数量}
        """
        added = 0
        updated = 0
        failed = 0

        for news in news_list:
            try:
                if await self.save_news(news):
                    added += 1
                else:
                    updated += 1
            except Exception as e:
                logger.error(f"❌ 保存新闻失败: {news.url[:50]}, 错误: {e}")
                failed += 1

        result = {"added": added, "updated": updated, "failed": failed}
        logger.info(f"📊 批量保存完成: {result}")
        return result

    async def get_news_by_url(
        self, url: str, session_id: str = "", category: str = ""
    ) -> Optional[NewsItem]:
        """根据URL获取新闻

        Args:
            url: 新闻URL
            session_id: 会话ID（可选，用于精确查询）
            category: 类别（可选，用于精确查询）

        Returns:
            新闻对象，不存在则返回None
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()

        if session_id and category:
            await cursor.execute(
                """
                SELECT id, title, url, summary, source, publish_time, author, event_name,
                       content, html_content, keywords, image_urls, local_image_paths, tags,
                       session_id, category, created_at, updated_at
                FROM news WHERE url = ? AND session_id = ? AND category = ?
                """,
                (url, session_id, category),
            )
        else:
            await cursor.execute(
                """
                SELECT id, title, url, summary, source, publish_time, author, event_name,
                       content, html_content, keywords, image_urls, local_image_paths, tags,
                       session_id, category, created_at, updated_at
                FROM news WHERE url = ?
                """,
                (url,),
            )

        row = await cursor.fetchone()
        if row:
            return NewsItem.from_db_row(row)
        return None

    async def search_news(self, filter: SearchFilter) -> List[NewsItem]:
        """搜索新闻（自动过滤会话和类别）

        Args:
            filter: 搜索过滤器（必须包含 session_id）

        Returns:
            新闻列表
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()

        # 构建SQL查询
        conditions = []
        params = []

        # 强制添加会话过滤
        if not filter.session_id:
            logger.warning("⚠️ 搜索时未提供 session_id，可能返回所有数据")
        else:
            conditions.append("session_id = ?")
            params.append(filter.session_id)

        # 添加类别过滤
        if filter.category:
            conditions.append("category = ?")
            params.append(filter.category)

        # 智能搜索：每个词在所有字段中独立搜索（OR关系）
        if filter.search_terms:
            # 为每个搜索词构建条件：(标题 OR 摘要 OR keywords字段 OR 内容)
            term_conditions = []
            for term in filter.search_terms:
                term_pattern = f"%{term}%"
                # 每个词在4个字段中搜索
                term_conditions.append(
                    """(
                    title LIKE ? OR
                    summary LIKE ? OR
                    keywords LIKE ? OR
                    content LIKE ?
                )"""
                )
                params.extend([term_pattern, term_pattern, f'%"{term}"%', term_pattern])

            # 多个词之间是 OR 关系：满足任意一个词即可
            conditions.append(f"({' OR '.join(term_conditions)})")

        # 来源筛选
        if filter.source:
            conditions.append("source = ?")
            params.append(filter.source)

        # 事件名称筛选
        if filter.event_name:
            conditions.append("event_name = ?")
            params.append(filter.event_name)

        # 日期范围筛选
        if filter.start_date:
            conditions.append("created_at >= ?")
            params.append(filter.start_date)

        if filter.end_date:
            conditions.append("created_at <= ?")
            params.append(filter.end_date)

        # 标签筛选
        if filter.tags:
            tag_conditions = []
            for tag in filter.tags:
                tag_conditions.append("tags LIKE ?")
                params.append(f'%"{tag}"%')
            conditions.append(f"({' OR '.join(tag_conditions)})")

        # 组合WHERE子句
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # 执行查询
        query = f"""
            SELECT id, title, url, summary, source, publish_time, author, event_name,
                   content, html_content, keywords, image_urls, local_image_paths, tags,
                   session_id, category, created_at, updated_at
            FROM news
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """

        params.extend([filter.limit, filter.offset])

        await cursor.execute(query, params)
        rows = await cursor.fetchall()

        return [NewsItem.from_db_row(row) for row in rows]

    async def get_recent_news(
        self, limit: int = 100, offset: int = 0, session_id: str = ""
    ) -> List[NewsItem]:
        """获取最近添加的新闻

        Args:
            limit: 返回数量
            offset: 偏移量
            session_id: 会话ID（可选，提供则只返回该会话的新闻）

        Returns:
            新闻列表
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()

        if session_id:
            await cursor.execute(
                """
                SELECT id, title, url, summary, source, publish_time, author, event_name,
                       content, html_content, keywords, image_urls, local_image_paths, tags,
                       session_id, category, created_at, updated_at
                FROM news
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (session_id, limit, offset),
            )
        else:
            await cursor.execute(
                """
                SELECT id, title, url, summary, source, publish_time, author, event_name,
                       content, html_content, keywords, image_urls, local_image_paths, tags,
                       session_id, category, created_at, updated_at
                FROM news
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )

        rows = await cursor.fetchall()
        return [NewsItem.from_db_row(row) for row in rows]

    async def update_news_content(
        self, url: str, content: str, html_content: str = ""
    ) -> bool:
        """更新新闻内容

        Args:
            url: 新闻URL
            content: 纯文本内容
            html_content: HTML内容（可选）

        Returns:
            是否成功
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()
        await cursor.execute(
            """
            UPDATE news
            SET content = ?, html_content = ?, updated_at = CURRENT_TIMESTAMP
            WHERE url = ?
            """,
            (content, html_content, url),
        )

        await conn.commit()
        success = cursor.rowcount > 0

        if success:
            logger.debug(f"📝 更新内容: {url[:50]}")
        else:
            logger.warning(f"⚠️ 未找到新闻: {url[:50]}")

        return success

    async def update_event_name(self, url: str, event_name: str) -> bool:
        """更新新闻的事件名称

        Args:
            url: 新闻URL
            event_name: 事件名称

        Returns:
            是否成功
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()
        await cursor.execute(
            """
            UPDATE news
            SET event_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE url = ?
            """,
            (event_name, url),
        )

        await conn.commit()
        success = cursor.rowcount > 0

        if success:
            logger.debug(f"📝 更新事件名称: {url[:50]} -> {event_name}")
        else:
            logger.warning(f"⚠️ 未找到新闻: {url[:50]}")

        return success

    async def batch_update_event_name(self, urls: List[str], event_name: str) -> dict:
        """批量更新新闻的事件名称

        Args:
            urls: 新闻URL列表
            event_name: 事件名称

        Returns:
            统计结果 {"updated": 更新数量, "failed": 失败数量}
        """
        updated = 0
        failed = 0

        for url in urls:
            if await self.update_event_name(url, event_name):
                updated += 1
            else:
                failed += 1

        result = {"updated": updated, "failed": failed}
        logger.info(f"📊 批量更新事件名称完成: {result}")
        return result

    async def delete_news(self, url: str) -> bool:
        """删除新闻

        Args:
            url: 新闻URL

        Returns:
            是否成功
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()
        await cursor.execute("DELETE FROM news WHERE url = ?", (url,))

        await conn.commit()
        success = cursor.rowcount > 0

        if success:
            logger.debug(f"🗑️ 删除新闻: {url[:50]}")
        else:
            logger.warning(f"⚠️ 未找到新闻: {url[:50]}")

        return success

    async def get_stats(self, session_id: str = "") -> dict:
        """获取统计信息

        Args:
            session_id: 会话ID（可选，提供则只统计该会话）

        Returns:
            统计数据
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()

        # 总数
        if session_id:
            await cursor.execute("SELECT COUNT(*) FROM news WHERE session_id = ?", (session_id,))
        else:
            await cursor.execute("SELECT COUNT(*) FROM news")
        total = (await cursor.fetchone())[0]

        # 按来源统计
        if session_id:
            await cursor.execute(
                """
                SELECT source, COUNT(*) as count
                FROM news
                WHERE session_id = ?
                GROUP BY source
                ORDER BY count DESC
                LIMIT 10
            """,
                (session_id,),
            )
        else:
            await cursor.execute(
                """
                SELECT source, COUNT(*) as count
                FROM news
                GROUP BY source
                ORDER BY count DESC
                LIMIT 10
            """
            )
        by_source = {row[0]: row[1] for row in await cursor.fetchall()}

        # 最近7天添加数量
        if session_id:
            await cursor.execute(
                """
                SELECT COUNT(*) FROM news
                WHERE session_id = ? AND created_at >= datetime('now', '-7 days')
            """,
                (session_id,),
            )
        else:
            await cursor.execute(
                """
                SELECT COUNT(*) FROM news
                WHERE created_at >= datetime('now', '-7 days')
            """
            )
        recent_week = (await cursor.fetchone())[0]

        return {
            "total": total,
            "by_source": by_source,
            "recent_week": recent_week,
            "db_path": str(self.db_path),
        }

    async def get_categories(self, session_id: str) -> List[dict]:
        """获取会话中的所有类别及统计

        Args:
            session_id: 会话ID

        Returns:
            类别列表：[{"name": "科技", "count": 85, "events": 12}, ...]
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()

        await cursor.execute(
            """
            SELECT
                category,
                COUNT(*) as count,
                COUNT(DISTINCT event_name) as events
            FROM news
            WHERE session_id = ?
            GROUP BY category
            ORDER BY count DESC
        """,
            (session_id,),
        )

        rows = await cursor.fetchall()
        return [
            {"name": row[0], "count": row[1], "events": row[2]} for row in rows
        ]

    async def get_events_by_category(
        self, session_id: str, category: str, limit: int = 20
    ) -> List[dict]:
        """获取类别下的事件列表

        Args:
            session_id: 会话ID
            category: 类别名称
            limit: 最大返回数量

        Returns:
            事件列表
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()

        await cursor.execute(
            """
            SELECT
                event_name,
                COUNT(*) as news_count,
                MAX(publish_time) as latest_time,
                GROUP_CONCAT(DISTINCT source) as sources
            FROM news
            WHERE session_id = ? AND category = ?
            GROUP BY event_name
            ORDER BY latest_time DESC
            LIMIT ?
        """,
            (session_id, category, limit),
        )

        rows = await cursor.fetchall()
        return [
            {
                "event_name": row[0],
                "news_count": row[1],
                "latest_time": row[2],
                "sources": (row[3] or "").split(",") if row[3] else [],
            }
            for row in rows
        ]

    async def get_news_titles_by_event(
        self, session_id: str, event_name: str, limit: int = 50
    ) -> List[dict]:
        """获取事件下的新闻标题列表（轻量级）

        Args:
            session_id: 会话ID
            event_name: 事件名称
            limit: 最大返回数量

        Returns:
            新闻列表（轻量级，包含图片URL）
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()

        await cursor.execute(
            """
            SELECT
                title, url, summary, source, publish_time, author, image_urls
            FROM news
            WHERE session_id = ? AND event_name = ?
            ORDER BY publish_time DESC
            LIMIT ?
        """,
            (session_id, event_name, limit),
        )

        rows = await cursor.fetchall()
        return [
            {
                "title": row[0],
                "url": row[1],
                "summary": row[2] or "",
                "source": row[3] or "",
                "publish_time": row[4] or "",
                "author": row[5] or "",
                "image_urls": json.loads(row[6]) if row[6] else [],
            }
            for row in rows
        ]

    async def get_images_by_event(
        self, session_id: str, event_name: str
    ) -> List[dict]:
        """获取事件下所有新闻的图片URL

        Args:
            session_id: 会话ID
            event_name: 事件名称

        Returns:
            图片列表：[{url, source_news_title, source_news_url}, ...]
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()

        await cursor.execute(
            """
            SELECT
                title, url, image_urls
            FROM news
            WHERE session_id = ? AND event_name = ? AND image_urls IS NOT NULL AND image_urls != '[]'
        """,
            (session_id, event_name),
        )

        rows = await cursor.fetchall()
        images = []

        for row in rows:
            title, url, image_urls_json = row
            if image_urls_json:
                image_urls = json.loads(image_urls_json)
                for img_url in image_urls:
                    images.append(
                        {
                            "url": img_url,
                            "source_news_title": title,
                            "source_news_url": url,
                        }
                    )

        return images

    async def close(self):
        """关闭数据库连接"""
        if self.conn:
            await self.conn.close()
            self.conn = None
            self._initialized = False
            logger.info("🔒 数据库连接已关闭")

    async def __aenter__(self):
        """异步上下文管理器支持"""
        await self._ensure_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器支持"""
        await self.close()


# 全局数据库实例
_db_instance: Optional[NewsDatabase] = None


async def get_database(db_path: str = "./data/news_storage.db") -> NewsDatabase:
    """获取数据库实例（单例模式）

    Args:
        db_path: 数据库路径

    Returns:
        数据库实例
    """
    global _db_instance

    if _db_instance is None:
        _db_instance = NewsDatabase(db_path)
        await _db_instance._ensure_connection()

    return _db_instance
