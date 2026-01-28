"""辅助函数"""

import random
from dataclasses import asdict

from ..config.settings import get_settings


def get_random_user_agent() -> str:
    """获取随机 User-Agent"""
    settings = get_settings()
    return random.choice(settings.user_agents)


def search_result_to_dict(result) -> dict:
    """将 SearchResult 转换为字典"""
    if hasattr(result, 'to_dict'):
        return result.to_dict()
    elif hasattr(result, '__dataclass_fields__'):
        return asdict(result)
    else:
        return {
            "title": getattr(result, 'title', ''),
            "url": getattr(result, 'url', ''),
            "summary": getattr(result, 'summary', ''),
            "source": getattr(result, 'source', ''),
            "time": getattr(result, 'time', ''),
        }
