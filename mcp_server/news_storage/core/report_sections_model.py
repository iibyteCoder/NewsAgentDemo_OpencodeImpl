"""
报告部分数据模型

用于存储各个环节生成的用于最终报告的数据，
避免上下文过长导致的信息丢失问题。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json


@dataclass
class ReportSection:
    """报告部分数据模型

    存储单个报告部分的完整数据，支持：
    - 验证结果（validation）
    - 时间轴（timeline）
    - 预测（prediction）
    - 摘要（summary）
    - 新闻列表（news）
    """

    # 基本信息
    section_id: str  # 部分唯一标识（格式：{session_id}_{event_name}_{section_type}）
    section_type: str  # 部分类型：validation/timeline/prediction/summary/news

    # 关联信息
    session_id: str  # 会话ID
    event_name: str  # 事件名称
    category: str  # 类别

    # 内容数据（JSON格式，存储该部分的完整数据）
    content_data: str  # JSON字符串，包含该部分的所有数据

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 生成状态
    status: str = "pending"  # pending/completed/failed
    error_message: str = ""  # 如果失败，记录错误信息

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "section_id": self.section_id,
            "section_type": self.section_type,
            "session_id": self.session_id,
            "event_name": self.event_name,
            "category": self.category,
            "content_data": self.content_data,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReportSection":
        """从字典创建实例"""
        return cls(
            section_id=data.get("section_id", ""),
            section_type=data.get("section_type", ""),
            session_id=data.get("session_id", ""),
            event_name=data.get("event_name", ""),
            category=data.get("category", ""),
            content_data=data.get("content_data", "{}"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            status=data.get("status", "pending"),
            error_message=data.get("error_message", ""),
        )

    def get_content(self) -> dict:
        """获取内容数据（解析JSON）"""
        try:
            return json.loads(self.content_data)
        except Exception:
            return {}

    def set_content(self, content: dict):
        """设置内容数据（转换为JSON）"""
        self.content_data = json.dumps(content, ensure_ascii=False, indent=2)
        self.updated_at = datetime.now().isoformat()


# 部分类型常量
SECTION_VALIDATION = "validation"
SECTION_TIMELINE = "timeline"
SECTION_PREDICTION = "prediction"
SECTION_SUMMARY = "summary"
SECTION_NEWS = "news"
SECTION_IMAGES = "images"


# 预定义的内容结构模板
class ContentTemplates:
    """各部分的内容数据模板"""

    @staticmethod
    def validation_template() -> dict:
        """验证结果模板"""
        return {
            "credibility_score": 0,  # 可信度评分 0-100
            "confidence_level": "",  # 置信度：高/中/低
            "evidence_chain": [],  # 证据链
            # [
            #     {
            #         "step": int,  # 步骤
            #         "description": str,  # 描述
            #         "source_url": str,  # 来源链接
            #         "reliable": bool,  # 是否可靠
            #     }
            # ]
            "analysis": "",  # 综合分析
            "sources": [],  # 所有来源链接
        }

    @staticmethod
    def timeline_template() -> dict:
        """时间轴模板"""
        return {
            "milestones": [],  # 里程碑
            # [
            #     {
            #         "date": str,  # 日期
            #         "event": str,  # 事件描述
            #         "importance": str,  # 重要性：高/中/低
            #         "source_url": str,  # 来源链接
            #     }
            # ]
            "development_path": "",  # 发展脉络描述
            "causal_relationships": [],  # 因果关系
        }

    @staticmethod
    def prediction_template() -> dict:
        """预测模板"""
        return {
            "scenarios": [],  # 可能情景
            # [
            #     {
            #         "scenario": str,  # 情景描述
            #         "probability": str,  # 概率
            #         "evidence": [],  # 支撑证据
            #         "timeframe": str,  # 时间范围
            #     }
            # ]
            "key_factors": [],  # 关键因素
            "conclusion": "",  # 结论
            "sources": [],  # 所有来源链接
        }

    @staticmethod
    def summary_template() -> dict:
        """摘要模板"""
        return {
            "summary": "",  # 事件摘要（2-3句话）
            "key_points": [],  # 关键点
            "importance": "",  # 重要性说明
        }

    @staticmethod
    def news_template() -> dict:
        """新闻列表模板"""
        return {
            "today_news": [],  # 今日新闻
            # [
            #     {
            #         "title": str,
            #         "url": str,
            #         "source": str,
            #         "publish_time": str,
            #         "summary": str,
            #     }
            # ]
            "related_news": [],  # 相关新闻
        }

    @staticmethod
    def images_template() -> dict:
        """图片模板"""
        return {
            "images": [],  # 图片列表
            # [
            #     {
            #         "local_path": str,  # 本地路径
            #         "caption": str,  # 说明
            #         "source_url": str,  # 来源URL
            #     }
            # ]
        }
