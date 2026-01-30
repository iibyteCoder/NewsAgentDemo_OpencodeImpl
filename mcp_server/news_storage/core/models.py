"""
数据库模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json


@dataclass
class NewsItem:
    """新闻数据模型"""

    title: str  # 标题
    url: str  # URL（唯一标识）

    # 基本信息
    summary: str = ""  # 摘要
    source: str = ""  # 来源
    publish_time: str = ""  # 发布时间（原始字符串）
    author: str = ""  # 作者
    event_name: str = ""  # 事件名称

    # 会话和分类
    session_id: str = ""  # 会话ID
    category: str = ""  # 类别（科技/体育/财经/...）

    # 内容
    content: str = ""  # 完整内容（纯文本）
    html_content: str = ""  # HTML内容（原文）

    # 扩展信息
    keywords: List[str] = field(default_factory=list)  # 关键词列表
    image_urls: List[str] = field(default_factory=list)  # 网络图片URL列表（未下载）
    local_image_paths: List[str] = field(default_factory=list)  # 本地图片文件路径列表（已下载）
    tags: List[str] = field(default_factory=list)  # 标签

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
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
            "keywords": json.dumps(self.keywords, ensure_ascii=False),
            "image_urls": json.dumps(self.image_urls, ensure_ascii=False),
            "local_image_paths": json.dumps(self.local_image_paths, ensure_ascii=False),
            "tags": json.dumps(self.tags, ensure_ascii=False),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NewsItem":
        """从字典创建实例"""
        return cls(
            title=data.get("title", ""),
            url=data.get("url", ""),
            summary=data.get("summary", ""),
            source=data.get("source", ""),
            publish_time=data.get("publish_time", ""),
            author=data.get("author", ""),
            event_name=data.get("event_name", ""),
            session_id=data.get("session_id", ""),
            category=data.get("category", ""),
            content=data.get("content", ""),
            html_content=data.get("html_content", ""),
            keywords=json.loads(data.get("keywords", "[]")),
            image_urls=json.loads(data.get("image_urls", "[]")),
            local_image_paths=json.loads(data.get("local_image_paths", "[]")),
            tags=json.loads(data.get("tags", "[]")),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )

    @classmethod
    def from_db_row(cls, row: tuple) -> "NewsItem":
        """从数据库行创建实例"""
        (
            id_,
            title,
            url,
            summary,
            source,
            publish_time,
            author,
            event_name,
            content,
            html_content,
            keywords,
            image_urls,
            local_image_paths,
            tags,
            session_id,
            category,
            created_at,
            updated_at,
        ) = row

        return cls(
            title=title,
            url=url,
            summary=summary or "",
            source=source or "",
            publish_time=publish_time or "",
            author=author or "",
            event_name=event_name or "",
            session_id=session_id or "",
            category=category or "",
            content=content or "",
            html_content=html_content or "",
            keywords=json.loads(keywords) if keywords else [],
            image_urls=json.loads(image_urls) if image_urls else [],
            local_image_paths=json.loads(local_image_paths) if local_image_paths else [],
            tags=json.loads(tags) if tags else [],
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class SearchFilter:
    """搜索过滤器

    搜索逻辑：
    - search_terms: 每个词独立搜索（标题 OR 摘要 OR keywords字段 OR 内容）
    - 多个词之间是 OR 关系（匹配任意一个即可）
    - 所有字段都用模糊匹配（LIKE）
    """

    # 会话和类别过滤（必填）
    session_id: str = ""  # 会话ID
    category: str = ""  # 类别筛选（可选）

    # 原有字段
    search_terms: Optional[List[str]] = None  # 搜索词列表（自动分词）
    source: Optional[str] = None  # 来源筛选
    event_name: Optional[str] = None  # 事件名称筛选
    start_date: Optional[str] = None  # 开始日期
    end_date: Optional[str] = None  # 结束日期
    tags: Optional[List[str]] = None  # 标签筛选
    limit: int = 100  # 返回数量限制
    offset: int = 0  # 偏移量
