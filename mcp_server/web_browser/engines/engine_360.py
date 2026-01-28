"""360搜索引擎"""

from typing import List

from loguru import logger
from playwright.async_api import Page

from .base import BaseEngine, EngineConfig, SearchResult


class Engine360(BaseEngine):
    """360搜索引擎"""

    def __init__(self):
        config = EngineConfig(
            name="360",
            search_url="https://www.so.com/s?q={query}",
            news_url="https://news.so.com/ns?q={query}",
        )
        super().__init__(config)

    async def search(
        self,
        page: Page,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行360搜索"""
        url = self.get_search_url(query, num_results, search_type)

        logger.info(f"   🌐 访问: {url}")
        await page.goto(url, timeout=30000)

        return await self._parse_results(page)

    async def _parse_results(self, page: Page) -> List[SearchResult]:
        """解析搜索结果"""
        raw_results = await page.evaluate("""() => {
            const results = [];
            const newsItems = document.querySelectorAll('li[data-from="news"]');

            newsItems.forEach(item => {
                try {
                    const url = item.getAttribute('data-url') || '';
                    if (!url) return;

                    const h3 = item.querySelector('h3');
                    if (!h3) return;

                    const titleDiv = h3.querySelector('.g-txt-inner');
                    if (!titleDiv) return;

                    const title = titleDiv.innerText?.trim() || '';
                    if (!title) return;

                    let summary = '';
                    const summaryElem = item.querySelector('.summary');
                    if (summaryElem) {
                        summary = summaryElem.innerText?.trim() || '';
                    }

                    let source = '';
                    const sourceElem = item.querySelector('.sitename');
                    if (sourceElem) {
                        source = sourceElem.innerText?.trim() || '';
                    }

                    let timeStr = '';
                    const timeElem = item.querySelector('.time');
                    if (timeElem) {
                        timeStr = timeElem.innerText?.trim() || '';
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
        logger.info(f"   ✅ 360成功解析 {len(results)} 条结果")
        return results[:30]
