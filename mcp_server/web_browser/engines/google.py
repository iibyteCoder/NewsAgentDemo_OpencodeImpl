"""谷歌搜索引擎"""

from typing import List

from loguru import logger
from playwright.async_api import Page

from .base import BaseEngine, EngineConfig, SearchResult


class GoogleEngine(BaseEngine):
    """谷歌搜索引擎"""

    def __init__(self):
        config = EngineConfig(
            name="谷歌",
            search_url="https://www.google.com/search?q={query}",
            news_url="https://www.google.com/search?q={query}&tbm=nws",
        )
        super().__init__(config)

    async def search(
        self,
        page: Page,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行谷歌搜索"""
        url = self.get_search_url(query, num_results, search_type)

        logger.info(f"   🌐 访问: {url}")
        await page.goto(url, timeout=30000)

        # 检查是否被拦截
        page_content = await page.content()
        if "验证" in page_content:
            logger.warning("   ⚠️ 被谷歌安全验证拦截")
            return []

        return await self._parse_results(page)

    async def _parse_results(self, page: Page) -> List[SearchResult]:
        """解析搜索结果"""
        raw_results = await page.evaluate(
            """() => {
            const results = [];
            const newsContainers = document.querySelectorAll('div[data-news-doc-id], div[data-news-cluster-id]');

            newsContainers.forEach(container => {
                try {
                    const link = container.querySelector('a[href]');
                    if (!link) return;

                    const url = link.getAttribute('href') || '';
                    if (!url || url.startsWith('#')) return;

                    const titleElem = link.querySelector('div[role="heading"]');
                    const title = titleElem?.innerText?.trim() || '';
                    if (!title) return;

                    const timeElem = link.querySelector('span[data-ts]');
                    const timeStr = timeElem?.innerText?.trim() || '';

                    let source = '';
                    const allDivs = link.querySelectorAll('div');
                    for (const div of allDivs) {
                        const divText = div.innerText?.trim() || '';
                        if (divText && divText.length < 20 && divText !== title &&
                            !divText.includes('前') && !div.querySelector('div[role="heading"]')) {
                            const span = div.querySelector('span');
                            if (span && !span.hasAttribute('data-ts')) {
                                source = span.innerText?.trim() || '';
                                if (source && source.length > 0) {
                                    break;
                                }
                            }
                        }
                    }

                    let summary = '';
                    for (const div of allDivs) {
                        const divText = div.innerText?.trim() || '';
                        if (divText && divText.length > 30 && divText !== title &&
                            !divText.includes(timeStr) && !div.querySelector('span[data-ts]')) {
                            if (!div.querySelector('div[role="heading"]')) {
                                summary = divText;
                                break;
                            }
                        }
                    }

                    results.push({title, url, summary, source, time: timeStr});
                } catch (e) {
                    // 忽略单个结果的解析错误
                }
            });

            return results;
        }"""
        )

        # 转换为 SearchResult 对象
        results = [SearchResult(**r) for r in raw_results]
        logger.info(f"   ✅ 谷歌成功解析 {len(results)} 条结果")
        return results[:30]
