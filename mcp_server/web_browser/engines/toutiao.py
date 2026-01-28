"""今日头条搜索引擎"""

from typing import List
from urllib.parse import quote

from loguru import logger
from playwright.async_api import Page

from .base import BaseEngine, EngineConfig, SearchResult


class ToutiaoEngine(BaseEngine):
    """今日头条搜索引擎"""

    def __init__(self):
        config = EngineConfig(
            name="今日头条",
            search_url="https://so.toutiao.com/search?dvpf=pc&keyword={query}&pd=information",
            news_url="https://so.toutiao.com/search?dvpf=pc&keyword={query}&pd=information&from=news",
        )
        super().__init__(config)

    def get_search_url(self, query: str, num_results: int = 30, search_type: str = "web") -> str:
        """构建搜索URL"""
        encoded_query = quote(query)
        # 今日头条搜索使用keyword参数
        return f"https://so.toutiao.com/search?dvpf=pc&keyword={encoded_query}&pd=information&from=news&page_num=0"

    async def search(
        self,
        page: Page,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行今日头条搜索"""
        url = self.get_search_url(query, num_results, search_type)

        logger.info(f"   🌐 访问: {url}")
        await page.goto(url, timeout=30000)

        # 等待页面加载
        try:
            await page.wait_for_selector("div.result-content", timeout=5000)
        except Exception:
            logger.warning("   ⚠️ 今日头条页面加载超时")
            return []

        # 解析结果
        raw_results = await page.evaluate("""() => {
            const results = [];
            const newsItems = document.querySelectorAll('div.result-content');

            newsItems.forEach(item => {
                try {
                    const linkElem = item.querySelector('a[href*="/search/jump"]');
                    if (!linkElem) return;

                    const titleElem = item.querySelector('.cs-header a');
                    const title = titleElem ? titleElem.innerText?.trim() || '' : '';
                    let url = linkElem.getAttribute('href') || '';

                    if (!title || !url) return;

                    // URL解码（今日头条使用jump URL）
                    try {
                        const urlObj = new URL(url, window.location.href);
                        const jumpUrl = urlObj.searchParams.get('url');
                        if (jumpUrl) {
                            url = decodeURIComponent(jumpUrl);
                        }
                    } catch (e) {
                        // 如果解码失败，保持原URL
                    }

                    // 提取摘要
                    const textElem = item.querySelector('.cs-text span');
                    const summary = textElem ? textElem.innerText?.trim() || '' : '';

                    // 提取来源和时间
                    const sourceContent = item.querySelector('.cs-source-content');
                    let source = '';
                    let time = '';

                    if (sourceContent) {
                        const spans = sourceContent.querySelectorAll('span.text-ellipsis');
                        if (spans.length >= 2) {
                            source = spans[0].innerText?.trim() || '';
                            time = spans[1].innerText?.trim() || '';
                        } else if (spans.length === 1) {
                            source = spans[0].innerText?.trim() || '';
                        }
                    }

                    results.push({title, url, summary, source, time});
                } catch (e) {
                    // 忽略单个结果的解析错误
                }
            });

            return results;
        }""")

        # 转换为 SearchResult 对象
        results = [SearchResult(**r) for r in raw_results]
        logger.info(f"   ✅ 今日头条成功解析 {len(results)} 条结果")
        return results[:30]
