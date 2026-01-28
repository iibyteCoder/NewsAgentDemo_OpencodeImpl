"""搜索工具 - 统一的搜索接口"""

import json
import re
from typing import Optional

from loguru import logger
from playwright.async_api import Page

from ..config.settings import get_settings
from ..core.browser_pool import get_browser_pool
from ..core.rate_limiter import RateLimiter
from ..engines.base import SearchResult
from ..engines.factory import EngineFactory
from ..utils.helpers import get_random_user_agent, search_result_to_dict


# 全局实例
_settings = get_settings()
_browser_pool = get_browser_pool(_settings)
_rate_limiter = RateLimiter(
    time_window=_settings.rate_limit_time_window,
    max_domain_requests=_settings.max_domain_requests_per_second,
    max_engine_requests=_settings.max_engine_requests_per_second,
)
_engine_factory = EngineFactory(enabled_engines=_settings.enabled_engines)


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
        response = await page.evaluate("() => ({ status: window.performance?.getEntriesByType?.('navigation')?.[0]?.responseStatus || 200 })")
        if response and response.get("status", 200) >= 400:
            return True, f"HTTP错误: {response['status']}"

        # 2. 检查页面标题
        page_title = await page.title()
        anti_bot_keywords = [
            "验证", "安全", "captcha", "人机验证", "机器人", "robot", "验证码",
            "滑动验证", "点选验证", "短信验证", "阿里云", "云盾", "腾讯云", "天御",
            "访问频繁", "请求过于频繁", "操作过于频繁", "系统检测", "异常访问",
            "风险检测", "安全检测", "cc攻击", "防刷", "反爬"
        ]

        page_title_lower = page_title.lower()
        for keyword in anti_bot_keywords:
            if keyword.lower() in page_title_lower or keyword in page_title:
                return True, f"页面标题包含反爬虫关键词: {keyword}"

        # 3. 检查页面内容
        body_text = await page.evaluate("() => document.body.innerText?.substring(0, 500) || ''")
        anti_bot_phrases = [
            '访问过于频繁', '请求过于频繁', '操作过于频繁', '系统检测到异常访问',
            '疑似机器人', '人机验证', '安全验证', '请完成验证', 'ip被封', '禁止访问',
            'access denied', 'forbidden', 'rate limit', 'too many requests'
        ]

        for phrase in anti_bot_phrases:
            if phrase.lower() in body_text.lower():
                return True, f"页面内容包含反爬虫提示: {phrase}"

        # 4. 检查验证码元素
        captcha_elements = await page.evaluate("""() => {
            const selectors = ['#captcha', '.captcha', '[class*="captcha"]', '#geetest',
                             '[class*="geetest"]', '.recaptcha', '[class*="recaptcha"]',
                             '.verify', '[class*="verify"]'];
            for (const selector of selectors) {
                if (document.querySelector(selector)) {
                    return true;
                }
            }
            return false;
        }""")

        if captcha_elements:
            return True, "检测到验证码元素"

        return False, ""

    except Exception as e:
        logger.warning(f"⚠️ 反爬虫检测失败: {e}")
        return False, ""


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
            {"error": f"搜索引擎 {engine_id} 不可用"},
            "engine": engine_id,
            "engine_name": engine_id,
            "query": query,
            "total": 0,
            "results": [],
            ensure_ascii=False,
        )

    logger.info(f"🔍 [{engine.config.name}] {query} ({search_type})")

    # 应用速率限制
    search_url = engine.get_search_url(query, num_results, search_type)
    domain = engine.extract_domain(search_url)
    await _rate_limiter.acquire(domain=domain, engine=engine_id)

    try:
        user_agent = get_random_user_agent()
        async with _browser_pool.get_page(user_agent=user_agent) as page:
            # 先访问页面
            await page.goto(search_url, timeout=30000)

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
                logger.info(f"   ✅ {engine.config.name} 成功返回 {result_data['total']} 条结果")
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
            response = await page.goto(url, timeout=30000)

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
    """提取文章正文"""
    content_selectors = [
        "article",
        ".article-content",
        ".news-content",
        ".content",
        "[class*='content']",
        "#content",
        ".article-body",
        ".post-content",
        "main",
    ]

    for selector in content_selectors:
        try:
            content_elem = await page.query_selector(selector)
            if content_elem:
                paragraphs = await content_elem.query_selector_all("p")
                if paragraphs and len(paragraphs) >= 3:
                    content_parts = []
                    for p in paragraphs[:20]:
                        text = await p.text_content()
                        if text and len(text.strip()) > 10:
                            content_parts.append(text.strip())

                    if content_parts:
                        full_content = "\n\n".join(content_parts)
                        logger.info(f"   ✅ 提取到 {len(content_parts)} 个段落")
                        return full_content
        except Exception:
            continue

    # 备用方案：使用 JavaScript 提取
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
    """提取文章中的图片链接

    Args:
        page: Playwright页面对象
        base_url: 基础URL（用于处理相对路径）

    Returns:
        图片信息列表，每个图片包含 url, alt, width, height
    """
    try:
        images = await page.evaluate(
            """(baseUrl) => {
            const images = [];
            const imgElements = document.querySelectorAll('article img, .content img, .article-content img, main img, .news-content img, [class*="content"] img');

            imgElements.forEach((img, idx) => {
                const src = img.src || img.getAttribute('data-src');
                if (src) {
                    // 处理相对路径
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

                    images.push({
                        index: idx + 1,
                        url: fullUrl,
                        alt: img.alt || '',
                        title: img.title || '',
                        width: img.naturalWidth || img.width || 0,
                        height: img.naturalHeight || img.height || 0
                    });
                }
            });

            return images;
        }""",
            base_url,
        )

        logger.info(f"   🖼️ 找到 {len(images)} 个图片")
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
                    status_info["suggestions"] = ["页面不存在", "检查URL是否正确", "尝试搜索相关内容"]
                elif status_code == 403:
                    status_info["suggestions"] = ["访问被拒绝", "可能需要登录", "尝试使用其他网站"]
                elif status_code >= 500:
                    status_info["suggestions"] = ["服务器错误", "稍后重试", "尝试使用镜像网站"]

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
        error_keywords = ["404", "不存在", "无法访问", "not found", "页面不存在", "访问失败"]
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
            status_info["checks"].append(f"检测到验证码元素: {page_check.get('captchaElements', [])}")
            status_info["suggestions"] = [
                "❌ 被反爬虫验证码拦截",
                "🚫 需要人工验证，浏览器已无法使用",
                "⏰ 建议等待较长时间后重试（30分钟以上）",
                "🔄 必须更换IP或使用代理",
                "🔍 尝试使用其他搜索引擎",
                "📱 尝试使用移动端网站",
            ]
            logger.warning(f"🚨 检测到反爬虫拦截（验证码）: {page_check.get('captchaElements', [])}")
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
            status_info["checks"].append(f"页面文本长度: {page_check.get('textLength', 0)}")
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


async def baidu_hot_search() -> str:
    """获取百度热搜榜"""
    logger.info("🔥 [百度热搜榜] 获取热搜榜单")

    await _rate_limiter.acquire()

    try:
        hot_url = "https://top.baidu.com/board?tab=realtime"

        user_agent = get_random_user_agent()
        async with _browser_pool.get_page(user_agent=user_agent) as page:
            await page.goto(hot_url, timeout=30000)

            hot_items = await page.evaluate(
                """() => {
                const items = [];
                const elements = document.querySelectorAll('.category-wrap_iQLoo.horizontal_1eKyQ');

                elements.forEach((item, idx) => {
                    try {
                        const titleElem = item.querySelector('.c-single-text-ellipsis');
                        const title = titleElem ? titleElem.innerText?.trim() || '' : '';

                        const hotScoreElem = item.querySelector('.hot-index_1Bl1a');
                        const hotScore = hotScoreElem ? hotScoreElem.innerText?.trim() || '' : '';

                        const linkElem = item.querySelector('a');
                        const url = linkElem ? linkElem.getAttribute('href') || '' : '';

                        if (title) {
                            items.push({
                                rank: idx + 1,
                                title,
                                hot_score: hotScore,
                                url
                            });
                        }
                    } catch (e) {
                        // 忽略单个条目的解析错误
                    }
                });

                return items;
            }"""
            )

        logger.info(f"✅ 热搜榜获取完成: {len(hot_items)} 条")

        return json.dumps(
            {"total": len(hot_items), "hot_items": hot_items},
            ensure_ascii=False,
            indent=2,
        )

    except Exception as e:
        logger.error(f"❌ 获取百度热搜失败: {e}")
        return json.dumps(
            {"total": 0, "hot_items": [], "error": str(e)},
            ensure_ascii=False,
        )
