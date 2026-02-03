"""搜狗搜索引擎"""

from typing import List

from loguru import logger
from playwright.async_api import Page

from .base import BaseEngine, EngineConfig, SearchResult


class SogouEngine(BaseEngine):
    """搜狗搜索引擎"""

    def __init__(self):
        config = EngineConfig(
            name="搜狗",
            search_url="https://www.sogou.com/web?query={query}&page=1&ie=utf8",
            news_url="https://www.sogou.com/sogou?ie=utf8&p=40230447&interation=1728053249&pid=sogou-wsse-8f646834ef1adefa&query={query}",
        )
        super().__init__(config)

    async def search(
        self,
        page: Page,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行搜狗搜索"""
        url = self.get_search_url(query, num_results, search_type)

        logger.info(f"   🌐 访问: {url}")
        await page.goto(url, timeout=30000)

        # 解析结果
        results = await self._parse_results(page)

        # 标准化URL
        current_url = await page.evaluate("() => window.location.href")
        for item in results:
            item.url = self.normalize_url(item.url, current_url)

        return results

    async def _parse_results(self, page: Page) -> List[SearchResult]:
        """解析搜索结果"""
        raw_results = await page.evaluate(
            """() => {
            const results = [];
            const mainContainer = document.querySelector('#main');
            if (!mainContainer) return results;

            const newsItems = mainContainer.querySelectorAll('div[class*="vrwrap"]');

            newsItems.forEach(item => {
                try {
                    const h3 = item.querySelector('h3');
                    if (!h3) return;

                    const link = h3.querySelector('a');
                    if (!link) return;

                    const title = link.innerText?.trim() || '';
                    const url = link.getAttribute('href') || '';

                    if (!title) return;

                    let source = '';
                    let timeStr = '';

                    const newsFrom = item.querySelector('p[class*="news-from"]');
                    if (newsFrom) {
                        const spans = newsFrom.querySelectorAll('span');
                        if (spans.length >= 1) {
                            source = spans[0].innerText?.trim() || '';
                        }
                        if (spans.length >= 2) {
                            timeStr = spans[1].innerText?.trim() || '';
                        }
                    }

                    if (!timeStr) {
                        const allDivs = item.querySelectorAll('div');
                        for (const div of allDivs) {
                            const text = div.innerText?.trim() || '';
                            if (text.match(/^\\d{4}-\\d{1,2}-\\d{1,2}$/) ||
                                text.match(/^\\d{4}年\\d{1,2}月\\d{1,2}日$/)) {
                                timeStr = text;
                                break;
                            }
                        }
                    }

                    let summary = '';
                    const allPs = item.querySelectorAll('p');
                    for (const p of allPs) {
                        const text = p.innerText?.trim() || '';
                        if (p.classList.contains('news-from') ||
                            p.classList.contains('text-lightgray')) {
                            continue;
                        }
                        if (text.length > 20 && text !== title) {
                            summary = text;
                            break;
                        }
                    }

                    if (!summary) {
                        const starWiki = item.querySelector('p[class*="star-wiki"], .str_info');
                        if (starWiki) {
                            summary = starWiki.innerText?.trim() || '';
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
        logger.info(f"   ✅ 搜狗成功解析 {len(results)} 条结果")
        return results[:30]
