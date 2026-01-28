"""必应搜索引擎"""

from typing import List

from loguru import logger
from playwright.async_api import Page

from .base import BaseEngine, EngineConfig, SearchResult


class BingEngine(BaseEngine):
    """必应搜索引擎"""

    def __init__(self):
        config = EngineConfig(
            name="必应",
            search_url="https://cn.bing.com/search?q={query}&count={num}",
            news_url="https://www.bing.com/news/search?q={query}",
        )
        super().__init__(config)

    async def search(
        self,
        page: Page,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行必应搜索"""
        url = self.get_search_url(query, num_results, search_type)

        logger.info(f"   🌐 访问: {url}")
        # 使用 domcontentloaded 而非 load，大幅提升速度
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # 等待新闻卡片出现（最多等待 5 秒）
        try:
            await page.wait_for_selector('div[class*="news-card"]', timeout=5000)
        except Exception:
            logger.debug("   ⏱️ 未检测到新闻卡片，可能页面结构已变化")

        # 检查是否被拦截
        page_title = await page.title()
        if "验证" in page_title:
            logger.warning("   ⚠️ 被必应安全验证拦截")
            return []

        # 解析结果（新闻和网页使用相同的解析逻辑）
        return await self._parse_results(page)

    async def _parse_results(self, page: Page) -> List[SearchResult]:
        """解析搜索结果"""
        raw_results = await page.evaluate("""() => {
            const results = [];
            const newsCards = document.querySelectorAll('div[class*="news-card"]');

            newsCards.forEach(card => {
                try {
                    const url = card.getAttribute('data-url') || '';
                    if (!url) return;

                    let title = card.getAttribute('data-title') || '';
                    if (!title) {
                        const h2 = card.querySelector('h2');
                        if (h2) {
                            title = h2.innerText?.trim() || '';
                        }
                    }
                    if (!title) return;

                    const source = card.getAttribute('data-author') || '';

                    let timeStr = '';
                    const timeSpan = card.querySelector('span[tabindex="0"]');
                    if (timeSpan) {
                        const ariaLabel = timeSpan.getAttribute('aria-label');
                        if (ariaLabel) {
                            timeStr = ariaLabel;
                        } else {
                            const innerDiv = timeSpan.querySelector('div');
                            if (innerDiv) {
                                timeStr = innerDiv.innerText?.trim() || '';
                            } else {
                                timeStr = timeSpan.innerText?.trim() || '';
                            }
                        }
                    }

                    let summary = '';
                    const snippet = card.querySelector('.snippet');
                    if (snippet) {
                        summary = snippet.innerText?.trim() || '';
                    }

                    results.push({title, url, summary, source, time: timeStr});
                } catch (e) {
                    // 忽略单个结果的解析错误
                }
            });

            return results;
        }""")

        # 转换为 SearchResult 对象
        results = [SearchResult(**r) for r in raw_results]
        logger.info(f"   ✅ 必应成功解析 {len(results)} 条结果")
        return results[:30]
