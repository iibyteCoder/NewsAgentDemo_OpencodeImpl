"""搜索工具 - 统一的搜索接口"""

import json
import re
from typing import Optional
from urllib.parse import urljoin

from loguru import logger
from playwright.async_api import Page

from ..config.settings import get_settings
from ..core.browser_pool import get_browser_pool
from ..core.rate_limiter import RateLimiter
from ..engines.factory import EngineFactory
from ..engines.serper import SerperEngine
from ..utils.helpers import get_random_user_agent, search_result_to_dict

# ========== 常量定义 ==========
# 图片过滤相关常量
DATA_IMAGE_PREFIX = "data:image"
MIN_IMAGE_URL_LENGTH = 20
MIN_IMAGE_SIZE = 100

# 无关图片关键词（用于URL过滤）
UNWANTED_IMAGE_KEYWORDS = [
    "icon",
    "logo",
    "pixel",
    "tracking",
    "avatar",
    "ad",
    "banner",
    "sponsor",
    "affiliate",
    "share",
    "social",
    "facebook",
    "twitter",
    "weibo",
    "wechat",
    "qq",
    "arrow",
    "bullet",
    "separator",
    "divider",
    "background",
    "pattern",
    "watermark",
    "qr-code",
    "qrcode",
    "barcode",
    "captcha",
    "loading",
    "spinner",
    "placeholder",
    "default",
    "thumb",
    "thumbnail",
    "small",
    "mini",
    "tiny",
]

# 有效图片扩展名
VALID_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]

# 无关区域选择器
UNWANTED_PARENT_SELECTORS = [
    "header",
    "footer",
    "nav",
    "aside",
    ".sidebar",
    ".header",
    ".footer",
    ".navigation",
    ".menu",
    ".advertisement",
    ".ad",
    ".ad-banner",
    ".ad-container",
    ".share",
    ".social",
    ".social-share",
    ".sharing",
    ".comment",
    ".comments",
    ".related",
    ".recommended",
    ".author-info",
    ".author-bio",
    ".sidebar-content",
    '[class*="ad-"]',
    '[class*="advertisement"]',
    '[id*="ad-"]',
    '[id*="advertisement"]',
    ".widget",
    ".widgets",
    ".sidebar-widget",
    ".newsletter",
    ".subscribe",
    ".subscription",
    ".breadcrumb",
    ".breadcrumbs",
    ".pager",
    ".pagination",
]

# 正文区域选择器
CONTENT_SELECTORS = [
    "article",
    '[role="article"]',
    "article .article-content",
    "article .content",
    "article .post-content",
    "article .entry-content",
    "article .article-body",
    "article .post-body",
    "main .content",
    "main .article-content",
    "main .post-content",
    "main .entry-content",
    ".article-content",
    ".post-content",
    ".entry-content",
    ".article-body",
    ".post-body",
    ".news-content",
    "#article-content",
    "#post-content",
    "#content",
]


# 全局实例
_settings = get_settings()
_browser_pool = get_browser_pool(_settings)
_rate_limiter = RateLimiter(
    time_window=_settings.rate_limit_time_window,
    max_domain_requests=_settings.max_domain_requests_per_second,
    max_engine_requests=_settings.max_engine_requests_per_second,
)
_engine_factory = EngineFactory(enabled_engines=_settings.enabled_engines)


# ========== 图片过滤辅助函数 ==========


def _is_valid_image_url(url: str) -> bool:
    """检查图片URL是否有效

    Args:
        url: 图片URL

    Returns:
        是否为有效的图片URL
    """
    if not url or len(url) < MIN_IMAGE_URL_LENGTH:
        return False

    if url.startswith(DATA_IMAGE_PREFIX):
        return False

    url_lower = url.lower()

    # 检查是否包含无关关键词
    if any(kw in url_lower for kw in UNWANTED_IMAGE_KEYWORDS):
        return False

    # 检查是否为有效图片格式
    if not any(ext in url_lower for ext in VALID_IMAGE_EXTENSIONS):
        return False

    return True


def _normalize_image_url(url: str, base_url: str) -> str:
    """规范化图片URL（处理相对路径）

    Args:
        url: 图片URL（可能是相对路径）
        base_url: 基础URL

    Returns:
        规范化后的完整URL
    """
    if url.startswith("//"):
        return "https:" + url
    elif url.startswith("/"):
        return urljoin(base_url, url)
    elif not url.startswith("http"):
        return urljoin(base_url, url)
    return url


def _create_image_dict(
    index: int, url: str, alt: str = "", width: int = 0, height: int = 0
) -> dict:
    """创建图片信息字典

    Args:
        index: 图片索引
        url: 图片URL
        alt: 图片alt文本
        width: 图片宽度
        height: 图片高度

    Returns:
        图片信息字典
    """
    return {
        "index": index,
        "url": url,
        "alt": alt,
        "width": width,
        "height": height,
    }


async def _check_anti_bot(page: Page, url: str) -> tuple[bool, str]:
    """检测页面是否被反爬虫拦截

    Args:
        page: Playwright页面对象
        url: 页面URL

    Returns:
        (是否被拦截, 拦截原因)
    """
    try:
        # 1. 检查HTTP状态
        response = await page.evaluate(
            "() => ({ status: window.performance?.getEntriesByType?.('navigation')?.[0]?.responseStatus || 200 })"
        )
        if response and response.get("status", 200) >= 400:
            return True, f"HTTP错误: {response['status']}"

        # 2. 检查页面标题
        page_title = await page.title()
        anti_bot_keywords = [
            "验证",
            "安全",
            "captcha",
            "人机验证",
            "机器人",
            "robot",
            "验证码",
            "滑动验证",
            "点选验证",
            "短信验证",
            "阿里云",
            "云盾",
            "腾讯云",
            "天御",
            "访问频繁",
            "请求过于频繁",
            "操作过于频繁",
            "系统检测",
            "异常访问",
            "风险检测",
            "安全检测",
            "cc攻击",
            "防刷",
            "反爬",
        ]

        page_title_lower = page_title.lower()
        for keyword in anti_bot_keywords:
            if keyword.lower() in page_title_lower or keyword in page_title:
                return True, f"页面标题包含反爬虫关键词: {keyword}"

        # 3. 检查页面内容
        body_text = await page.evaluate(
            "() => document.body.innerText?.substring(0, 500) || ''"
        )
        anti_bot_phrases = [
            "访问过于频繁",
            "请求过于频繁",
            "操作过于频繁",
            "系统检测到异常访问",
            "疑似机器人",
            "人机验证",
            "安全验证",
            "请完成验证",
            "ip被封",
            "禁止访问",
            "access denied",
            "forbidden",
            "rate limit",
            "too many requests",
        ]

        for phrase in anti_bot_phrases:
            if phrase.lower() in body_text.lower():
                return True, f"页面内容包含反爬虫提示: {phrase}"

        # 4. 检查验证码元素
        captcha_elements = await page.evaluate(
            """() => {
            const selectors = ['#captcha', '.captcha', '[class*="captcha"]', '#geetest',
                             '[class*="geetest"]', '.recaptcha', '[class*="recaptcha"]',
                             '.verify', '[class*="verify"]'];
            for (const selector of selectors) {
                if (document.querySelector(selector)) {
                    return true;
                }
            }
            return false;
        }"""
        )

        if captcha_elements:
            return True, "检测到验证码元素"

        return False, ""

    except Exception as e:
        logger.warning(f"⚠️ 反爬虫检测失败: {e}")
        return False, ""


def _is_api_engine(engine) -> bool:
    """检查是否为 API 引擎"""
    return isinstance(engine, SerperEngine)


async def _execute_search(
    engine_id: str,
    query: str,
    num_results: int = 30,
    search_type: str = "web",
) -> str:
    """执行搜索的内部函数（带反爬虫检测）"""
    engine = _engine_factory.get_engine(engine_id)
    if not engine:
        return json.dumps(
            {
                "error": f"搜索引擎 {engine_id} 不可用",
                "engine": engine_id,
                "engine_name": engine_id,
                "query": query,
                "total": 0,
                "results": [],
            },
            ensure_ascii=False,
        )

    logger.info(f"🔍 [{engine.name}] {query} ({search_type})")

    # API 引擎直接调用（不需要浏览器，不受速率限制）
    if _is_api_engine(engine):
        try:
            results = await engine.search(query, num_results, search_type)
            results_dict = [search_result_to_dict(r) for r in results]

            return json.dumps(
                {
                    "engine": engine_id,
                    "engine_name": engine.name,
                    "query": query,
                    "total": len(results_dict),
                    "results": results_dict,
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            logger.error(f"❌ {engine.name} 搜索失败: {e}")
            return json.dumps(
                {
                    "engine": engine_id,
                    "engine_name": engine.name,
                    "query": query,
                    "total": 0,
                    "results": [],
                    "error": str(e),
                },
                ensure_ascii=False,
            )

    # 浏览器引擎：应用速率限制
    search_url = engine.get_search_url(query, num_results, search_type)
    domain = engine.extract_domain(search_url)
    await _rate_limiter.acquire(domain=domain, engine=engine_id)

    try:
        user_agent = get_random_user_agent()
        async with _browser_pool.get_page(user_agent=user_agent, engine=engine) as page:
            # 先访问页面
            await page.goto(search_url, timeout=_settings.page_load_timeout)

            # 检测反爬虫拦截
            is_blocked, block_reason = await _check_anti_bot(page, search_url)
            if is_blocked:
                logger.error(f"🚨 {engine.config.name} 被反爬虫拦截: {block_reason}")
                # 禁用该引擎
                _engine_factory.ban_engine(engine_id, block_reason)
                return json.dumps(
                    {
                        "engine": engine_id,
                        "engine_name": engine.config.name,
                        "query": query,
                        "total": 0,
                        "results": [],
                        "blocked": True,
                        "block_reason": block_reason,
                        "error": "被反爬虫拦截",
                    },
                    ensure_ascii=False,
                    indent=2,
                )

            # 执行搜索
            results = await engine.search(page, query, num_results, search_type)

            # 如果没有结果，可能是被拦截了
            if len(results) == 0:
                logger.warning(f"⚠️ {engine.config.name} 返回0条结果，可能被拦截")
                # 不禁用引擎，只记录警告
                # 如果连续多次失败，可以考虑禁用

            results_dict = [search_result_to_dict(r) for r in results]

            return json.dumps(
                {
                    "engine": engine_id,
                    "engine_name": engine.config.name,
                    "query": query,
                    "total": len(results_dict),
                    "results": results_dict,
                },
                ensure_ascii=False,
                indent=2,
            )

    except Exception as e:
        logger.error(f"❌ {engine.config.name} 搜索失败: {e}")
        return json.dumps(
            {
                "engine": engine_id,
                "engine_name": engine.config.name,
                "query": query,
                "total": 0,
                "results": [],
                "error": str(e),
            },
            ensure_ascii=False,
        )


async def _multi_search_with_fallback(
    query: str,
    preferred_engine: str = "auto",
    num_results: int = 30,
    search_type: str = "web",
) -> str:
    """多搜索引擎搜索（智能降级，自动跳过被禁用的引擎）"""
    available_count = _engine_factory.get_available_engine_count()
    banned_count = _engine_factory.get_banned_engine_count()

    logger.info(f"📊 可用引擎: {available_count}个, 被禁用: {banned_count}个")

    # 选择引擎
    if preferred_engine == "auto":
        engine = _engine_factory.get_random_engine()
        if not engine:
            return json.dumps(
                {
                    "query": query,
                    "total": 0,
                    "results": [],
                    "error": f"所有搜索引擎均被禁用，请稍后重试（被禁用引擎将在{EngineFactory.BAN_DURATION}秒后自动解禁）",
                },
                ensure_ascii=False,
            )
        engines_to_try = [engine] + _engine_factory.get_engines_by_priority()
    else:
        engine = _engine_factory.get_engine(preferred_engine)
        if not engine:
            engine = _engine_factory.get_random_engine()
        if not engine:
            return json.dumps(
                {
                    "query": query,
                    "total": 0,
                    "results": [],
                    "error": "所有搜索引擎均被禁用",
                },
                ensure_ascii=False,
            )
        engines_to_try = [engine] + _engine_factory.get_engines_by_priority()

    # 去重
    seen_engines = set()
    unique_engines = []
    for e in engines_to_try:
        if e and e.engine_id not in seen_engines:
            seen_engines.add(e.engine_id)
            unique_engines.append(e)

    logger.info(f"   📋 引擎尝试顺序: {[e.engine_id for e in unique_engines]}")

    # 依次尝试每个引擎
    for engine in unique_engines:
        try:
            result = await _execute_search(
                engine_id=engine.engine_id,
                query=query,
                num_results=num_results,
                search_type=search_type,
            )

            result_data = json.loads(result)

            # 如果被拦截，继续尝试下一个引擎
            if result_data.get("blocked"):
                logger.warning(f"   ⚠️ {engine.config.name} 被拦截，尝试下一个引擎")
                continue

            # 如果有结果，返回
            if result_data.get("total", 0) > 0:
                logger.info(
                    f"   ✅ {engine.config.name} 成功返回 {result_data['total']} 条结果"
                )
                # 添加引擎状态信息
                result_data["available_engines"] = available_count
                result_data["banned_engines"] = banned_count
                return result

        except Exception as e:
            logger.warning(f"   ❌ {engine.config.name} 搜索失败: {e}")
            continue

    # 所有引擎都失败
    return json.dumps(
        {
            "query": query,
            "total": 0,
            "results": [],
            "error": "所有搜索引擎均不可用或返回0条结果",
            "available_engines": _engine_factory.get_available_engine_count(),
            "banned_engines": _engine_factory.get_banned_engine_count(),
        },
        ensure_ascii=False,
    )


# ========== 公开工具函数 ==========


async def baidu_search(
    query: str, num_results: int = 30, time_range: Optional[str] = None
) -> str:
    """百度搜索

    Args:
        query: 搜索关键词
        num_results: 返回结果数量
        time_range: 时间范围（暂未实现，保留参数）
    """
    _ = time_range  # 保留参数，暂未实现
    return await _execute_search("baidu", query, num_results, "web")


async def baidu_news_search(query: str, num_results: int = 30) -> str:
    """百度新闻搜索"""
    return await _execute_search("baidu", query, num_results, "news")


async def bing_search(query: str, num_results: int = 30) -> str:
    """必应搜索"""
    return await _execute_search("bing", query, num_results, "web")


async def bing_news_search(query: str, num_results: int = 30) -> str:
    """必应新闻搜索"""
    return await _execute_search("bing", query, num_results, "news")


async def sogou_search(query: str, num_results: int = 30) -> str:
    """搜狗搜索"""
    return await _execute_search("sogou", query, num_results, "web")


async def sogou_news_search(query: str, num_results: int = 30) -> str:
    """搜狗新闻搜索"""
    return await _execute_search("sogou", query, num_results, "news")


async def google_search(query: str, num_results: int = 30) -> str:
    """谷歌搜索"""
    return await _execute_search("google", query, num_results, "web")


async def google_news_search(query: str, num_results: int = 30) -> str:
    """谷歌新闻搜索"""
    return await _execute_search("google", query, num_results, "news")


async def search_360(query: str, num_results: int = 30) -> str:
    """360搜索"""
    return await _execute_search("360", query, num_results, "web")


async def search_360_news(query: str, num_results: int = 30) -> str:
    """360新闻搜索"""
    return await _execute_search("360", query, num_results, "news")


async def toutiao_search(query: str, num_results: int = 30) -> str:
    """今日头条搜索"""
    return await _execute_search("toutiao", query, num_results, "web")


async def toutiao_news_search(query: str, num_results: int = 30) -> str:
    """今日头条新闻搜索"""
    return await _execute_search("toutiao", query, num_results, "news")


async def tencent_search(query: str, num_results: int = 30) -> str:
    """腾讯新闻搜索"""
    return await _execute_search("tencent", query, num_results, "web")


async def tencent_news_search(query: str, num_results: int = 30) -> str:
    """腾讯新闻搜索"""
    return await _execute_search("tencent", query, num_results, "news")


async def wangyi_search(query: str, num_results: int = 30) -> str:
    """网易新闻搜索"""
    return await _execute_search("wangyi", query, num_results, "web")


async def wangyi_news_search(query: str, num_results: int = 30) -> str:
    """网易新闻搜索"""
    return await _execute_search("wangyi", query, num_results, "news")


async def sina_search(query: str, num_results: int = 30) -> str:
    """新浪新闻搜索"""
    return await _execute_search("sina", query, num_results, "web")


async def sina_news_search(query: str, num_results: int = 30) -> str:
    """新浪新闻搜索"""
    return await _execute_search("sina", query, num_results, "news")


async def sohu_search(query: str, num_results: int = 30) -> str:
    """搜狐新闻搜索"""
    return await _execute_search("sohu", query, num_results, "web")


async def sohu_news_search(query: str, num_results: int = 30) -> str:
    """搜狐新闻搜索"""
    return await _execute_search("sohu", query, num_results, "news")


async def multi_search(
    query: str,
    engine: str = "auto",
    num_results: int = 30,
    search_type: str = "web",
) -> str:
    """多搜索引擎 - 支持自动降级"""
    return await _multi_search_with_fallback(query, engine, num_results, search_type)


async def fetch_article_content(url: str, include_images: bool = True) -> str:
    """获取文章正文内容

    Args:
        url: 文章URL
        include_images: 是否提取图片链接（默认True）

    Note:
        始终会检测并返回页面状态信息，包括：
        - HTTP状态码
        - 页面加载状态
        - 内容质量评估
        - 智能建议
    """
    logger.info(f"📄 [获取文章正文] URL: {url}")

    await _rate_limiter.acquire()

    try:
        user_agent = get_random_user_agent()
        async with _browser_pool.get_page(user_agent=user_agent) as page:
            response = await page.goto(url, timeout=_settings.page_navigation_timeout)

            # 始终检查页面状态
            status = await _check_page_status(page, response, url)

            # 如果页面状态异常，直接返回状态信息
            if status.get("status") == "error":
                logger.warning(f"   ⚠️ 页面异常: {status.get('reason')}")
                return json.dumps(
                    {
                        "url": url,
                        "status": status,
                        "title": "",
                        "content": "",
                        "images": [],
                        "suggestions": status.get("suggestions", []),
                    },
                    ensure_ascii=False,
                    indent=2,
                )

            logger.info(f"   ✓ 页面状态: {status.get('status', 'unknown')}")

            # 提取标题
            title = await _extract_title(page)

            # 提取正文
            content = await _extract_content(page)

            # 清理内容
            if content:
                content = _clean_content(content)

            # 始终检查内容质量
            if content:
                content_quality = _assess_content_quality(content, title, len(content))
                status.update(content_quality)

            # 提取图片链接
            images = []
            if include_images:
                images = await _extract_images(page, url)
                logger.info(f"   🖼️ 提取到 {len(images)} 个图片链接")

            logger.info(f"✅ 文章内容获取完成，长度: {len(content)} 字符")

            # 构建结果，始终包含状态信息
            result = {
                "url": url,
                "title": title,
                "content": content,
                "content_length": len(content),
                "images": images,
                "image_count": len(images),
                "status": status,
            }

            # 根据状态给出建议
            if status.get("status") in ["warning", "poor"]:
                result["suggestions"] = _get_suggestions(status)
            elif status.get("status") == "ok":
                result["suggestions"] = ["✅ 页面状态正常"]

            return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取文章内容失败: {e}")
        error_status = {
            "status": "error",
            "reason": f"请求失败: {str(e)}",
            "error_type": type(e).__name__,
        }
        return json.dumps(
            {
                "url": url,
                "status": error_status,
                "title": "",
                "content": "",
                "images": [],
                "suggestions": ["检查URL是否正确", "尝试使用其他搜索引擎"],
            },
            ensure_ascii=False,
            indent=2,
        )


async def _extract_title(page) -> str:
    """提取文章标题"""
    title_selectors = [
        "h1",
        ".article-title",
        ".news-title",
        ".title",
        "[class*='title']",
        "#title",
    ]

    for selector in title_selectors:
        try:
            title_elem = await page.query_selector(selector)
            if title_elem:
                title_text = await title_elem.text_content()
                if title_text and len(title_text.strip()) > 5:
                    logger.info(f"   📰 标题: {title_text[:50]}...")
                    return title_text.strip()
        except Exception:
            continue

    return ""


async def _extract_content(page) -> str:
    """提取文章正文（使用 trafilatura 成熟算法）"""
    try:
        # 获取页面HTML
        html = await page.content()

        # 使用 trafilatura 提取内容
        import trafilatura

        # 提取主要内容
        content = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=False,
            favor_recall=True,
        )

        if content and len(content.strip()) > 100:
            logger.info(f"   ✅ trafilatura 提取成功，长度: {len(content)} 字符")
            return content.strip()
        else:
            logger.warning("   ⚠️ trafilatura 提取内容过少，使用备用方案")
            return await _extract_content_fallback(page)

    except ImportError:
        logger.warning("   ⚠️ trafilatura 未安装，使用备用方案")
        return await _extract_content_fallback(page)
    except Exception as e:
        logger.warning(f"   ⚠️ trafilatura 提取失败: {e}，使用备用方案")
        return await _extract_content_fallback(page)


async def _extract_content_fallback(page) -> str:
    """备用方案：使用 JavaScript 提取内容"""
    logger.warning("   ⚠️ 常规选择器失败，尝试备用方案")

    body_text = await page.evaluate(
        """() => {
        const clones = document.body.cloneNode(true);

        const unwantedSelectors = [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            'iframe', 'noscript', 'meta', 'link', '[class*="ad"]',
            '[class*="advertisement"]', '[class*="sidebar"]',
            '[class*="comment"]', '[class*="share"]', '[class*="social"]',
            '[id*="ad"]', '[id*="advertisement"]'
        ];

        unwantedSelectors.forEach(selector => {
            const elements = clones.querySelectorAll(selector);
            elements.forEach(el => el.remove());
        });

        const contentElements = clones.querySelectorAll('p, h1, h2, h3, h4, div, span');
        const texts = [];

        contentElements.forEach(el => {
            const text = el.textContent || el.innerText || '';
            const trimmed = text.trim();

            if (trimmed.length > 20 &&
                !trimmed.includes('点击') &&
                !trimmed.includes('关注') &&
                !trimmed.includes('订阅') &&
                !trimmed.match(/^\\d+$/)) {
                texts.push(trimmed);
            }
        });

        const uniqueTexts = [...new Set(texts)];

        if (uniqueTexts.length >= 3) {
            return uniqueTexts.slice(0, 30).join('\\n\\n');
        }
        return '';
    }"""
    )

    if body_text and len(body_text) > 100:
        logger.info(f"   ✅ 备用方案提取到内容，长度: {len(body_text)}")
        return body_text

    return ""


def _clean_content(content: str) -> str:
    """清理和规范化内容"""
    # 移除多余的空白字符
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = re.sub(r"[ \t]+", " ", content)
    content = re.sub(r"\n +", "\n", content)
    content = content.strip()

    # 移除常见的无用文本
    useless_patterns = [
        r"点击查看.*详情",
        r"更多内容请.*",
        r"责任编辑.*",
        r"版权声明.*",
        r"本文来源.*",
        r"转载请注明.*",
        r"免责声明.*",
        r"广告.*",
    ]
    for pattern in useless_patterns:
        content = re.sub(pattern, "", content, flags=re.IGNORECASE)

    return content


async def _extract_images(page, base_url: str) -> list[dict]:
    """提取文章中的图片链接（使用专业工具）

    优先级调整说明:
    1. JavaScript 备用方案 - 最严格的正文区域检测，过滤无关图片
    2. newspaper3k - 作为备选
    3. trafilatura - 作为最后备选

    原因：newspaper3k 会提取整个页面的图片，包括相关文章、缩略图等
    而 JavaScript fallback 有10层过滤逻辑，能更准确地提取正文图片

    Args:
        page: Playwright页面对象
        base_url: 基础URL（用于处理相对路径）

    Returns:
        图片信息列表，每个图片包含 url, alt, width, height
    """
    # 方法1: 优先使用 JavaScript 方案（最严格的过滤）
    result = await _extract_images_fallback(page, base_url)
    if result:
        return result

    # 方法2: newspaper3k 作为备选
    html = await page.content()
    result = _extract_images_newspaper3k(html, base_url)
    if result:
        return result

    # 方法3: trafilatura 作为最后备选
    result = _extract_images_trafilatura(html, base_url)
    return result


def _extract_images_newspaper3k(html: str, base_url: str) -> list[dict]:
    """使用 newspaper3k 提取图片"""
    try:
        from newspaper import Article, Config

        config = Config()
        config.browser_user_agent = "Mozilla/5.0"
        config.fetch_images = False
        config.request_timeout = 10

        article = Article(url=base_url, config=config)
        article.set_html(html)
        article.parse()

        # 提取图片列表
        if article.images and len(article.images) > 0:
            valid_images = [url for url in article.images if _is_valid_image_url(url)]

            if valid_images:
                logger.info(
                    f"   ✅ newspaper3k 提取到 {len(valid_images)} 个有效图片 (原始{len(article.images)}个)"
                )
                return [
                    _create_image_dict(i + 1, url) for i, url in enumerate(valid_images)
                ]
            else:
                logger.info("   ⚠️ newspaper3k 提取的图片都被过滤掉了")

        # 检查主图
        elif article.top_img and _is_valid_image_url(article.top_img):
            logger.info(f"   ✅ newspaper3k 提取到主图: {article.top_img}")
            return [_create_image_dict(1, article.top_img)]

        logger.info("   ⚠️ newspaper3k 未找到有效图片，尝试下一个方法")

    except ImportError:
        logger.info("   ⚠️ newspaper3k 未安装，尝试下一个方法")
    except Exception as e:
        logger.info(f"   ⚠️ newspaper3k 提取失败: {e}，尝试下一个方法")

    return []


def _extract_images_trafilatura(html: str, base_url: str) -> list[dict]:
    """使用 trafilatura 提取正文图片"""
    try:
        import trafilatura
        from bs4 import BeautifulSoup

        # 提取主要内容
        extracted_html = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            output_format="html",
            no_fallback=False,
        )

        if not extracted_html:
            logger.info("   ⚠️ trafilatura 未提取到正文内容")
            return []

        soup = BeautifulSoup(extracted_html, "html.parser")
        img_tags = soup.find_all("img")

        if not img_tags:
            logger.info("   ⚠️ trafilatura 正文中未找到图片")
            return []

        valid_images = []
        for img in img_tags:
            src = img.get("src") or img.get("data-src")
            if not src or not _is_valid_image_url(src):
                continue

            # 规范化URL
            normalized_url = _normalize_image_url(src, base_url)
            valid_images.append(normalized_url)

        if valid_images:
            logger.info(f"   ✅ trafilatura 正文中提取到 {len(valid_images)} 个图片")
            return [
                _create_image_dict(i + 1, url) for i, url in enumerate(valid_images)
            ]

        logger.info("   ⚠️ trafilatura 未找到有效图片，使用备用方案")

    except ImportError:
        logger.info("   ⚠️ BeautifulSoup 或 trafilatura 未安装，使用备用方案")
    except Exception as e:
        logger.info(f"   ⚠️ trafilatura 图片提取失败: {e}，使用备用方案")

    return []


async def _extract_images_fallback(page, base_url: str) -> list[dict]:
    """备用方案：使用 JavaScript 提取正文区域内的图片

    优化策略：
    1. 先定位正文区域容器
    2. 只提取正文容器内的图片
    3. 严格过滤无关图片（广告、图标、装饰等）
    4. 检查图片与正文段落的位置关系
    """
    try:
        images = await page.evaluate(
            """(baseUrl) => {
            // ========== 1. 定位正文区域容器 ==========
            const contentSelectors = [
                'article',
                '[role="article"]',
                'article .article-content',
                'article .content',
                'article .post-content',
                'article .entry-content',
                'article .article-body',
                'article .post-body',
                'main .content',
                'main .article-content',
                'main .post-content',
                'main .entry-content',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.article-body',
                '.post-body',
                '.news-content',
                '#article-content',
                '#post-content',
                '#content',
            ];

            let contentContainer = null;
            for (const selector of contentSelectors) {
                const elem = document.querySelector(selector);
                if (elem) {
                    // 检查容器是否包含足够的文本内容（至少200字）
                    const textLength = elem.innerText?.length || 0;
                    if (textLength >= 200) {
                        contentContainer = elem;
                        break;
                    }
                }
            }

            // 如果没找到明确的正文容器，使用 body
            if (!contentContainer) {
                contentContainer = document.body;
            }

            // ========== 2. 只提取正文容器内的图片 ==========
            const images = [];
            const imgElements = contentContainer.querySelectorAll('img, picture img, figure img');

            // ========== 3. 无关区域选择器（这些区域的图片要排除） ==========
            const unwantedParentSelectors = [
                'header', 'footer', 'nav', 'aside', '.sidebar',
                '.header', '.footer', '.navigation', '.menu',
                '.advertisement', '.ad', '.ad-banner', '.ad-container',
                '.share', '.social', '.social-share', '.sharing',
                '.comment', '.comments', '.related', '.recommended',
                '.author-info', '.author-bio', '.sidebar-content',
                '[class*="ad-"]', '[class*="advertisement"]',
                '[id*="ad-"]', '[id*="advertisement"]',
                '.widget', '.widgets', '.sidebar-widget',
                '.newsletter', '.subscribe', '.subscription',
                '.breadcrumb', '.breadcrumbs', '.pager', '.pagination',
            ];

            // ========== 4. 无关图片关键词（URL中包含这些关键词的排除） ==========
            const unwantedKeywords = [
                'icon', 'logo', 'avatar', 'pixel', 'tracking',
                'ad', 'banner', 'sponsor', 'affiliate',
                'share', 'social', 'facebook', 'twitter', 'weibo',
                'wechat', 'qq', 'arrow', 'bullet', 'separator',
                'divider', 'background', 'pattern', 'watermark',
                'qr-code', 'qrcode', 'barcode', 'captcha',
                'loading', 'spinner', 'placeholder', 'default',
                'thumb', 'thumbnail', 'small', 'mini', 'tiny',
            ];

            imgElements.forEach((img, idx) => {
                const src = img.src || img.getAttribute('data-src') || img.getAttribute('data-original');

                if (!src || src.length < 15) return;

                // ========== 5. 检查图片是否在无关区域内 ==========
                let parent = img.parentElement;
                let inUnwantedArea = false;
                let depth = 0;
                while (parent && depth < 10) {
                    const classList = parent.className || '';
                    const id = parent.id || '';
                    const tagName = parent.tagName?.toLowerCase() || '';

                    for (const selector of unwantedParentSelectors) {
                        // 检查标签名
                        if (selector === tagName) {
                            inUnwantedArea = true;
                            break;
                        }
                        // 检查 class
                        if (classList.includes(selector.replace('.', ''))) {
                            inUnwantedArea = true;
                            break;
                        }
                        // 检查 id
                        if (id === selector.replace('#', '')) {
                            inUnwantedArea = true;
                            break;
                        }
                    }

                    if (inUnwantedArea) break;
                    parent = parent.parentElement;
                    depth++;
                }

                if (inUnwantedArea) return;

                // ========== 6. 检查 URL 是否包含无关关键词 ==========
                const srcLower = src.toLowerCase();
                const hasUnwantedKeyword = unwantedKeywords.some(kw => srcLower.includes(kw));
                if (hasUnwantedKeyword) return;

                // ========== 7. 处理相对路径 ==========
                let fullUrl = src;
                if (src.startsWith('//')) {
                    fullUrl = 'https:' + src;
                } else if (src.startsWith('/')) {
                    try {
                        const urlObj = new URL(baseUrl);
                        fullUrl = urlObj.origin + src;
                    } catch (e) {
                        fullUrl = src;
                    }
                } else if (!src.startsWith('http')) {
                    try {
                        fullUrl = new URL(src, baseUrl).href;
                    } catch (e) {
                        fullUrl = src;
                    }
                }

                // ========== 8. 检查图片尺寸（更严格） ==========
                const width = img.naturalWidth || img.width || 0;
                const height = img.naturalHeight || img.height || 0;

                // 尺寸过滤：宽高都必须大于100px，且宽高比要合理（0.2-5.0之间）
                if (width < 100 || height < 100) return;
                const aspectRatio = width / height;
                if (aspectRatio < 0.2 || aspectRatio > 5.0) return;

                // ========== 9. 检查图片周围的文本（确保与正文相关） ==========
                // 如果图片的父元素或相邻元素没有文本，可能是装饰性图片
                let hasNearbyText = false;
                let checkElem = img.parentElement;
                let checks = 0;
                while (checkElem && checks < 3) {
                    const text = checkElem.innerText?.trim() || '';
                    if (text.length >= 20) {
                        hasNearbyText = true;
                        break;
                    }
                    checkElem = checkElem.parentElement;
                    checks++;
                }

                // 检查前后兄弟元素
                if (!hasNearbyText) {
                    const prev = img.previousElementSibling;
                    const next = img.nextElementSibling;
                    const prevText = prev?.innerText?.trim() || '';
                    const nextText = next?.innerText?.trim() || '';
                    if (prevText.length >= 20 || nextText.length >= 20) {
                        hasNearbyText = true;
                    }
                }

                if (!hasNearbyText) return;

                // ========== 10. 检查图片格式（只保留常见格式） ==========
                const validExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'];
                const hasValidExtension = validExtensions.some(ext => fullUrl.toLowerCase().includes(ext));
                // 如果 URL 中没有文件扩展名，但图片通过了其他检查，也接受

                images.push({
                    index: images.length + 1,
                    url: fullUrl,
                    alt: img.alt || '',
                    title: img.title || '',
                    width: width,
                    height: height
                });
            });

            return images;
        }""",
            base_url,
        )

        logger.info(f"   🖼️ 备用方案找到 {len(images)} 个正文图片")
        return images

    except Exception as e:
        logger.warning(f"   ⚠️ 提取图片失败: {e}")
        return []


async def _check_page_status(page, response, url: str) -> dict:
    """检查页面状态（加强反爬虫检测）

    Args:
        page: Playwright页面对象
        response: 响应对象
        url: 页面URL

    Returns:
        状态信息字典
    """
    status_info = {
        "status": "unknown",
        "checks": [],
        "anti_bot_detected": False,  # 反爬虫检测标记
    }

    try:
        # 1. 检查HTTP状态码
        if response:
            status_code = response.status
            status_info["http_status"] = status_code

            if status_code >= 400:
                status_info["status"] = "error"
                status_info["reason"] = f"HTTP错误: {status_code}"
                status_info["checks"].append(f"HTTP状态码异常: {status_code}")

                if status_code == 404:
                    status_info["suggestions"] = [
                        "页面不存在",
                        "检查URL是否正确",
                        "尝试搜索相关内容",
                    ]
                elif status_code == 403:
                    status_info["suggestions"] = [
                        "访问被拒绝",
                        "可能需要登录",
                        "尝试使用其他网站",
                    ]
                elif status_code >= 500:
                    status_info["suggestions"] = [
                        "服务器错误",
                        "稍后重试",
                        "尝试使用镜像网站",
                    ]

                return status_info

            status_info["checks"].append(f"HTTP状态码正常: {status_code}")

        # 2. 检查页面标题（加强反爬虫检测）
        page_title = await page.title()
        status_info["page_title"] = page_title

        # 反爬虫关键词列表（扩展）
        anti_bot_keywords = [
            "验证",
            "安全",
            "captcha",
            "人机验证",
            "机器人",
            "robot",
            "bot",
            "验证码",
            "滑动验证",
            "点选验证",
            "短信验证",
            "阿里云",
            "云盾",
            "腾讯云",
            "天御",
            "访问频繁",
            "请求过于频繁",
            "操作过于频繁",
            "系统检测",
            "异常访问",
            "风险检测",
            "安全检测",
            "cc攻击",
            "防刷",
            "反爬",
        ]

        page_title_lower = page_title.lower()
        for keyword in anti_bot_keywords:
            if keyword.lower() in page_title_lower or keyword in page_title:
                status_info["status"] = "error"
                status_info["reason"] = f"被反爬虫拦截: 检测到关键词 '{keyword}'"
                status_info["anti_bot_detected"] = True
                status_info["anti_bot_type"] = "title_keyword"
                status_info["checks"].append(f"标题包含反爬虫关键词: {keyword}")
                status_info["suggestions"] = [
                    "❌ 被反爬虫验证拦截",
                    "🚫 检测到反爬虫关键词，建议暂停使用",
                    "⏰ 等待较长时间后重试（建议30分钟以上）",
                    "🔄 考虑更换IP或使用代理",
                    "🔍 尝试使用其他搜索引擎",
                    "📱 尝试使用移动端网站",
                ]
                logger.warning(f"🚨 检测到反爬虫拦截（标题）: {keyword}")
                return status_info

        # 检查是否是错误页面
        error_keywords = [
            "404",
            "不存在",
            "无法访问",
            "not found",
            "页面不存在",
            "访问失败",
        ]
        if any(keyword in page_title for keyword in error_keywords):
            status_info["status"] = "error"
            status_info["reason"] = "页面不存在或无法访问"
            status_info["checks"].append("标题包含错误信息")
            status_info["suggestions"] = [
                "页面不存在",
                "检查URL是否正确",
                "尝试搜索其他来源",
            ]
            return status_info

        status_info["checks"].append("页面标题正常")

        # 3. 使用JavaScript检查页面内容（加强反爬虫检测）
        page_check = await page.evaluate(
            """() => {
            const checks = {
                hasBody: !!document.body,
                bodyText: document.body ? document.body.innerText.substring(0, 500) : '',
                hasArticle: !!document.querySelector('article'),
                hasContent: !!document.querySelector('.content, .article-content, main, [class*="content"]'),
                errorCode: null,
                needsLogin: false,
                isEmpty: false,
                // 反爬虫检测
                hasCaptcha: false,
                captchaElements: [],
                antiBotElements: [],
                accessDenied: false,
                ipBlocked: false,
            };

            // 检查验证码相关元素
            const captchaSelectors = [
                '#captcha',
                '.captcha',
                '[class*="captcha"]',
                '[id*="captcha"]',
                '.geetest',
                '#geetest',
                '[class*="geetest"]',
                '.recaptcha',
                '[class*="recaptcha"]',
                '.verify',
                '[class*="verify"]',
                '.validate',
                '[class*="validate"]',
                'iframe[src*="captcha"]',
                'iframe[src*="verify"]',
            ];

            captchaSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    checks.hasCaptcha = true;
                    checks.captchaElements.push(selector);
                }
            });

            // 检查反爬虫提示文本
            const bodyText = document.body.innerText.toLowerCase();
            const antiBotPhrases = [
                '访问过于频繁',
                '请求过于频繁',
                '操作过于频繁',
                '您的访问过于频繁',
                '请稍后再试',
                '系统检测到异常访问',
                '疑似机器人',
                '人机验证',
                '安全验证',
                '请完成验证',
                '滑动验证',
                '点选验证',
                '阿里云盾',
                '腾讯云天御',
                '风险控制',
                '安全检测',
                'cc防御',
                'waf防火墙',
                '访问被拒绝',
                'ip被封',
                '禁止访问',
                'access denied',
                'forbidden',
                'blocked',
                'rate limit',
                'too many requests',
            ];

            antiBotPhrases.forEach(phrase => {
                if (bodyText.includes(phrase)) {
                    checks.antiBotElements.push(phrase);
                }
            });

            // 检查是否IP被封禁
            const ipBlockedPhrases = [
                'ip被封',
                'ip已被封',
                'ip禁止',
                'ip限制',
                '封禁ip',
                '禁止ip',
                'blocked ip',
                'ip blocked',
            ];

            checks.ipBlocked = ipBlockedPhrases.some(phrase => bodyText.includes(phrase));

            // 检查是否需要登录
            const loginKeywords = ['登录', 'login', 'signin', '请先登录', '需要登录'];
            checks.needsLogin = loginKeywords.some(keyword =>
                document.body.innerText.includes(keyword)
            );

            // 检查页面是否为空
            const textLength = document.body.innerText.trim().length;
            checks.isEmpty = textLength < 100;
            checks.textLength = textLength;

            return checks;
        }"""
        )

        status_info["page_checks"] = {
            "has_body": page_check["hasBody"],
            "has_article": page_check["hasArticle"],
            "has_content": page_check["hasContent"],
            "text_length": page_check.get("textLength", 0),
        }

        # 检查验证码元素（重要！）
        if page_check.get("hasCaptcha") or page_check.get("captchaElements"):
            status_info["status"] = "error"
            status_info["reason"] = "被反爬虫拦截: 检测到验证码"
            status_info["anti_bot_detected"] = True
            status_info["anti_bot_type"] = "captcha_element"
            status_info["checks"].append(
                f"检测到验证码元素: {page_check.get('captchaElements', [])}"
            )
            status_info["suggestions"] = [
                "❌ 被反爬虫验证码拦截",
                "🚫 需要人工验证，浏览器已无法使用",
                "⏰ 建议等待较长时间后重试（30分钟以上）",
                "🔄 必须更换IP或使用代理",
                "🔍 尝试使用其他搜索引擎",
                "📱 尝试使用移动端网站",
            ]
            logger.warning(
                f"🚨 检测到反爬虫拦截（验证码）: {page_check.get('captchaElements', [])}"
            )
            return status_info

        # 检查反爬虫提示文本
        anti_bot_elements = page_check.get("antiBotElements", [])
        if anti_bot_elements:
            status_info["status"] = "error"
            status_info["reason"] = f"被反爬虫拦截: {anti_bot_elements[0]}"
            status_info["anti_bot_detected"] = True
            status_info["anti_bot_type"] = "content_text"
            status_info["checks"].append(f"内容包含反爬虫文本: {anti_bot_elements}")
            status_info["suggestions"] = [
                "❌ 被反爬虫拦截",
                "🚫 检测到反爬虫提示，建议暂停使用",
                "⏰ 等待较长时间后重试（建议30分钟以上）",
                "🔄 考虑更换IP或使用代理",
                "🔍 尝试使用其他搜索引擎",
            ]
            logger.warning(f"🚨 检测到反爬虫拦截（文本）: {anti_bot_elements}")
            return status_info

        # 检查IP是否被封
        if page_check.get("ipBlocked"):
            status_info["status"] = "error"
            status_info["reason"] = "IP被封禁"
            status_info["anti_bot_detected"] = True
            status_info["anti_bot_type"] = "ip_blocked"
            status_info["checks"].append("检测到IP封禁提示")
            status_info["suggestions"] = [
                "❌ IP已被封禁",
                "🚫 必须更换IP才能继续",
                "⏰ 建议等待较长时间后重试（1小时以上）",
                "🔄 使用代理或更换网络",
                "🔍 尝试使用其他搜索引擎",
            ]
            logger.warning("🚨 检测到IP封禁")
            return status_info

        # 检查错误代码
        if page_check.get("errorCode"):
            status_info["status"] = "error"
            status_info["reason"] = f"页面返回错误: {page_check['errorCode']}"
            status_info["checks"].append(f"内容包含错误代码: {page_check['errorCode']}")
            status_info["suggestions"] = [
                "页面无法访问",
                "尝试使用其他网站",
                "尝试搜索相关内容",
            ]
            return status_info

        # 检查是否需要登录
        if page_check.get("needsLogin"):
            status_info["status"] = "warning"
            status_info["reason"] = "页面可能需要登录"
            status_info["checks"].append("检测到登录提示")
            status_info["suggestions"] = [
                "页面需要登录才能访问",
                "尝试搜索公开的内容",
                "寻找其他来源",
            ]
            return status_info

        # 检查页面是否为空
        if page_check.get("isEmpty"):
            status_info["status"] = "warning"
            status_info["reason"] = "页面内容过少"
            status_info["checks"].append(
                f"页面文本长度: {page_check.get('textLength', 0)}"
            )
            status_info["suggestions"] = [
                "页面内容过少",
                "可能是加载中或内容被限制",
                "尝试等待或使用其他来源",
            ]
            return status_info

        # 所有检查通过
        status_info["status"] = "ok"
        status_info["reason"] = "页面状态正常"
        status_info["checks"].append("页面加载正常")
        status_info["anti_bot_detected"] = False

        return status_info

    except Exception as e:
        logger.error(f"检查页面状态失败: {e}")
        status_info["status"] = "error"
        status_info["reason"] = f"状态检查失败: {str(e)}"
        status_info["suggestions"] = ["无法验证页面状态", "尝试直接访问URL"]
        return status_info


def _assess_content_quality(content: str, title: str, content_length: int) -> dict:
    """评估内容质量

    Args:
        content: 文章内容
        title: 文章标题
        content_length: 内容长度

    Returns:
        质量评估信息
    """
    quality = {
        "quality": "unknown",
        "score": 0,
        "issues": [],
    }

    # 1. 检查标题
    if not title or len(title) < 5:
        quality["issues"].append("标题过短或缺失")
        quality["score"] -= 10
    else:
        quality["score"] += 10

    # 2. 检查内容长度
    if content_length < 100:
        quality["issues"].append("内容过少")
        quality["score"] -= 30
        quality["quality"] = "poor"
    elif content_length < 300:
        quality["issues"].append("内容较少")
        quality["score"] -= 15
        quality["quality"] = "warning"
    elif content_length >= 500:
        quality["score"] += 20

    # 3. 检查段落数量
    paragraphs = content.split("\n\n")
    if len(paragraphs) < 2:
        quality["issues"].append("段落结构简单")
        quality["score"] -= 10
    elif len(paragraphs) >= 5:
        quality["score"] += 10

    # 4. 检查是否包含错误信息
    error_patterns = [
        "页面不存在",
        "访问受限",
        "请登录",
        "404",
        "403",
        "无法访问",
    ]
    for pattern in error_patterns:
        if pattern in content:
            quality["issues"].append(f"内容包含错误信息: {pattern}")
            quality["score"] -= 50
            quality["quality"] = "poor"
            break

    # 5. 检查是否包含广告或无关内容
    ad_patterns = ["广告", "点击查看", "关注我们", "扫码", "分享"]
    ad_count = sum(1 for pattern in ad_patterns if pattern in content)
    if ad_count > 5:
        quality["issues"].append("可能包含较多广告信息")
        quality["score"] -= 5

    # 确定质量等级
    if quality["quality"] == "unknown":
        if quality["score"] >= 30:
            quality["quality"] = "good"
        elif quality["score"] >= 10:
            quality["quality"] = "acceptable"
        elif quality["score"] >= 0:
            quality["quality"] = "warning"
        else:
            quality["quality"] = "poor"

    return quality


def _get_suggestions(status: dict) -> list[str]:
    """根据状态给出建议

    Args:
        status: 状态信息字典

    Returns:
        建议列表
    """
    suggestions = []

    status_level = status.get("status", "unknown")
    reason = status.get("reason", "")

    if status_level == "error":
        if "验证" in reason or "captcha" in reason.lower():
            suggestions.extend(
                [
                    "❌ 被反爬虫验证拦截",
                    "💡 建议：尝试使用其他搜索引擎",
                    "💡 建议：等待几秒后重试",
                    "💡 建议：寻找其他网站的相同内容",
                ]
            )
        elif "404" in reason or "不存在" in reason:
            suggestions.extend(
                [
                    "❌ 页面不存在",
                    "💡 建议：检查URL是否正确",
                    "💡 建议：尝试搜索相关关键词",
                    "💡 建议：使用其他搜索引擎",
                ]
            )
        elif "403" in reason or "拒绝" in reason:
            suggestions.extend(
                [
                    "❌ 访问被拒绝",
                    "💡 建议：寻找其他公开来源",
                    "💡 建议：尝试使用搜索引擎找类似内容",
                ]
            )
        else:
            suggestions.extend(
                [
                    f"❌ {reason}",
                    "💡 建议：尝试使用其他搜索引擎",
                    "💡 建议：搜索相关关键词",
                ]
            )

    elif status_level == "warning":
        if "登录" in reason:
            suggestions.extend(
                [
                    "⚠️ 页面需要登录",
                    "💡 建议：寻找公开的内容来源",
                    "💡 建议：使用搜索引擎找相关文章",
                ]
            )
        elif "过少" in reason or "内容" in reason:
            suggestions.extend(
                [
                    "⚠️ 页面内容不足",
                    "💡 建议：尝试使用其他网站",
                    "💡 建议：搜索更多相关内容",
                ]
            )
        else:
            suggestions.append(f"⚠️ {reason}")

    # 根据质量评估给出建议
    quality = status.get("quality", "")
    if quality == "poor":
        suggestions.extend(
            [
                "📊 内容质量评估：较差",
                "💡 建议：尝试其他来源",
                "💡 建议：综合多个来源的信息",
            ]
        )
    elif quality == "warning":
        suggestions.extend(
            [
                "📊 内容质量评估：一般",
                "💡 建议：可以参考，但建议寻找更多来源",
            ]
        )

    if not suggestions:
        suggestions.append("✅ 页面状态正常")

    return suggestions


# ========== Serper 搜索函数 ==========


async def serper_search(query: str, num_results: int = 30) -> str:
    """Serper 搜索（使用 Google Search API）

    Args:
        query: 搜索关键词
        num_results: 返回结果数量（最大100）

    Note:
        Serper.dev 使用 API 调用，不需要浏览器
        速度快，稳定性高，但需要 API Key
    """
    return await _execute_search("serper", query, num_results, "web")


async def serper_news_search(query: str, num_results: int = 30) -> str:
    """Serper 新闻搜索（使用 Google Search API）

    Args:
        query: 搜索关键词
        num_results: 返回结果数量（最大100）

    Note:
        Serper.dev 使用 API 调用，不需要浏览器
    """
    return await _execute_search("serper", query, num_results, "news")
