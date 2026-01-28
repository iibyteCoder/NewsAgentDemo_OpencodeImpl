#!/usr/bin/env python
"""
测试 MCP Server 工具是否正常工作
"""
import sys
import io
import json
import asyncio

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from mcp_server.web_browser.tools.search_tools import (
    baidu_news_search,
    multi_search,
    fetch_article_content,
    baidu_hot_search
)

async def test_search():
    """测试搜索功能"""
    print("=" * 60)
    print("测试1: 百度新闻搜索 - '人工智能最新进展'")
    print("=" * 60)

    result_json = await baidu_news_search("人工智能最新进展", 5)
    result = json.loads(result_json)
    print(f"\n搜索结果: {len(result.get('results', []))} 条新闻\n")

    for i, news in enumerate(result.get('results', [])[:3], 1):
        print(f"{i}. {news.get('title')}")
        print(f"   来源: {news.get('source')}")
        print(f"   链接: {news.get('url')}")
        print(f"   摘要: {news.get('summary', '')[:100]}...")
        print()

    return result

async def test_fetch_content(url):
    """测试内容获取功能"""
    print("=" * 60)
    print("测试2: 获取文章完整内容")
    print("=" * 60)

    result_json = await fetch_article_content(url)
    result = json.loads(result_json)
    print(f"\n标题: {result.get('title')}")
    print(f"内容长度: {result.get('content_length')} 字符")
    print(f"\n内容预览:\n{result.get('content', '')[:300]}...")

    return result

async def test_hot_search():
    """测试热搜榜功能"""
    print("\n" + "=" * 60)
    print("测试3: 百度热搜榜")
    print("=" * 60)

    result_json = await baidu_hot_search()
    result = json.loads(result_json)
    print(f"\n热搜总数: {result.get('total')}")

    print("\n前10名热点:")
    for item in result.get('hot_items', [])[:10]:
        print(f"  {item.get('rank')}. {item.get('title')} (热度: {item.get('hot_score')})")

    return result

async def main():
    """主测试函数"""
    try:
        # 测试搜索
        search_result = await test_search()

        # 获取第一条新闻的完整内容
        if search_result.get('results'):
            first_url = search_result['results'][0].get('url')
            await test_fetch_content(first_url)

        # 测试热搜榜
        await test_hot_search()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成！MCP Server 工具运行正常")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
