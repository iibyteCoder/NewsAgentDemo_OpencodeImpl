"""腾讯新闻搜索引擎"""

from typing import List
from urllib.parse import quote

from loguru import logger
from playwright.async_api import Page

from .base import BaseEngine, EngineConfig, SearchResult


class TencentEngine(BaseEngine):
    """腾讯新闻搜索引擎"""

    def __init__(self):
        config = EngineConfig(
            name="腾讯新闻",
            search_url="https://news.qq.com/search?query={query}&page=1",
            news_url="https://news.qq.com/search?query={query}&page=1",
        )
        super().__init__(config)

    def get_search_url(self, query: str, num_results: int = 30, search_type: str = "web") -> str:
        """构建搜索URL"""
        encoded_query = quote(query)
        # 腾讯新闻搜索使用query参数
        return f"https://news.qq.com/search?query={encoded_query}&page=1"

    async def search(
        self,
        page: Page,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行腾讯新闻搜索"""
        url = self.get_search_url(query, num_results, search_type)

        logger.info(f"   🌐 访问: {url}")
        await page.goto(url, timeout=30000)

        # 等待页面加载
        try:
            await page.wait_for_selector("div.img-text-card", timeout=5000)
        except Exception:
            logger.warning("   ⚠️ 腾讯新闻页面加载超时")
            return []

        # 解析结果
        raw_results = await page.evaluate("""() => {
            const results = [];
            const newsItems = document.querySelectorAll('div.img-text-card');

            newsItems.forEach(item => {
                try {
                    const linkElem = item.querySelector('a');
                    if (!linkElem) return;

                    const titleElem = item.querySelector('p.title');
                    const title = titleElem ? titleElem.innerText?.trim() || '' : '';
                    let url = linkElem.getAttribute('href') || '';

                    if (!title || !url) return;

                    // 提取摘要
                    const descElem = item.querySelector('p.description');
                    const summary = descElem ? descElem.innerText?.trim() || '' : '';

                    // 提取来源
                    const authorElem = item.querySelector('span.author');
                    const source = authorElem ? authorElem.innerText?.trim() || '' : '腾讯新闻';

                    // 提取时间
                    const timeElem = item.querySelector('span.time');
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
        logger.info(f"   ✅ 腾讯新闻成功解析 {len(results)} 条结果")
        return results[:30]
