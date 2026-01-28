"""
调试搜索引擎页面解析
"""

import sys
import io
import asyncio

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from mcp_server.baidu_search.browser_pool import get_browser_pool


async def debug_engine(engine_name: str, url: str, selectors: list):
    """调试单个搜索引擎的页面结构"""
    print(f"\n{'='*60}")
    print(f"调试 {engine_name}")
    print(f"URL: {url}")
    print('='*60)

    browser_pool = get_browser_pool(
        max_concurrent=1,
        proxy={"server": "localhost:7897"}
    )

    try:
        async with browser_pool.get_page() as page:
            await page.goto(url, timeout=30000)
            await asyncio.sleep(3)

            # 获取页面标题
            title = await page.title()
            print(f"\n页面标题: {title}")

            # 测试各个选择器
            for selector_desc, selector in selectors:
                print(f"\n--- 测试选择器: {selector_desc} ---")
                print(f"CSS: {selector}")

                elements = await page.query_selector_all(selector)
                print(f"找到 {len(elements)} 个元素")

                if elements:
                    # 显示前3个元素的HTML结构
                    for i in range(min(3, len(elements))):
                        elem = elements[i]
                        print(f"\n  元素 {i+1}:")
                        print(f"    标签: {await elem.evaluate('e => e.tagName')}")

                        # 获取innerHTML的前200个字符
                        inner_html = await elem.inner_html()
                        print(f"    HTML: {inner_html[:200]}...")

                        # 尝试提取标题
                        title_elem = await elem.query_selector("h1, h2, h3, h4, a")
                        if title_elem:
                            text = await title_elem.inner_text()
                            print(f"    标题文本: {text[:100]}")

                        # 尝试提取链接
                        link_elem = await elem.query_selector("a[href]")
                        if link_elem:
                            href = await link_elem.get_attribute("href")
                            print(f"    链接: {href[:100]}")

    except Exception as e:
        print(f"\n❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser_pool.close()


async def main():
    """主调试函数"""
    print("\n" + "="*60)
    print("🔍 搜索引擎页面结构调试")
    print("="*60)

    test_query = "你好"

    debug_tasks = [
        ("百度新闻", f"https://www.baidu.com/s?rtt=1&bsst=1&cl=2&tn=news&ie=utf-8&word={test_query}", [
            ("结果容器", "div.result"),
            ("新闻容器", "div[class*='result']"),
            ("任意容器", "div"),
        ]),
        ("谷歌新闻", f"https://www.google.com/search?q={test_query}&tbm=nws", [
            ("Gx5Zad容器", "div[class*='Gx5Zad']"),
            ("xpd容器", "div[class*='xpd']"),
            ("新闻卡片", "div[class*='SoGUE']"),
        ]),
        ("搜狗新闻", f"https://www.sogou.com/news?query={test_query}", [
            ("结果容器", "div[class*='results']"),
            ("新闻容器", "div[class*='news']"),
            ("RB容器", "div.rb"),
            ("任意容器", "div"),
        ]),
    ]

    for engine_name, url, selectors in debug_tasks:
        await debug_engine(engine_name, url, selectors)
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
