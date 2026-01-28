"""
测试百度搜索 MCP Server

验证所有工具是否正常工作
"""

import sys
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import json
from mcp_server.baidu_search.main import (
    baidu_search,
    baidu_news_search,
    baidu_hot_search,
    fetch_article_content,
)


async def test_baidu_search():
    """测试百度搜索"""
    print("\n" + "=" * 50)
    print("测试 1: 百度搜索")
    print("=" * 50)

    result = await baidu_search(query="人工智能", num_results=5)
    data = json.loads(result)

    print(f"✅ 搜索完成，共 {data['total']} 个结果")
    if data['results']:
        print(f"   第一个结果: {data['results'][0]['title'][:50]}...")
    else:
        print("   ⚠️ 未获取到结果")
    return data['total'] > 0


async def test_baidu_news_search():
    """测试百度新闻搜索"""
    print("\n" + "=" * 50)
    print("测试 2: 百度新闻搜索")
    print("=" * 50)

    result = await baidu_news_search(query="科技", num_results=5)
    data = json.loads(result)

    print(f"✅ 新闻搜索完成，共 {data['total']} 条新闻")
    if data['results']:
        print(f"   第一条: {data['results'][0]['title'][:50]}...")
    else:
        print("   ⚠️ 未获取到结果")
    return data['total'] > 0


async def test_baidu_hot_search():
    """测试百度热搜榜"""
    print("\n" + "=" * 50)
    print("测试 3: 百度热搜榜")
    print("=" * 50)

    result = await baidu_hot_search()
    data = json.loads(result)

    print(f"✅ 热搜榜获取完成，共 {data['total']} 条热搜")
    if data['hot_items']:
        print(f"   热搜第一: {data['hot_items'][0]['title']}")
    else:
        print("   ⚠️ 未获取到热搜")
    return data['total'] > 0


async def test_fetch_article():
    """测试获取文章内容"""
    print("\n" + "=" * 50)
    print("测试 4: 获取文章内容")
    print("=" * 50)

    # 先搜索一篇文章
    search_result = await baidu_search(query="Python教程", num_results=3)
    search_data = json.loads(search_result)

    if search_data['results']:
        # 获取第一篇文章
        url = search_data['results'][0]['url']
        print(f"   正在获取文章: {url[:60]}...")

        article_result = await fetch_article_content(url)
        article_data = json.loads(article_result)

        print(f"✅ 文章获取完成")
        print(f"   标题: {article_data.get('title', '无')[:50]}...")
        print(f"   内容长度: {article_data.get('content_length', 0)} 字符")
        return article_data.get('content_length', 0) > 0
    else:
        print("   ⚠️ 搜索无结果，跳过文章获取测试")
        return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("🚀 开始测试 MCP Server")
    print("=" * 50)

    try:
        results = {
            "百度搜索": await test_baidu_search(),
            "百度新闻搜索": await test_baidu_news_search(),
            "百度热搜榜": await test_baidu_hot_search(),
            "获取文章内容": await test_fetch_article(),
        }

        print("\n" + "=" * 50)
        print("📊 测试结果汇总")
        print("=" * 50)

        for test_name, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"{status} - {test_name}")

        total_passed = sum(results.values())
        total_tests = len(results)
        print(f"\n总计: {total_passed}/{total_tests} 测试通过")

        if total_passed == total_tests:
            print("\n🎉 所有测试通过！MCP Server 工作正常！")
        else:
            print("\n⚠️ 部分测试失败，请检查配置和网络连接")

    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
