"""搜索工具 - 统一的搜索接口"""

import json
import re
from typing import Optional

from loguru import logger

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


async def _execute_search(
    engine_id: str,
    query: str,
    num_results: int = 30,
    search_type: str = "web",
) -> str:
    """执行搜索的内部函数"""
    engine = _engine_factory.get_engine(engine_id)
    if not engine:
        return json.dumps(
            {"error": f"搜索引擎 {engine_id} 不可用"},
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
            results = await engine.search(page, query, num_results, search_type)

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
    """多搜索引擎搜索（带降级）"""
    # 选择引擎
    if preferred_engine == "auto":
        engine = _engine_factory.get_random_engine()
        engines_to_try = [engine] + _engine_factory.get_engines_by_priority()
    else:
        engine = _engine_factory.get_engine(preferred_engine)
        if not engine:
            engine = _engine_factory.get_random_engine()
        engines_to_try = [engine] + _engine_factory.get_engines_by_priority()

    # 去重
    seen_engines = set()
    unique_engines = []
    for e in engines_to_try:
        if e.engine_id not in seen_engines:
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
            if result_data.get("total", 0) > 0:
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
            "error": "所有搜索引擎均不可用",
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


async def multi_search(
    query: str,
    engine: str = "auto",
    num_results: int = 30,
    search_type: str = "web",
) -> str:
    """多搜索引擎 - 支持自动降级"""
    return await _multi_search_with_fallback(query, engine, num_results, search_type)


async def fetch_article_content(url: str) -> str:
    """获取文章正文内容"""
    logger.info(f"📄 [获取文章正文] URL: {url}")

    await _rate_limiter.acquire()

    try:
        user_agent = get_random_user_agent()
        async with _browser_pool.get_page(user_agent=user_agent) as page:
            await page.goto(url, timeout=30000)

            # 检查是否被拦截
            page_title = await page.title()
            if "验证" in page_title or "安全" in page_title:
                logger.warning("   ⚠️ 被安全验证拦截")
                return json.dumps(
                    {"url": url, "title": "", "content": "", "error": "被安全验证拦截"},
                    ensure_ascii=False,
                )

            # 提取标题
            title = await _extract_title(page)

            # 提取正文
            content = await _extract_content(page)

            # 清理内容
            if content:
                content = _clean_content(content)

            logger.info(f"✅ 文章内容获取完成，长度: {len(content)} 字符")

            return json.dumps(
                {
                    "url": url,
                    "title": title,
                    "content": content,
                    "content_length": len(content),
                },
                ensure_ascii=False,
                indent=2,
            )

    except Exception as e:
        logger.error(f"❌ 获取文章内容失败: {e}")
        return json.dumps(
            {"url": url, "title": "", "content": "", "error": str(e)},
            ensure_ascii=False,
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
