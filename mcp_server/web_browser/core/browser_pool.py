"""浏览器池管理器 - 支持上下文复用和代理"""

import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from loguru import logger
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from ..config.settings import get_settings, Settings


@dataclass
class ContextInfo:
    """上下文信息"""
    context: BrowserContext
    created_at: datetime
    last_used: datetime
    page_count: int
    cookies_saved: bool = False


class BrowserPool:
    """浏览器池管理器（全局单例）"""

    _instance: Optional["BrowserPool"] = None
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, settings: Settings):
        """初始化浏览器池

        Args:
            settings: 配置对象
        """
        # 避免重复初始化
        if hasattr(self, "_initialized"):
            return

        self.settings = settings

        # Playwright 实例
        self._playwright = None
        self._browser: Optional[Browser] = None

        # 并发控制
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_browsers)

        # Context 池
        self._context_pool: List[ContextInfo] = []
        self._context_lock = asyncio.Lock()

        # 统计信息
        self._total_requests = 0
        self._active_requests = 0
        self._context_reuse_count = 0
        self._context_create_count = 0

        self._initialized = True
        logger.info(
            f"🔧 浏览器池初始化: "
            f"max_browsers={settings.max_concurrent_browsers}, "
            f"max_contexts={settings.max_contexts_per_browser}, "
            f"context_pool_size={settings.max_context_pool_size}"
        )

    async def _ensure_browser(self) -> Browser:
        """确保浏览器已启动"""
        if self._browser is None:
            async with self._lock:
                if self._browser is None:
                    logger.info("🚀 启动全局浏览器实例...")
                    self._playwright = await async_playwright().start()

                    launch_args = self._get_launch_args()

                    self._browser = await self._playwright.chromium.launch(**launch_args)
                    logger.info("✅ 全局浏览器实例已启动")

        return self._browser

    def _get_launch_args(self) -> dict:
        """获取浏览器启动参数"""
        args = {
            "headless": self.settings.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--exclude-switches=enable-automation",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--start-maximized",
                "--disable-infobars",
                "--disable-extensions",
                "--window-size=1920,1080",
                "--mute-audio",
                "--lang=zh-CN",
            ],
        }

        # 添加代理配置
        if self.settings.proxy_config:
            args["proxy"] = self.settings.proxy_config
            logger.info(f"🌐 使用代理: {self.settings.proxy_server}")

        return args

    async def _get_or_create_context(self, user_agent: str, viewport: dict = None, engine=None) -> BrowserContext:
        """从池中获取或创建 BrowserContext"""
        async with self._context_lock:
            # 清理过期的 Context
            await self._cleanup_idle_contexts()

            # 检查池中是否有空闲 Context（不考虑引擎差异，因为主要影响的是资源拦截）
            for ctx_info in self._context_pool:
                ctx = ctx_info.context
                if len(ctx.pages) == 0:
                    ctx_info.last_used = datetime.now()
                    self._context_reuse_count += 1
                    logger.debug(
                        f"♻️ 复用空闲 BrowserContext "
                        f"[池大小={len(self._context_pool)}]"
                    )
                    return ctx

            # 创建新的 Context
            browser = await self._ensure_browser()
            context = await self._create_context(browser, user_agent, viewport, engine)

            # 添加到池中
            ctx_info = ContextInfo(
                context=context,
                created_at=datetime.now(),
                last_used=datetime.now(),
                page_count=0,
                cookies_saved=False,
            )
            self._context_pool.append(ctx_info)
            self._context_create_count += 1

            logger.info(
                f"🆕 创建新 BrowserContext "
                f"[池大小={len(self._context_pool)}/{self.settings.max_context_pool_size}]"
            )

            # 加载 Cookies
            await self._load_cookies(context)

            return context

    async def _create_context(self, browser: Browser, user_agent: str, viewport: dict = None, engine=None) -> BrowserContext:
        """创建新的浏览器上下文"""
        context_options = {
            "viewport": viewport or {"width": 1920, "height": 1080},
            "user_agent": user_agent,
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "ignore_https_errors": True,
            "java_script_enabled": True,
            "extra_http_headers": {
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
        }

        context = await browser.new_context(**context_options)

        # 设置资源拦截（使用引擎的策略）
        if engine:
            block_list = engine.get_resource_block_list()
            await context.route("**/*", lambda route: self._block_resources_with_list(route, block_list))
        else:
            # 默认策略
            await context.route("**/*", self._block_resources)

        # 设置额外请求头
        await context.set_extra_http_headers({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "DNT": "1",
        })

        # 添加反检测脚本
        await context.add_init_script(self._get_anti_detection_script())

        return context

    @staticmethod
    async def _block_resources(route):
        """拦截并阻止不必要的资源加载（默认策略）

        只拦截明显非必要的资源，保留页面正常显示所需的核心资源
        """
        resource_type = route.request.resource_type
        url = route.request.url.lower()

        # 只拦截图片、字体、媒体文件等重型资源
        # 保留样式表(stylesheet)、脚本(script)、文档(document)等核心资源
        if resource_type in ["image", "font", "media"] or "icon" in url or "favicon" in url:
            await route.abort()
        else:
            await route.continue_()

    @staticmethod
    async def _block_resources_with_list(route, block_list: list):
        """根据给定的列表拦截资源

        Args:
            route: Playwright route 对象
            block_list: 需要拦截的资源类型列表，如 ["image", "font", "media"]
        """
        resource_type = route.request.resource_type
        url = route.request.url.lower()

        # 拦截指定类型的资源和图标
        if resource_type in block_list or "icon" in url or "favicon" in url:
            await route.abort()
        else:
            await route.continue_()

    @staticmethod
    def _get_anti_detection_script() -> str:
        """获取反检测脚本"""
        return """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
        Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
        Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
        Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
        Object.defineProperty(navigator, 'connection', {
            get: () => ({effectiveType: '4g', rtt: 50, downlink: 10})
        });
        window.chrome = {runtime: {}, loadTimes: function() {}, csi: function() {}, app: {}};
        delete navigator.__proto__.webdriver;
        window.outerWidth = window.screen.width;
        window.outerHeight = window.screen.height;
        """

    async def _cleanup_idle_contexts(self) -> None:
        """清理空闲过期的 Context"""
        now = datetime.now()
        to_remove = []

        for ctx_info in self._context_pool:
            idle_time = (now - ctx_info.last_used).total_seconds()
            if idle_time > self.settings.context_max_idle_time and len(ctx_info.context.pages) == 0:
                to_remove.append(ctx_info)

        for ctx_info in to_remove:
            try:
                await ctx_info.context.close()
                self._context_pool.remove(ctx_info)
                logger.debug(f"🧹 清理空闲 BrowserContext [空闲={idle_time:.0f}秒]")
            except Exception as e:
                logger.debug(f"清理 Context 失败: {e}")

    @asynccontextmanager
    async def get_page(self, user_agent: str = None, viewport: dict = None, engine=None):
        """获取一个浏览器页面（上下文管理器）

        用法:
            async with browser_pool.get_page() as page:
                await page.goto(url)
                content = await page.content()

        Args:
            user_agent: User-Agent 字符串
            viewport: 视口大小
            engine: 搜索引擎实例（用于定制资源拦截策略）

        Yields:
            Page: Playwright Page 对象
        """
        if user_agent is None:
            from ..utils.helpers import get_random_user_agent
            user_agent = get_random_user_agent()

        async with self._semaphore:
            self._total_requests += 1
            self._active_requests += 1

            logger.debug(
                f"🔍 获取页面 [活跃: {self._active_requests}/{self.settings.max_concurrent_browsers}]"
            )

            context = await self._get_or_create_context(user_agent, viewport, engine)
            page = await context.new_page()

            try:
                yield page
            finally:
                await page.close()
                self._active_requests -= 1
                logger.debug(
                    f"✅ 释放页面 [活跃: {self._active_requests}/{self.settings.max_concurrent_browsers}]"
                )

    async def _load_cookies(self, context: BrowserContext) -> None:
        """加载已保存的Cookies"""
        cookie_file = Path(self.settings.cookie_file)
        if not cookie_file.exists():
            logger.debug("📋 没有已保存的Cookies文件")
            return

        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)

            if cookies_data:
                await context.add_cookies(cookies_data)
                logger.info(f"📥 已加载 {len(cookies_data)} 个Cookies")
        except Exception as e:
            logger.debug(f"加载Cookies失败: {e}")

    async def save_cookies(self, context: BrowserContext) -> None:
        """保存Cookies到文件"""
        try:
            cookies = await context.cookies()
            with open(self.settings.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 已保存 {len(cookies)} 个Cookies到 {self.settings.cookie_file}")
        except Exception as e:
            logger.error(f"保存Cookies失败: {e}")

    async def close(self) -> None:
        """关闭浏览器池（释放所有资源）"""
        async with self._lock:
            # 关闭所有 Context
            async with self._context_lock:
                if self._context_pool:
                    logger.info(f"🔒 关闭 {len(self._context_pool)} 个 BrowserContext...")
                    for ctx_info in self._context_pool:
                        try:
                            await ctx_info.context.close()
                        except Exception as e:
                            logger.debug(f"关闭 Context 失败: {e}")
                    self._context_pool.clear()

            # 关闭浏览器
            if self._browser:
                logger.info("🔒 关闭浏览器...")
                await self._browser.close()
                self._browser = None

            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            logger.info(
                f"✅ 浏览器池已关闭 "
                f"[总请求数: {self._total_requests}, "
                f"Context创建: {self._context_create_count}, "
                f"Context复用: {self._context_reuse_count}]"
            )

    def get_stats(self) -> dict:
        """获取统计信息"""
        total_context_ops = self._context_create_count + self._context_reuse_count
        reuse_rate = (
            (self._context_reuse_count / total_context_ops * 100)
            if total_context_ops > 0
            else 0
        )

        return {
            "total_requests": self._total_requests,
            "active_requests": self._active_requests,
            "max_concurrent": self.settings.max_concurrent_browsers,
            "browser_alive": self._browser is not None,
            "context_pool_size": len(self._context_pool),
            "context_create_count": self._context_create_count,
            "context_reuse_count": self._context_reuse_count,
            "context_reuse_rate": f"{reuse_rate:.1f}%",
        }


# 全局浏览器池实例
_global_browser_pool: Optional[BrowserPool] = None


def get_browser_pool(settings: Settings = None) -> BrowserPool:
    """获取全局浏览器池实例（单例）

    Args:
        settings: 配置对象（首次创建时需要）

    Returns:
        BrowserPool: 浏览器池实例
    """
    global _global_browser_pool

    if _global_browser_pool is None:
        if settings is None:
            settings = get_settings()
        _global_browser_pool = BrowserPool(settings)

    return _global_browser_pool


async def close_global_browser_pool() -> None:
    """关闭全局浏览器池"""
    global _global_browser_pool

    if _global_browser_pool:
        await _global_browser_pool.close()
        _global_browser_pool = None
