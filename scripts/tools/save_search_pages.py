"""
保存搜索引擎页面demo

用于保存各个搜索引擎的实际页面，方便分析页面结构并调整解析逻辑
"""

import sys
import io
import asyncio
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from mcp_server.baidu_search.browser_pool import get_browser_pool


# 创建输出目录
OUTPUT_DIR = Path("search_engine_demos")
OUTPUT_DIR.mkdir(exist_ok=True)


async def save_search_page(engine_name: str, url: str, search_type: str):
    """保存搜索引擎页面"""
    print(f"\n{'='*60}")
    print(f"📄 保存 {engine_name} {search_type} 搜索页面")
    print(f"   URL: {url}")
    print(f"{'='*60}")

    # 初始化浏览器池
    browser_pool = get_browser_pool(
        max_concurrent=1,
        proxy={"server": "localhost:7897"}
    )

    try:
        async with browser_pool.get_page() as page:
            # 访问搜索页面
            print(f"🌐 正在访问...")
            await page.goto(url, timeout=30000)

            # 等待页面加载
            await asyncio.sleep(3)

            # 获取页面标题
            title = await page.title()
            print(f"📋 页面标题: {title}")

            # 获取页面HTML
            html = await page.content()

            # 保存到文件
            filename = OUTPUT_DIR / f"{engine_name}_{search_type}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)

            print(f"✅ 已保存到: {filename}")
            print(f"   文件大小: {len(html)} 字符")

            # 同时保存页面截图
            screenshot_path = OUTPUT_DIR / f"{engine_name}_{search_type}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"📸 截图已保存: {screenshot_path}")

            return True

    except Exception as e:
        print(f"❌ 保存失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await browser_pool.close()


async def save_all_search_pages():
    """保存所有搜索引擎的页面demo"""
    print("\n" + "="*60)
    print("🔥 搜索引擎页面demo保存工具")
    print("="*60)
    print(f"\n输出目录: {OUTPUT_DIR.absolute()}")

    # 搜索引擎URL配置（只保留新闻搜索）
    search_engines = {
        "百度": {
            "news": "https://www.baidu.com/s?rtt=1&bsst=1&cl=2&tn=news&ie=utf-8&word=%E4%BD%A0%E5%A5%BD",
        },
        # "搜狗": {
        #     "news": "https://www.sogou.com/sogou?ie=utf8&p=40230447&interation=1728053249&interV=&pid=sogou-wsse-8f646834ef1adefa&query=%E4%BD%A0%E5%A5%BD",
        # },
        # "必应": {
        #     "news": "https://www.bing.com/news/search?q=%E4%BD%A0%E5%A5%BD",
        # },
        # "谷歌": {
        #     "news": "https://www.google.com/search?q=%E4%BD%A0%E5%A5%BD&tbm=nws",
        # },
    }

    success_count = 0
    total_count = 0

    # 遍历所有搜索引擎
    for engine_name, urls in search_engines.items():
        for search_type, url in urls.items():
            total_count += 1
            success = await save_search_page(engine_name, url, search_type)
            if success:
                success_count += 1

            # 等待一下，避免请求过快
            await asyncio.sleep(3)

    # 打印总结
    print("\n" + "="*60)
    print("📊 保存总结")
    print("="*60)
    print(f"成功: {success_count}/{total_count}")
    print(f"输出目录: {OUTPUT_DIR.absolute()}")

    if success_count == total_count:
        print("\n✅ 所有页面保存成功！")
        print("\n📋 下一步：")
        print("1. 查看保存的HTML文件，分析页面结构")
        print("2. 查看截图，了解页面布局")
        print("3. 告诉我页面结构，我将调整解析逻辑")
    else:
        print("\n⚠️ 部分页面保存失败，请检查网络连接")


async def save_custom_search_page(engine_name: str, url: str, search_type: str = "web"):
    """保存自定义搜索页面"""
    await save_search_page(engine_name, url, search_type)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 自定义URL模式
        if len(sys.argv) >= 3:
            engine = sys.argv[1]
            url = sys.argv[2]
            search_type = sys.argv[3] if len(sys.argv) > 3 else "web"
            asyncio.run(save_custom_search_page(engine, url, search_type))
        else:
            print("用法: python save_search_pages.py <引擎名> <URL> [搜索类型]")
            print("示例: python save_search_pages.py 百度 'https://www.baidu.com/s?wd=test' web")
    else:
        # 默认：保存所有搜索引擎
        asyncio.run(save_all_search_pages())
