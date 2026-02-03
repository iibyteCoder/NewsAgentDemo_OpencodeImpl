"""新浪新闻搜索引擎"""

from typing import List
from urllib.parse import quote

from loguru import logger
from playwright.async_api import Page

from .base import BaseEngine, EngineConfig, SearchResult


class SinaEngine(BaseEngine):
    """新浪新闻搜索引擎"""

    def __init__(self):
        config = EngineConfig(
            name="新浪新闻",
            search_url="https://search.sina.com.cn/",
            news_url="https://search.sina.com.cn/",
        )
        super().__init__(config)

    def get_resource_block_list(self) -> List[str]:
        """新浪需要保留样式表"""
        return ["image", "media"]

    def get_search_url(
        self, query: str, num_results: int = 30, search_type: str = "web"
    ) -> str:
        """构建搜索URL"""
        encoded_query = quote(query)
        # 新浪搜索使用 q 参数，并添加 c=news 指定新闻搜索
        return f"https://search.sina.com.cn/?q={encoded_query}&c=news&from=channel&ie=utf-8"

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
            await page.wait_for_selector("div#result", timeout=15000)
            await page.wait_for_timeout(2000)
        except Exception:
            logger.warning("   ⚠️ 新浪新闻页面加载超时，但继续尝试解析")

        # 解析结果
        raw_results = await page.evaluate(
            """() => {
            const results = [];
            const newsItems = document.querySelectorAll('div.box-result');

            newsItems.forEach(item => {
                try {
                    // 提取标题和链接
                    const titleElem = item.querySelector('h2 a');
                    if (!titleElem) return;

                    const title = titleElem.innerText ? titleElem.innerText.trim() : '';
                    const url = titleElem.getAttribute('href') || '';

                    if (!title || !url) return;

                    // 提取摘要
                    const summaryElem = item.querySelector('p.content');
                    const summary = summaryElem && summaryElem.innerText ? summaryElem.innerText.trim() : '';

                    // 提取来源和时间（在 span.fgray_time 中）
                    const timeElem = item.querySelector('span.fgray_time');
                    let source = '';
                    let time = '';

                    if (timeElem) {
                        const timeText = timeElem.innerText ? timeElem.innerText.trim() : '';
                        // 格式通常是 "来源   时间" 或 "来源\\n时间"，用多个空格或换行分隔
                        const parts = timeText.split(/\\s+/);
                        if (parts.length >= 2) {
                            // 第一部分是来源，最后部分是时间
                            source = parts[0];
                            time = parts[parts.length - 1];
                        } else {
                            time = timeText;
                        }
                    }

                    results.push({title, url, summary, source, time});
                } catch (e) {
                    // 忽略解析错误
                }
            });

            return results;
        }"""
        )

        # 转换为 SearchResult 对象
        results = [SearchResult(**r) for r in raw_results]
        logger.info(f"   ✅ 新浪新闻成功解析 {len(results)} 条结果")
        return results[:30]
