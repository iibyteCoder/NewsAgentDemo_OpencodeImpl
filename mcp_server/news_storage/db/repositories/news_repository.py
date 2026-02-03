"""
新闻数据访问层 - Repository 模式

封装所有与 NewsItem 相关的数据库操作
"""

from datetime import datetime, timedelta
from typing import Any

from loguru import logger
from sqlalchemy import and_, func, or_, select

from ..models.news import NewsItem
from ..session import DatabaseManager


class NewsRepository:
    """新闻数据访问层"""

    def __init__(self, db_manager: DatabaseManager):
        """初始化仓储

        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager

    async def save(
        self,
        title: str,
        url: str,
        session_id: str,
        category: str,
        summary: str | None = None,
        source: str | None = None,
        publish_time: str | None = None,
        author: str | None = None,
        event_name: str | None = None,
        content: str | None = None,
        html_content: str | None = None,
        keywords: dict | None = None,
        image_urls: dict | None = None,
        local_image_paths: dict | None = None,
        tags: dict | None = None,
    ) -> bool:
        """保存单条新闻（基于 URL 唯一，已存在则更新）

        Args:
            title: 标题
            url: URL（唯一标识）
            session_id: 会话ID
            category: 类别
            summary: 摘要
            source: 来源
            publish_time: 发布时间
            author: 作者
            event_name: 事件名称
            content: 纯文本内容
            html_content: HTML内容
            keywords: 关键词字典
            image_urls: 图片URL字典
            local_image_paths: 本地图片路径字典
            tags: 标签字典

        Returns:
            是否是新插入的记录
        """
        async with self.db_manager.session() as session:
            # 尝试查找已存在的记录
            existing = await session.execute(
                select(NewsItem).where(NewsItem.url == url)
            )
            existing_news = existing.scalar_one_or_none()

            if existing_news:
                # 更新已存在的记录
                existing_news.title = title
                existing_news.summary = summary
                existing_news.source = source
                existing_news.publish_time = publish_time
                existing_news.author = author
                existing_news.event_name = event_name
                existing_news.session_id = session_id
                existing_news.category = category
                existing_news.content = content
                existing_news.html_content = html_content
                existing_news.keywords = keywords or {}
                existing_news.image_urls = image_urls or {}
                existing_news.local_image_paths = local_image_paths or {}
                existing_news.tags = tags or {}

                logger.debug(f"📝 Updated news: {title[:50]}")
                return False
            else:
                # 创建新记录
                news = NewsItem(
                    title=title,
                    url=url,
                    session_id=session_id,
                    category=category,
                    summary=summary,
                    source=source,
                    publish_time=publish_time,
                    author=author,
                    event_name=event_name,
                    content=content,
                    html_content=html_content,
                    keywords=keywords or {},
                    image_urls=image_urls or {},
                    local_image_paths=local_image_paths or {},
                    tags=tags or {},
                )
                session.add(news)
                logger.debug(f"✅ Inserted news: {title[:50]}")
                return True

    async def save_batch(self, news_list: list[dict[str, Any]]) -> dict[str, int]:
        """批量保存新闻

        Args:
            news_list: 新闻字典列表

        Returns:
            统计结果 {"added": 数量, "updated": 数量, "failed": 数量}
        """
        added = 0
        updated = 0
        failed = 0

        async with self.db_manager.session() as session:
            try:
                for item in news_list:
                    url = item.get("url")
                    if not url:
                        failed += 1
                        continue

                    # 检查是否已存在
                    existing = await session.execute(
                        select(NewsItem).where(NewsItem.url == url)
                    )
                    existing_news = existing.scalar_one_or_none()

                    if existing_news:
                        # 更新
                        for key, value in item.items():
                            if key != "id" and hasattr(existing_news, key):
                                setattr(existing_news, key, value)
                        updated += 1
                    else:
                        # 插入
                        news = NewsItem(**item)
                        session.add(news)
                        added += 1

                await session.commit()
                logger.info(f"📊 Batch save completed: added={added}, updated={updated}")

            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Batch save failed: {e}")
                failed = len(news_list)
                added = updated = 0

        return {"added": added, "updated": updated, "failed": failed}

    async def get_by_url(
        self, url: str, session_id: str = "", category: str = ""
    ) -> NewsItem | None:
        """根据 URL 获取新闻

        Args:
            url: 新闻 URL
            session_id: 会话ID（可选，用于精确查询）
            category: 类别（可选，用于精确查询）

        Returns:
            NewsItem 对象，不存在则返回 None
        """
        async with self.db_manager.session() as session:
            stmt = select(NewsItem).where(NewsItem.url == url)

            if session_id and category:
                stmt = stmt.where(
                    NewsItem.session_id == session_id, NewsItem.category == category
                )

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def search(
        self,
        session_id: str,
        search_terms: list[str] | None = None,
        category: str = "",
        source: str | None = None,
        event_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[NewsItem]:
        """搜索新闻

        Args:
            session_id: 会话ID（必填）
            search_terms: 搜索词列表
            category: 类别
            source: 来源
            event_name: 事件名称
            start_date: 开始日期
            end_date: 结束日期
            tags: 标签列表
            limit: 返回数量
            offset: 偏移量

        Returns:
            NewsItem 列表
        """
        async with self.db_manager.session() as session:
            stmt = select(NewsItem)

            # 构建条件
            conditions = []

            # 会话过滤
            if not session_id:
                logger.warning("⚠️ 搜索时未提供 session_id，可能返回所有数据")
            else:
                conditions.append(NewsItem.session_id == session_id)

            # 类别过滤
            if category:
                conditions.append(NewsItem.category == category)

            # 搜索词过滤（OR 关系）
            if search_terms:
                term_conditions = []
                for term in search_terms:
                    pattern = f"%{term}%"
                    term_conditions.append(
                        or_(
                            NewsItem.title.like(pattern),
                            NewsItem.summary.like(pattern),
                            NewsItem.content.like(pattern),
                        )
                    )
                if term_conditions:
                    conditions.append(or_(*term_conditions))

            # 来源过滤
            if source:
                conditions.append(NewsItem.source == source)

            # 事件名称过滤
            if event_name:
                conditions.append(NewsItem.event_name == event_name)

            # 日期范围过滤
            if start_date:
                conditions.append(NewsItem.created_at >= start_date)
            if end_date:
                conditions.append(NewsItem.created_at <= end_date)

            # 应用所有条件
            if conditions:
                stmt = stmt.where(and_(*conditions))

            # 标签过滤（JSON 查询）
            # 注意：这里简化处理，实际应用中可能需要更复杂的 JSON 查询

            # 排序和分页
            stmt = stmt.order_by(NewsItem.created_at.desc()).limit(limit).offset(offset)

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_recent(
        self, limit: int = 100, offset: int = 0, session_id: str = ""
    ) -> list[NewsItem]:
        """获取最近添加的新闻

        Args:
            limit: 返回数量
            offset: 偏移量
            session_id: 会话ID（可选）

        Returns:
            NewsItem 列表
        """
        async with self.db_manager.session() as session:
            stmt = select(NewsItem).order_by(NewsItem.created_at.desc())

            if session_id:
                stmt = stmt.where(NewsItem.session_id == session_id)

            stmt = stmt.limit(limit).offset(offset)

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_content(
        self, url: str, content: str, html_content: str = ""
    ) -> bool:
        """更新新闻内容

        Args:
            url: 新闻 URL
            content: 纯文本内容
            html_content: HTML 内容

        Returns:
            是否成功
        """
        async with self.db_manager.session() as session:
            result = await session.execute(select(NewsItem).where(NewsItem.url == url))
            news = result.scalar_one_or_none()

            if news:
                news.content = content
                news.html_content = html_content
                logger.debug(f"📝 Updated content: {url[:50]}")
                return True

            logger.warning(f"⚠️ News not found: {url[:50]}")
            return False

    async def update_event_name(self, url: str, event_name: str) -> bool:
        """更新新闻的事件名称

        Args:
            url: 新闻 URL
            event_name: 事件名称

        Returns:
            是否成功
        """
        async with self.db_manager.session() as session:
            result = await session.execute(select(NewsItem).where(NewsItem.url == url))
            news = result.scalar_one_or_none()

            if news:
                news.event_name = event_name
                logger.debug(f"📝 Updated event_name: {url[:50]} -> {event_name}")
                return True

            logger.warning(f"⚠️ News not found: {url[:50]}")
            return False

    async def batch_update_event_name(self, urls: list[str], event_name: str) -> dict:
        """批量更新新闻的事件名称

        Args:
            urls: 新闻 URL 列表
            event_name: 事件名称

        Returns:
            统计结果 {"updated": 数量, "failed": 数量}
        """
        async with self.db_manager.session() as session:
            try:
                # 批量查询
                result = await session.execute(
                    select(NewsItem).where(NewsItem.url.in_(urls))
                )
                news_list = result.scalars().all()

                # 批量更新
                for news in news_list:
                    news.event_name = event_name

                updated = len(news_list)
                failed = len(urls) - updated

                logger.info(
                    f"📊 Batch update event_name completed: updated={updated}, failed={failed}"
                )
                return {"updated": updated, "failed": failed}

            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Batch update failed: {e}")
                return {"updated": 0, "failed": len(urls)}

    async def delete(self, url: str) -> bool:
        """删除新闻

        Args:
            url: 新闻 URL

        Returns:
            是否成功
        """
        async with self.db_manager.session() as session:
            result = await session.execute(select(NewsItem).where(NewsItem.url == url))
            news = result.scalar_one_or_none()

            if news:
                await session.delete(news)
                logger.debug(f"🗑️ Deleted news: {url[:50]}")
                return True

            logger.warning(f"⚠️ News not found: {url[:50]}")
            return False

    async def get_stats(self, session_id: str = "") -> dict[str, Any]:
        """获取统计信息

        Args:
            session_id: 会话ID（可选）

        Returns:
            统计数据
        """
        async with self.db_manager.session() as session:
            # 总数
            if session_id:
                total_stmt = select(func.count(NewsItem.id)).where(
                    NewsItem.session_id == session_id
                )
            else:
                total_stmt = select(func.count(NewsItem.id))

            total_result = await session.execute(total_stmt)
            total = total_result.scalar() or 0

            # 按来源统计
            if session_id:
                source_stmt = (
                    select(NewsItem.source, func.count(NewsItem.id))
                    .where(NewsItem.session_id == session_id)
                    .group_by(NewsItem.source)
                    .order_by(func.count(NewsItem.id).desc())
                    .limit(10)
                )
            else:
                source_stmt = (
                    select(NewsItem.source, func.count(NewsItem.id))
                    .group_by(NewsItem.source)
                    .order_by(func.count(NewsItem.id).desc())
                    .limit(10)
                )

            source_result = await session.execute(source_stmt)
            by_source = {row[0]: row[1] for row in source_result.all()}

            # 最近7天添加数量
            week_ago = datetime.now() - timedelta(days=7)

            if session_id:
                recent_stmt = select(func.count(NewsItem.id)).where(
                    NewsItem.session_id == session_id, NewsItem.created_at >= week_ago
                )
            else:
                recent_stmt = select(func.count(NewsItem.id)).where(
                    NewsItem.created_at >= week_ago
                )

            recent_result = await session.execute(recent_stmt)
            recent_week = recent_result.scalar() or 0

            return {
                "total": total,
                "by_source": by_source,
                "recent_week": recent_week,
            }

    async def get_categories(self, session_id: str) -> list[dict[str, Any]]:
        """获取会话中的所有类别及统计

        Args:
            session_id: 会话ID

        Returns:
            类别列表：[{"name": "科技", "count": 85, "events": 12}, ...]
        """
        async with self.db_manager.session() as session:
            stmt = (
                select(
                    NewsItem.category,
                    func.count(NewsItem.id).label("count"),
                    func.count(func.distinct(NewsItem.event_name)).label("events"),
                )
                .where(NewsItem.session_id == session_id)
                .group_by(NewsItem.category)
                .order_by(func.count(NewsItem.id).desc())
            )

            result = await session.execute(stmt)
            return [
                {"name": row.category, "count": row.count, "events": row.events}
                for row in result.all()
            ]

    async def get_events_by_category(
        self, session_id: str, category: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """获取类别下的事件列表

        Args:
            session_id: 会话ID
            category: 类别名称
            limit: 最大返回数量

        Returns:
            事件列表
        """
        async with self.db_manager.session() as session:
            stmt = (
                select(
                    NewsItem.event_name,
                    func.count(NewsItem.id).label("news_count"),
                    func.max(NewsItem.publish_time).label("latest_time"),
                )
                .where(NewsItem.session_id == session_id, NewsItem.category == category)
                .group_by(NewsItem.event_name)
                .order_by(func.max(NewsItem.publish_time).desc())
                .limit(limit)
            )

            result = await session.execute(stmt)
            return [
                {
                    "event_name": row.event_name or "",
                    "news_count": row.news_count,
                    "latest_time": row.latest_time or "",
                }
                for row in result.all()
            ]

    async def get_news_by_event(
        self, session_id: str, event_name: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """获取事件下的新闻（轻量级）

        Args:
            session_id: 会话ID
            event_name: 事件名称
            limit: 最大返回数量

        Returns:
            新闻列表（轻量级）
        """
        async with self.db_manager.session() as session:
            stmt = (
                select(
                    NewsItem.title,
                    NewsItem.url,
                    NewsItem.summary,
                    NewsItem.source,
                    NewsItem.publish_time,
                    NewsItem.author,
                    NewsItem.image_urls,
                )
                .where(NewsItem.session_id == session_id, NewsItem.event_name == event_name)
                .order_by(NewsItem.publish_time.desc())
                .limit(limit)
            )

            result = await session.execute(stmt)
            return [
                {
                    "title": row.title,
                    "url": row.url,
                    "summary": row.summary or "",
                    "source": row.source or "",
                    "publish_time": row.publish_time or "",
                    "author": row.author or "",
                    "image_urls": row.image_urls or {},
                }
                for row in result.all()
            ]

    async def get_images_by_event(
        self, session_id: str, event_name: str
    ) -> list[dict[str, str]]:
        """获取事件下所有新闻的图片URL

        Args:
            session_id: 会话ID
            event_name: 事件名称

        Returns:
            图片列表：[{url, source_news_title, source_news_url}, ...]
        """
        async with self.db_manager.session() as session:
            stmt = select(NewsItem.title, NewsItem.url, NewsItem.image_urls).where(
                NewsItem.session_id == session_id,
                NewsItem.event_name == event_name,
                NewsItem.image_urls != {},
            )

            result = await session.execute(stmt)
            images = []

            for row in result.all():
                for img_url in (row.image_urls or {}).values():
                    if img_url:
                        images.append(
                            {
                                "url": img_url,
                                "source_news_title": row.title,
                                "source_news_url": row.url,
                            }
                        )

            return images
