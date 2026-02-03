"""搜索引擎工厂 - 管理和创建搜索引擎实例"""

import random
import time
from typing import Dict, List, Optional

from loguru import logger

from .baidu import BaiduEngine
from .base import BaseEngine
from .bing import BingEngine
from .engine_360 import Engine360
from .google import GoogleEngine
from .serper import SerperEngine
from .sina import SinaEngine
from .sogou import SogouEngine
from .sohu import SohuEngine
from .tencent import TencentEngine
from .toutiao import ToutiaoEngine
from .wangyi import WangyiEngine


class EngineFactory:
    """搜索引擎工厂 - 支持自动禁用被拦截的引擎（递增禁用机制）"""

    # 所有可用的搜索引擎类
    _ENGINE_CLASSES = {
        "baidu": BaiduEngine,
        "bing": BingEngine,
        "sogou": SogouEngine,
        "google": GoogleEngine,
        "360": Engine360,
        "toutiao": ToutiaoEngine,
        "tencent": TencentEngine,
        "wangyi": WangyiEngine,
        "sina": SinaEngine,
        "sohu": SohuEngine,
    }

    # API 搜索引擎（不需要浏览器）
    _API_ENGINES = {
        "serper": SerperEngine,
    }

    # 引擎速度优先级（根据测试数据，越快越靠前）
    _SPEED_PRIORITY = [
        "serper",  # API 引擎优先
        "baidu",
        "sogou",
        "toutiao",
        "tencent",
        "360",
        "wangyi",
        "sina",
        "google",
        "sohu",
        "bing",
    ]

    # 禁用时间配置（秒）
    BAN_DURATION_BASE = 300  # 基础禁用时间：5分钟
    BAN_DURATION_MAX = 1800  # 最大禁用时间：30分钟

    def __init__(self, enabled_engines: List[str] = None):
        """初始化引擎工厂

        Args:
            enabled_engines: 启用的引擎列表
        """
        all_engines = list(self._ENGINE_CLASSES.keys()) + list(self._API_ENGINES.keys())
        self.enabled_engines = enabled_engines or all_engines
        self._engines: Dict[str, BaseEngine] = {}
        self._api_engine_instances: Dict[str, SerperEngine] = {}
        # 记录被禁用的引擎及其信息 {engine_id: {'unban_time': timestamp, 'ban_count': count}}
        self._banned_engines: Dict[str, dict] = {}

    def get_engine(self, engine_id: str) -> Optional[BaseEngine]:
        """获取指定引擎实例

        Args:
            engine_id: 引擎ID

        Returns:
            引擎实例，如果不存在、未启用或被禁用则返回 None
        """
        # API 引擎直接返回（不受禁用机制影响）
        if engine_id in self._API_ENGINES:
            if engine_id not in self.enabled_engines:
                logger.warning(f"❌ API 引擎 {engine_id} 未启用")
                return None

            if engine_id not in self._api_engine_instances:
                engine_class = self._API_ENGINES[engine_id]
                self._api_engine_instances[engine_id] = engine_class()
                logger.info(f"✅ 创建 API 引擎 {engine_id} 实例")

            return self._api_engine_instances[engine_id]

        # 检查是否被禁用
        if self.is_engine_banned(engine_id):
            logger.warning(f"🚫 引擎 {engine_id} 已被禁用（反爬虫拦截）")
            return None

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

    def ban_engine(self, engine_id: str, reason: str = "被反爬虫拦截"):
        """禁用引擎（递增禁用机制）

        Args:
            engine_id: 引擎ID
            reason: 禁用原因

        禁用时长：
        - 首次：5分钟
        - 第2次：10分钟
        - 第3次：20分钟
        - 第4次及以后：30分钟（上限）
        """
        # 获取当前禁用次数
        if engine_id in self._banned_engines:
            ban_count = self._banned_engines[engine_id].get("ban_count", 0) + 1
        else:
            ban_count = 1

        # 计算禁用时长（指数增长，最大30分钟）
        ban_duration = min(
            self.BAN_DURATION_BASE * (2 ** (ban_count - 1)), self.BAN_DURATION_MAX
        )

        unban_time = time.time() + ban_duration
        self._banned_engines[engine_id] = {
            "unban_time": unban_time,
            "ban_count": ban_count,
        }
        logger.warning(
            f"🚫 禁用引擎 {engine_id}: {reason} "
            f"(第{ban_count}次，{ban_duration//60}分钟)"
        )

    def is_engine_banned(self, engine_id: str) -> bool:
        """检查引擎是否被禁用

        Args:
            engine_id: 引擎ID

        Returns:
            True if banned, False otherwise
        """
        if engine_id not in self._banned_engines:
            return False

        ban_info = self._banned_engines[engine_id]
        unban_time = ban_info["unban_time"]

        # 检查是否已到解禁时间
        if time.time() >= unban_time:
            # 自动解禁，但保留禁用计数用于递增机制
            # （重置计数可选，这里选择保留以累积惩罚）
            del self._banned_engines[engine_id]
            logger.info(f"✅ 引擎 {engine_id} 已自动解禁")
            return False

        return True

    def get_random_engine(self) -> Optional[BaseEngine]:
        """随机选择一个启用的引擎（跳过被禁用的）"""
        available_engines = []

        # API 引擎总是可用
        for engine_id in self._API_ENGINES:
            if engine_id in self.enabled_engines:
                available_engines.append(engine_id)

        # 浏览器引擎（检查是否被禁用）
        for engine_id in self.enabled_engines:
            if engine_id in self._ENGINE_CLASSES and not self.is_engine_banned(
                engine_id
            ):
                available_engines.append(engine_id)

        if not available_engines:
            logger.warning("❌ 没有可用的搜索引擎（所有引擎均被禁用）")
            return None

        engine_id = random.choice(available_engines)
        return self.get_engine(engine_id)

    def get_engines_by_priority(self) -> List[BaseEngine]:
        """按速度优先级获取启用的引擎列表（跳过被禁用的）"""
        engines = []
        for engine_id in self._SPEED_PRIORITY:
            if engine_id in self.enabled_engines and not self.is_engine_banned(
                engine_id
            ):
                engine = self.get_engine(engine_id)
                if engine:
                    engines.append(engine)
        return engines

    def get_enabled_engine_ids(self) -> List[str]:
        """获取所有启用的引擎ID（不包括被禁用的）"""
        enabled = []

        # API 引擎（不受禁用影响）
        for e in self.enabled_engines:
            if e in self._API_ENGINES:
                enabled.append(e)

        # 浏览器引擎（检查是否被禁用）
        for e in self.enabled_engines:
            if e in self._ENGINE_CLASSES and not self.is_engine_banned(e):
                enabled.append(e)

        return enabled

    def get_available_engine_count(self) -> int:
        """获取当前可用引擎数量"""
        return len(self.get_enabled_engine_ids())

    def get_banned_engine_count(self) -> int:
        """获取被禁用引擎数量"""
        return len(self._banned_engines)

    @classmethod
    def get_all_engine_ids(cls) -> List[str]:
        """获取所有支持的引擎ID"""
        return list(cls._ENGINE_CLASSES.keys()) + list(cls._API_ENGINES.keys())
