"""网易新闻搜索引擎"""

from typing import List
from urllib.parse import quote

from loguru import logger
from playwright.async_api import Page

from .base import BaseEngine, EngineConfig, SearchResult


class WangyiEngine(BaseEngine):
    """网易新闻搜索引擎"""

    def __init__(self):
        config = EngineConfig(
            name="网易新闻",
            search_url="https://www.163.com/search?keyword={query}",
            news_url="https://www.163.com/search?keyword={query}",
        )
        super().__init__(config)

    def get_resource_block_list(self) -> List[str]:
        """网易可以拦截更多资源以加快速度"""
        return []

    def get_search_url(self, query: str, num_results: int = 30, search_type: str = "web") -> str:
        """构建搜索URL"""
        encoded_query = quote(query)
        # 网易搜索使用keyword参数
        return f"https://www.163.com/search?keyword={encoded_query}"

    async def search(
        self,
        page: Page,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行网易新闻搜索"""
        url = self.get_search_url(query, num_results, search_type)

        logger.info(f"   🌐 访问: {url}")
        await page.goto(url, timeout=30000)

        # 等待页面加载
        try:
            await page.wait_for_selector("div.keyword_new", timeout=5000)
        except Exception:
            logger.warning("   ⚠️ 网易新闻页面加载超时")
            return []

        # 解析结果
        raw_results = await page.evaluate("""() => {
            const results = [];
            const newsItems = document.querySelectorAll('div.keyword_new');

            newsItems.forEach(item => {
                try {
                    const titleElem = item.querySelector('h3 a');
                    if (!titleElem) return;

                    const title = titleElem.innerText?.trim() || '';
                    const url = titleElem.getAttribute('href') || '';

                    if (!title || !url) return;

                    // 提取来源
                    const sourceElem = item.querySelector('div.keyword_source');
                    const source = sourceElem ? sourceElem.innerText?.trim() || '' : '网易新闻';

                    // 提取时间
                    const timeElem = item.querySelector('div.keyword_time');
                    const time = timeElem ? timeElem.innerText?.trim() || '' : '';

                    // 网易新闻搜索没有明显的摘要字段，使用空字符串
                    const summary = '';

                    results.push({title, url, summary, source, time});
                } catch (e) {
                    // 忽略单个结果的解析错误
                }
            });

            return results;
        }""")

        # 转换为 SearchResult 对象
        results = [SearchResult(**r) for r in raw_results]
        logger.info(f"   ✅ 网易新闻成功解析 {len(results)} 条结果")
        return results[:30]
