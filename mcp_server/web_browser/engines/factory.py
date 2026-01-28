"""搜索引擎工厂 - 管理和创建搜索引擎实例"""

import random
from typing import Dict, List, Optional

from loguru import logger

from .base import BaseEngine
from .baidu import BaiduEngine
from .bing import BingEngine
from .sogou import SogouEngine
from .google import GoogleEngine
from .engine_360 import Engine360


class EngineFactory:
    """搜索引擎工厂"""

    # 所有可用的搜索引擎类
    _ENGINE_CLASSES = {
        "baidu": BaiduEngine,
        "bing": BingEngine,
        "sogou": SogouEngine,
        "google": GoogleEngine,
        "360": Engine360,
    }

    # 引擎速度优先级（根据测试数据）
    _SPEED_PRIORITY = ["baidu", "sogou", "google", "360", "bing"]

    def __init__(self, enabled_engines: List[str] = None):
        """初始化引擎工厂

        Args:
            enabled_engines: 启用的引擎列表
        """
        self.enabled_engines = enabled_engines or list(self._ENGINE_CLASSES.keys())
        self._engines: Dict[str, BaseEngine] = {}

    def get_engine(self, engine_id: str) -> Optional[BaseEngine]:
        """获取指定引擎实例

        Args:
            engine_id: 引擎ID

        Returns:
            引擎实例，如果不存在或未启用则返回 None
        """
        if engine_id not in self.enabled_engines:
            logger.warning(f"❌ 引擎 {engine_id} 未启用")
            return None

        if engine_id not in self._engines:
            engine_class = self._ENGINE_CLASSES.get(engine_id)
            if engine_class:
                self._engines[engine_id] = engine_class()
                logger.info(f"✅ 创建 {engine_id} 引擎实例")
            else:
                logger.error(f"❌ 未知的引擎: {engine_id}")
                return None

        return self._engines[engine_id]

    def get_random_engine(self) -> BaseEngine:
        """随机选择一个启用的引擎"""
        enabled = [e for e in self.enabled_engines if e in self._ENGINE_CLASSES]
        if not enabled:
            raise ValueError("没有可用的搜索引擎")
        engine_id = random.choice(enabled)
        return self.get_engine(engine_id)

    def get_engines_by_priority(self) -> List[BaseEngine]:
        """按速度优先级获取启用的引擎列表"""
        engines = []
        for engine_id in self._SPEED_PRIORITY:
            if engine_id in self.enabled_engines:
                engine = self.get_engine(engine_id)
                if engine:
                    engines.append(engine)
        return engines

    def get_enabled_engine_ids(self) -> List[str]:
        """获取所有启用的引擎ID"""
        return [e for e in self.enabled_engines if e in self._ENGINE_CLASSES]

    @classmethod
    def get_all_engine_ids(cls) -> List[str]:
        """获取所有支持的引擎ID"""
        return list(cls._ENGINE_CLASSES.keys())
