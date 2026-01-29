"""
数据库管理器 - SQLite
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from loguru import logger

from .models import NewsItem, SearchFilter


class NewsDatabase:
    """新闻数据库管理器"""

    def __init__(self, db_path: str = "./data/news_storage.db"):
        """初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()

        logger.info(f"✅ NewsDatabase 初始化完成: {self.db_path}")

    def _connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(
            self.db_path, check_same_thread=False, timeout=30
        )
        self.conn.row_factory = sqlite3.Row  # 支持字典式访问

    def _create_tables(self):
        """创建数据表"""
        cursor = self.conn.cursor()

        # 主表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                summary TEXT,
                source TEXT,
                publish_time TEXT,
                author TEXT,
                event_name TEXT,
                content TEXT,
                html_content TEXT,
                keywords TEXT,
                images TEXT,
                local_images TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 创建索引
        cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_url ON news(url)"""
        )
        cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_source ON news(source)"""
        )
        cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_created_at ON news(created_at)"""
        )
        cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_publish_time ON news(publish_time)"""
        )
        cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_news_event_name ON news(event_name)"""
        )

        # 为旧数据库添加 event_name 字段（如果不存在）
        try:
            cursor.execute("ALTER TABLE news ADD COLUMN event_name TEXT")
            logger.debug("📊 已为旧数据库添加 event_name 字段")
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass

        # 为旧数据库添加 local_images 字段（如果不存在）
        try:
            cursor.execute("ALTER TABLE news ADD COLUMN local_images TEXT")
            logger.debug("📊 已为旧数据库添加 local_images 字段")
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass

        self.conn.commit()
        logger.debug("📊 数据表创建完成")

    def save_news(self, news: NewsItem) -> bool:
        """保存单条新闻（自动去重）

        Args:
            news: 新闻对象

        Returns:
            是否插入新记录（False表示更新已存在记录）
        """
        cursor = self.conn.cursor()

        try:
            # 检查是否已存在
            cursor.execute("SELECT id FROM news WHERE url = ?", (news.url,))
            existing = cursor.fetchone()

            news_dict = news.to_dict()

            if existing:
                # 更新
                cursor.execute(
                    """
                    UPDATE news
                    SET title = ?, summary = ?, source = ?, publish_time = ?,
                        author = ?, event_name = ?, content = ?, html_content = ?,
                        keywords = ?, images = ?, local_images = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE url = ?
                    """,
                    (
                        news_dict["title"],
                        news_dict["summary"],
                        news_dict["source"],
                        news_dict["publish_time"],
                        news_dict["author"],
                        news_dict["event_name"],
                        news_dict["content"],
                        news_dict["html_content"],
                        news_dict["keywords"],
                        news_dict["images"],
                        news_dict["local_images"],
                        news_dict["tags"],
                        news.url,
                    ),
                )
                logger.debug(f"📝 更新新闻: {news.title[:50]}")
                self.conn.commit()
                return False
            else:
                # 插入
                cursor.execute(
                    """
                    INSERT INTO news (
                        title, url, summary, source, publish_time, author, event_name,
                        content, html_content, keywords, images, local_images, tags, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        news_dict["images"],
                        news_dict["local_images"],
                        news_dict["tags"],
                        news_dict["created_at"],
                        news_dict["updated_at"],
                    ),
                )
                logger.debug(f"✅ 新增新闻: {news.title[:50]}")
                self.conn.commit()
                return True

        except sqlite3.Error as e:
            logger.error(f"❌ 保存新闻失败: {e}")
            self.conn.rollback()
            raise

    def save_news_batch(self, news_list: List[NewsItem]) -> dict:
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
                if self.save_news(news):
                    added += 1
                else:
                    updated += 1
            except Exception as e:
                logger.error(f"❌ 保存新闻失败: {news.url[:50]}, 错误: {e}")
                failed += 1

        result = {"added": added, "updated": updated, "failed": failed}
        logger.info(f"📊 批量保存完成: {result}")
        return result

    def get_news_by_url(self, url: str) -> Optional[NewsItem]:
        """根据URL获取新闻

        Args:
            url: 新闻URL

        Returns:
            新闻对象，不存在则返回None
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, title, url, summary, source, publish_time, author, event_name,
                   content, html_content, keywords, images, local_images, tags, created_at, updated_at
            FROM news WHERE url = ?
            """,
            (url,),
        )

        row = cursor.fetchone()
        if row:
            return NewsItem.from_db_row(row)
        return None

    def search_news(self, filter: SearchFilter) -> List[NewsItem]:
        """搜索新闻

        Args:
            filter: 搜索过滤器

        Returns:
            新闻列表
        """
        cursor = self.conn.cursor()

        # 构建SQL查询
        conditions = []
        params = []

        # 智能搜索：每个词在所有字段中独立搜索（OR关系）
        if filter.search_terms:
            # 为每个搜索词构建条件：(标题 OR 摘要 OR keywords字段 OR 内容)
            term_conditions = []
            for term in filter.search_terms:
                term_pattern = f"%{term}%"
                # 每个词在4个字段中搜索
                term_conditions.append(f"""(
                    title LIKE ? OR
                    summary LIKE ? OR
                    keywords LIKE ? OR
                    content LIKE ?
                )""")
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
                   content, html_content, keywords, images, local_images, tags, created_at, updated_at
            FROM news
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """

        params.extend([filter.limit, filter.offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [NewsItem.from_db_row(row) for row in rows]

    def get_recent_news(
        self, limit: int = 100, offset: int = 0
    ) -> List[NewsItem]:
        """获取最近添加的新闻

        Args:
            limit: 返回数量
            offset: 偏移量

        Returns:
            新闻列表
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, title, url, summary, source, publish_time, author, event_name,
                   content, html_content, keywords, images, local_images, tags, created_at, updated_at
            FROM news
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )

        rows = cursor.fetchall()
        return [NewsItem.from_db_row(row) for row in rows]

    def update_news_content(self, url: str, content: str, html_content: str = "") -> bool:
        """更新新闻内容

        Args:
            url: 新闻URL
            content: 纯文本内容
            html_content: HTML内容（可选）

        Returns:
            是否成功
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE news
            SET content = ?, html_content = ?, updated_at = CURRENT_TIMESTAMP
            WHERE url = ?
            """,
            (content, html_content, url),
        )

        self.conn.commit()
        success = cursor.rowcount > 0

        if success:
            logger.debug(f"📝 更新内容: {url[:50]}")
        else:
            logger.warning(f"⚠️ 未找到新闻: {url[:50]}")

        return success

    def update_event_name(self, url: str, event_name: str) -> bool:
        """更新新闻的事件名称

        Args:
            url: 新闻URL
            event_name: 事件名称

        Returns:
            是否成功
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE news
            SET event_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE url = ?
            """,
            (event_name, url),
        )

        self.conn.commit()
        success = cursor.rowcount > 0

        if success:
            logger.debug(f"📝 更新事件名称: {url[:50]} -> {event_name}")
        else:
            logger.warning(f"⚠️ 未找到新闻: {url[:50]}")

        return success

    def batch_update_event_name(self, urls: List[str], event_name: str) -> dict:
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
            if self.update_event_name(url, event_name):
                updated += 1
            else:
                failed += 1

        result = {"updated": updated, "failed": failed}
        logger.info(f"📊 批量更新事件名称完成: {result}")
        return result

    def delete_news(self, url: str) -> bool:
        """删除新闻

        Args:
            url: 新闻URL

        Returns:
            是否成功
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM news WHERE url = ?", (url,))

        self.conn.commit()
        success = cursor.rowcount > 0

        if success:
            logger.debug(f"🗑️ 删除新闻: {url[:50]}")
        else:
            logger.warning(f"⚠️ 未找到新闻: {url[:50]}")

        return success

    def get_stats(self) -> dict:
        """获取统计信息

        Returns:
            统计数据
        """
        cursor = self.conn.cursor()

        # 总数
        cursor.execute("SELECT COUNT(*) FROM news")
        total = cursor.fetchone()[0]

        # 按来源统计
        cursor.execute(
            """
            SELECT source, COUNT(*) as count
            FROM news
            GROUP BY source
            ORDER BY count DESC
            LIMIT 10
        """
        )
        by_source = {row[0]: row[1] for row in cursor.fetchall()}

        # 最近7天添加数量
        cursor.execute(
            """
            SELECT COUNT(*) FROM news
            WHERE created_at >= datetime('now', '-7 days')
        """
        )
        recent_week = cursor.fetchone()[0]

        return {
            "total": total,
            "by_source": by_source,
            "recent_week": recent_week,
            "db_path": str(self.db_path),
        }

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("🔒 数据库连接已关闭")

    def __enter__(self):
        """上下文管理器支持"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器支持"""
        self.close()


# 全局数据库实例
_db_instance: Optional[NewsDatabase] = None


def get_database(db_path: str = "./data/news_storage.db") -> NewsDatabase:
    """获取数据库实例（单例模式）

    Args:
        db_path: 数据库路径

    Returns:
        数据库实例
    """
    global _db_instance

    if _db_instance is None:
        _db_instance = NewsDatabase(db_path)

    return _db_instance
