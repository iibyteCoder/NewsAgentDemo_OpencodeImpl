"""
测试谷歌解析器的具体逻辑
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


async def test_google_parser_logic():
    """测试谷歌解析器逻辑"""
    url = "https://www.google.com/search?q=你好&tbm=nws"

    print(f"\n测试谷歌解析器逻辑")
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

            results = []
            for i, element in enumerate(elements[:5]):
                print(f"\n{'='*60}")
                print(f"处理元素 {i+1}")
                print('='*60)

                try:
                    # 1. 提取链接
                    link_elem = await element.query_selector("a[href]")
                    if not link_elem:
                        print("❌ 未找到链接 - 跳过")
                        continue

                    url_raw = await link_elem.get_attribute("href")
                    print(f"原始URL: {url_raw[:80] if url_raw else 'None'}...")

                    # 解析URL
                    url_final = url_raw
                    if url_raw and url_raw.startswith("/url?q="):
                        url_part = url_raw[6:]
                        if "&sa=" in url_part:
                            real_url = url_part.split("&sa=")[0]
                            if real_url.startswith('='):
                                real_url = real_url[1:]
                            url_final = unquote(real_url)
                            print(f"解析后URL: {url_final[:80]}...")

                    # 2. 提取标题
                    title_elem = await element.query_selector("h3")
                    if not title_elem:
                        title_elem = await element.query_selector("div[class*='ilUpNd']")

                    if not title_elem:
                        print("❌ 未找到标题 - 跳过")
                        continue

                    title = await title_elem.inner_text()
                    print(f"✅ 标题: {title[:60]}...")

                    # 3. 提取内容
                    summary = ""
                    source = ""
                    time_str = ""

                    content_elem = await element.query_selector("div[class*='DnJfK']")
                    if content_elem:
                        content_text = await content_elem.inner_text()
                        lines = [line.strip() for line in content_text.split('\n') if line.strip()]

                        print(f"内容行数: {len(lines)}")
                        for j, line in enumerate(lines[:3]):
                            print(f"  行{j+1}: {line[:60]}")

                        if len(lines) >= 2 and lines[0] != title.strip():
                            source = lines[0]

                        if len(lines) >= 3:
                            time_str = lines[1]
                            summary = ' '.join(lines[2:])
                        elif len(lines) == 2:
                            summary = lines[1]

                    print(f"来源: {source}")
                    print(f"时间: {time_str}")
                    print(f"摘要: {summary[:60] if summary else '无'}...")

                    # 4. 添加到结果
                    results.append({
                        "title": title.strip(),
                        "url": url_final if url_final else "",
                        "summary": summary.strip(),
                        "source": source.strip(),
                        "time": time_str.strip(),
                    })

                    print(f"✅ 成功添加到结果列表")

                except Exception as e:
                    print(f"❌ 处理失败: {e}")
                    import traceback
                    traceback.print_exc()

            print(f"\n{'='*60}")
            print(f"最终结果: {len(results)} 条")
            print('='*60)

            for i, result in enumerate(results):
                print(f"\n{i+1}. {result['title']}")
                print(f"   链接: {result['url'][:60]}...")
                print(f"   来源: {result['source']}")
                print(f"   时间: {result['time']}")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser_pool.close()


if __name__ == "__main__":
    asyncio.run(test_google_parser_logic())
