"""搜狐新闻搜索引擎"""

from typing import List
from urllib.parse import quote

from loguru import logger
from playwright.async_api import Page

from .base import BaseEngine, EngineConfig, SearchResult


class SohuEngine(BaseEngine):
    """搜狐新闻搜索引擎"""

    def __init__(self):
        config = EngineConfig(
            name="搜狐新闻",
            search_url="https://search.sohu.com/?keyword={query}&type=10002",
            news_url="https://search.sohu.com/?keyword={query}&type=10002",
        )
        super().__init__(config)

    def get_search_url(self, query: str, num_results: int = 30, search_type: str = "web") -> str:
        """构建搜索URL"""
        encoded_query = quote(query)
        # 搜狐搜索使用keyword参数，type=10002表示新闻
        return f"https://search.sohu.com/?keyword={encoded_query}&type=10002&ie=utf8"

    async def search(
        self,
        page: Page,
        query: str,
        num_results: int = 30,
        search_type: str = "web",
    ) -> List[SearchResult]:
        """执行搜狐新闻搜索"""
        url = self.get_search_url(query, num_results, search_type)

        logger.info(f"   🌐 访问: {url}")
        await page.goto(url, timeout=30000)

        # 等待页面加载
        try:
            await page.wait_for_selector("div.cards-small-img", timeout=5000)
        except Exception:
            logger.warning("   ⚠️ 搜狐新闻页面加载超时")
            return []

        # 搜狐使用滚动加载，需要滚动页面来加载更多结果
        max_scroll_attempts = 10  # 最大滚动次数
        scroll_pause_time = 1500  # 每次滚动后等待时间（毫秒）

        for attempt in range(max_scroll_attempts):
            # 检查当前已加载的结果数量
            current_count = await page.evaluate("""() => {
                return document.querySelectorAll('div.cards-small-img').length;
            }""")

            logger.info(f"   📜 滚动加载 (第{attempt + 1}次): 已加载 {current_count} 条结果")

            # 如果已获取足够结果，停止滚动
            if current_count >= num_results:
                logger.info(f"   ✅ 已获取足够结果 ({current_count} 条)")
                break

            # 滚动到页面底部
            await page.evaluate("""() => {
                window.scrollTo(0, document.body.scrollHeight);
            }""")

            # 等待新数据加载
            await page.wait_for_timeout(scroll_pause_time)

            # 检查是否有新数据加载
            new_count = await page.evaluate("""() => {
                return document.querySelectorAll('div.cards-small-img').length;
            }""")

            # 如果没有新数据，说明已经到底了
            if new_count == current_count:
                logger.info("   ✅ 已到达页面底部")
                break

        # 解析结果
        raw_results = await page.evaluate("""() => {
            const results = [];
            const newsItems = document.querySelectorAll('div.cards-small-img');

            newsItems.forEach(item => {
                try {
                    const titleElem = item.querySelector('.cards-content-title a');
                    if (!titleElem) return;

                    const title = titleElem.innerText?.trim() || '';
                    const url = titleElem.getAttribute('href') || '';

                    if (!title || !url) return;

                    // 提取摘要
                    const descElem = item.querySelector('.cards-content-right-desc a');
                    const summary = descElem ? descElem.innerText?.trim() || '' : '';

                    // 提取来源和时间
                    const commElem = item.querySelector('.cards-content-right-comm');
                    let source = '搜狐新闻';
                    let time = '';

                    if (commElem) {
                        const commText = commElem.innerText?.trim() || '';
                        // 移除多余空白
                        const cleanText = commText.replace(/\\s+/g, ' ');

                        // 来源通常是第一个非空部分
                        const parts = cleanText.split(/\\d+小时前|\\d+天前|\\d{4}-\\d{2}-\\d{2}/);
                        if (parts.length > 0) {
                            source = parts[0].trim() || '搜狐新闻';
                        }

                        // 提取时间
                        const timeMatch = cleanText.match(/(\\d+小时前|\\d+天前|\\d{4}-\\d{2}-\\d{2})/);
                        if (timeMatch) {
                            time = timeMatch[1];
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
        logger.info(f"   ✅ 搜狐新闻成功解析 {len(results)} 条结果")
        return results[:30]
