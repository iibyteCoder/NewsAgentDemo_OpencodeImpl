"""
调试百度新闻页面结构
"""

import sys
import io
import asyncio

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from mcp_server.baidu_search.config.settings import get_settings
from mcp_server.baidu_search.core import get_browser_pool
from mcp_server.baidu_search.utils.helpers import get_random_user_agent


async def main():
    settings = get_settings()
    browser_pool = get_browser_pool(settings)

    try:
        user_agent = get_random_user_agent()
        async with browser_pool.get_page(user_agent=user_agent) as page:
            url = "https://www.baidu.com/s?tn=news&rtt=1&bsst=1&cl=2&wd=%E4%BD%A0%E5%A5%BD"
            print(f"访问: {url}\n")

            await page.goto(url, timeout=30000)

            # 等待页面加载
            await asyncio.sleep(2)

            # 保存 HTML
            html_content = await page.content()

            # 保存到文件
            with open("baidu_news_debug.html", "w", encoding="utf-8") as f:
                f.write(html_content)

            print("✅ 已保存页面到 baidu_news_debug.html")

            # 调试：查看实际的选择器
            print("\n=== 调试信息 ===\n")

            debug_info = await page.evaluate("""() => {
                const info = {};

                // 检查各种选择器
                info['div[tpl="news-normal"] 数量'] = document.querySelectorAll('div[tpl="news-normal"]').length;

                // 检查第一个结果的结构
                const firstItem = document.querySelector('div[tpl="news-normal"]');
                if (firstItem) {
                    info['第一个结果的 HTML'] = firstItem.outerHTML.substring(0, 1000);

                    // 检查各种子元素
                    info['h3 数量'] = firstItem.querySelectorAll('h3').length;
                    info['h3 文本'] = firstItem.querySelector('h3')?.innerText || '';

                    info['span.c-color-gray2 数量'] = firstItem.querySelectorAll('span.c-color-gray2').length;
                    info['第一个 span.c-color-gray2'] = firstItem.querySelector('span.c-color-gray2')?.innerText || '';

                    info['div.news-source_Xj4Dv 数量'] = firstItem.querySelectorAll('div.news-source_Xj4Dv').length;
                    info['div.news-source_Xj4Dv > a 数量'] = firstItem.querySelectorAll('div.news-source_Xj4Dv > a').length;
                    info['div.news-source_Xj4Dv > a 文本'] = firstItem.querySelector('div.news-source_Xj4Dv > a')?.innerText || '';

                    info['div.c-row > span.c-font-normal.c-color-text 数量'] =
                        firstItem.querySelectorAll('div.c-row > span.c-font-normal.c-color-text').length;

                    // 列出所有 class
                    info['所有 div class'] = Array.from(firstItem.querySelectorAll('div'))
                        .map(d => d.className)
                        .filter(c => c)
                        .join(', ');

                    // 列出所有 span class
                    info['所有 span class'] = Array.from(firstItem.querySelectorAll('span'))
                        .map(s => s.className)
                        .filter(c => c)
                        .join(', ');
                }

                return info;
            }""")

            for key, value in debug_info.items():
                if key == "第一个结果的 HTML":
                    print(f"\n{key}:\n{value}\n")
                else:
                    print(f"{key}: {value}")

    finally:
        await browser_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
