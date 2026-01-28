"""百度搜索引擎"""

from typing import List

from loguru import logger
from playwright.async_api import Page

from .base import BaseEngine, EngineConfig, SearchResult


class BaiduEngine(BaseEngine):
    """百度搜索引擎"""

    def __init__(self):
        config = EngineConfig(
            name="百度",
            search_url="https://www.baidu.com/s?wd={query}&rn={num}",
            news_url="https://www.baidu.com/s?tn=news&rtt=1&bsst=1&cl=2&wd={query}",
        )
        super().__init__(config)

    async def search(
        self,
        page: Page,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行百度搜索"""
        url = self.get_search_url(query, num_results, search_type)

        logger.info(f"   🌐 访问: {url}")
        await page.goto(url, timeout=30000)

        # 检查是否被拦截
        page_title = await page.title()
        if "验证" in page_title or "安全" in page_title:
            logger.warning("   ⚠️ 被百度安全验证拦截")
            return []

        # 解析结果
        if search_type == "news":
            return await self._parse_news_results(page)
        else:
            return await self._parse_web_results(page)

    async def _parse_web_results(self, page: Page) -> List[SearchResult]:
        """解析网页搜索结果"""
        raw_results = await page.evaluate("""() => {
            const results = [];
            const contentLeft = document.querySelector('#content_left');
            if (!contentLeft) return results;

            const newsItems = contentLeft.querySelectorAll('div[srcid], div.result-op');

            newsItems.forEach(item => {
                try {
                    const h3 = item.querySelector('h3');
                    if (!h3) return;

                    const link = h3.querySelector('a');
                    if (!link) return;

                    const title = link.innerText?.trim() || '';
                    const url = link.getAttribute('href') || '';

                    if (!title) return;

                    // 提取时间
                    let timeStr = '';
                    const allSpans = item.querySelectorAll('span');
                    for (const span of allSpans) {
                        const text = span.innerText?.trim() || '';
                        if (text.match(/昨天|前天|\\d+小时前|\\d+月\\d+日|\\d+天前/)) {
                            timeStr = text;
                            break;
                        }
                    }

                    // 提取摘要
                    let summary = '';
                    const allDivs = item.querySelectorAll('div');
                    for (const div of allDivs) {
                        const text = div.innerText?.trim() || '';
                        if (text.length > 30 && text !== title && !text.includes(timeStr)) {
                            summary = text;
                            break;
                        }
                    }

                    // 提取来源
                    let source = '';
                    for (const span of allSpans) {
                        const text = span.innerText?.trim() || '';
                        if (text.length >= 2 && text.length <= 10 &&
                            !text.match(/昨天|前天|\\d+小时前|\\d+月\\d+日|\\d+天前/) &&
                            text !== title) {
                            source = text;
                            break;
                        }
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
        logger.info(f"   ✅ 百度成功解析 {len(results)} 条结果")
        return results[:30]

    async def _parse_news_results(self, page: Page) -> List[SearchResult]:
        """解析新闻搜索结果"""
        raw_results = await page.evaluate("""() => {
            const results = [];
            const newsItems = document.querySelectorAll('div[tpl="news-normal"]');

            newsItems.forEach(item => {
                try {
                    const url = item.getAttribute('mu') || '';
                    if (!url) return;

                    const h3 = item.querySelector('h3');
                    if (!h3) return;

                    const title = h3.innerText?.trim() || '';
                    if (!title) return;

                    // 提取时间
                    const timeElem = item.querySelector('span.c-color-gray2');
                    let timeStr = '';
                    if (timeElem) {
                        timeStr = timeElem.innerText?.trim().replace('发布于：', '') || '';
                    }

                    // 提取摘要
                    const summaryElem = item.querySelector('div.c-span-last > span.c-font-normal.c-color-text');
                    const summary = summaryElem ? summaryElem.innerText?.trim() || '' : '';

                    // 提取来源
                    const sourceElem = item.querySelector('div.news-source_Xj4Dv > a');
                    const source = sourceElem ? sourceElem.innerText?.trim() || '' : '';

                    results.push({title, url, summary, source, time: timeStr});
                } catch (e) {
                    // 忽略单个结果的解析错误
                }
            });

            return results;
        }""")

        # 转换为 SearchResult 对象
        results = [SearchResult(**r) for r in raw_results]
        logger.info(f"   ✅ 百度新闻成功解析 {len(results)} 条结果")
        return results[:30]
