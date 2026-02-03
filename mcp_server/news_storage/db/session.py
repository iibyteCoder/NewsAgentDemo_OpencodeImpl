"""
会话管理 - SQLAlchemy 2.0 异步会话

使用依赖注入模式，避免全局单例
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .base import Base


class DatabaseManager:
    """数据库管理器 - 负责引擎和会话工厂"""

    def __init__(self, db_path: str | Path = "./data/news_storage.db"):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建异步引擎
        sqlite_url = f"sqlite+aiosqlite:///{self.db_path}"
        self.engine = create_async_engine(
            sqlite_url,
            echo=False,
            pool_pre_ping=True,
        )

        # 创建会话工厂
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self._initialized = False

    async def init_db(self) -> None:
        """初始化数据库 - 创建表"""
        if self._initialized:
            return

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self._initialized = True
        logger.info(f"✅ Database initialized: {self.db_path}")

    async def close(self) -> None:
        """关闭数据库连接"""
        await self.engine.dispose()
        self._initialized = False
        logger.info("🔒 Database connection closed")

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """获取会话的上下文管理器

        Usage:
            async with db_manager.session() as session:
                # 使用 session
        """
        if not self._initialized:
            await self.init_db()

        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# 默认数据库实例（用于向后兼容）
_default_manager: DatabaseManager | None = None


def get_db_manager(db_path: str | Path = "./data/news_storage.db") -> DatabaseManager:
    """获取数据库管理器实例（单例）

    Args:
        db_path: 数据库路径

    Returns:
        DatabaseManager 实例
    """
    global _default_manager

    if _default_manager is None or str(_default_manager.db_path) != str(db_path):
        _default_manager = DatabaseManager(db_path)

    return _default_manager
