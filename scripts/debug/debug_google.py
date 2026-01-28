"""
专门调试谷歌解析器
"""

import sys
import io
import asyncio
from urllib.parse import unquote

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from mcp_server.baidu_search.browser_pool import get_browser_pool


async def debug_google():
    """调试谷歌新闻解析"""
    url = "https://www.google.com/search?q=你好&tbm=nws"

    print(f"\n调试谷歌新闻解析")
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

            # 获取所有Gx5Zad元素
            elements = await page.query_selector_all("div[class*='Gx5Zad']")
            print(f"\n找到 {len(elements)} 个 Gx5Zad 元素")

            for i, element in enumerate(elements[:3]):
                print(f"\n{'='*60}")
                print(f"元素 {i+1}")
                print('='*60)

                # 1. 查找链接
                link_elem = await element.query_selector("a[href]")
                if link_elem:
                    url_raw = await link_elem.get_attribute("href")
                    print(f"原始链接: {url_raw[:100] if url_raw else 'None'}...")

                    # 解析URL
                    if url_raw and url_raw.startswith("/url?q="):
                        url_part = url_raw[6:]  # 移除 "/url?q="
                        if "&sa=" in url_part:
                            real_url = url_part.split("&sa=")[0]
                            url_parsed = unquote(real_url)
                            print(f"解析后URL: {url_parsed[:100]}...")
                else:
                    print("未找到链接")
                    continue

                # 2. 查找标题 - 尝试多种方式
                print(f"\n查找标题:")

                # 方式1: h3
                h3_elem = await element.query_selector("h3")
                if h3_elem:
                    h3_text = await h3_elem.inner_text()
                    print(f"  h3: {h3_text}")
                else:
                    print(f"  h3: 未找到")

                # 方式2: div[class*='ilUpNd']
                ilupnd_elem = await element.query_selector("div[class*='ilUpNd']")
                if ilupnd_elem:
                    ilupnd_text = await ilupnd_elem.inner_text()
                    print(f"  div.ilUpNd: {ilupnd_text}")
                else:
                    print(f"  div.ilUpNd: 未找到")

                # 方式3: 直接从a标签获取
                if link_elem:
                    link_text = await link_elem.inner_text()
                    print(f"  a标签文本: {link_text[:100]}...")

                # 3. 查找内容区域
                print(f"\n查找内容区域:")

                content_elem = await element.query_selector("div[class*='DnJfK']")
                if content_elem:
                    content_text = await content_elem.inner_text()
                    print(f"  div.DnJfK: {content_text[:200]}...")

                    # 分割文本
                    lines = [line.strip() for line in content_text.split('\n') if line.strip()]
                    print(f"  分割后行数: {len(lines)}")
                    for j, line in enumerate(lines):
                        print(f"    行{j+1}: {line[:80]}")

                # 4. 显示完整HTML
                print(f"\n完整HTML (前500字符):")
                html = await element.inner_html()
                print(html[:500])

    except Exception as e:
        print(f"\n❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser_pool.close()


if __name__ == "__main__":
    asyncio.run(debug_google())
