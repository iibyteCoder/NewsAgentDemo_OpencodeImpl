"""新浪新闻搜索引擎"""

from typing import List

from loguru import logger
from playwright.async_api import Page

from .base import BaseEngine, EngineConfig, SearchResult


class SinaEngine(BaseEngine):
    """新浪新闻搜索引擎"""

    def __init__(self):
        config = EngineConfig(
            name="新浪新闻",
            search_url="https://search.sina.com.cn/?q={query}",
            news_url="https://news.sina.com.cn/roll/index.d.html?keyword={query}",
        )
        super().__init__(config)

    async def search(
        self,
        page: Page,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行新浪新闻搜索"""
        url = self.get_search_url(query, num_results, search_type)

        logger.info(f"   🌐 访问: {url}")
        await page.goto(url, timeout=30000)

        # 等待页面加载
        try:
            await page.wait_for_selector("div.blkContainer_01, dd, li.r", timeout=5000)
        except Exception:
            logger.warning("   ⚠️ 新浪新闻页面加载超时")
            return []

        # 解析结果
        raw_results = await page.evaluate("""() => {
            const results = [];
            const newsItems = document.querySelectorAll('dd, li.r, div.news-item');

            newsItems.forEach(item => {
                try {
                    const linkElem = item.querySelector('a');
                    if (!linkElem) return;

                    const title = linkElem.innerText?.trim() || '';
                    let url = linkElem.getAttribute('href') || '';

                    if (!title || !url) return;

                    // 提取摘要
                    const summaryElem = item.querySelector('p, div.summary');
                    const summary = summaryElem ? summaryElem.innerText?.trim() || '' : '';

                    // 提取来源
                    const sourceElem = item.querySelector('span.source, span.fgray, cite');
                    const source = sourceElem ? sourceElem.innerText?.trim() || '' : '新浪新闻';

                    // 提取时间
                    const timeElem = item.querySelector('span.date, span.fgray, span.time');
                    const time = timeElem ? timeElem.innerText?.trim() || '' : '';

                    results.push({title, url, summary, source, time});
                } catch (e) {
                    // 忽略单个结果的解析错误
                }
            });

            return results;
        }""")

        # 转换为 SearchResult 对象
        results = [SearchResult(**r) for r in raw_results]
        logger.info(f"   ✅ 新浪新闻成功解析 {len(results)} 条结果")
        return results[:30]
