"""
测试反爬虫增强效果
"""

import sys
import io
import asyncio
import json

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from mcp_server.baidu_search.main import baidu_search, baidu_news_search


async def test_search():
    """测试搜索功能"""
    print("\n" + "="*60)
    print("测试 1: 百度搜索（带反爬虫增强）")
    print("="*60)

    result = await baidu_search(query="Python编程", num_results=10)
    data = json.loads(result)

    print(f"\n搜索完成，结果数: {data['total']}")
    if data['results']:
        print(f"第一个结果:")
        print(f"  标题: {data['results'][0]['title']}")
        print(f"  链接: {data['results'][0]['url'][:80]}...")
        print(f"  摘要: {data['results'][0]['summary'][:100]}...")
    else:
        print("未获取到结果")

    return data['total'] > 0


async def test_news():
    """测试新闻搜索"""
    print("\n" + "="*60)
    print("测试 2: 百度新闻搜索（带反爬虫增强）")
    print("="*60)

    result = await baidu_news_search(query="科技", num_results=10)
    data = json.loads(result)

    print(f"\n新闻搜索完成，结果数: {data['total']}")
    if data['results']:
        print(f"第一条新闻:")
        print(f"  标题: {data['results'][0]['title']}")
        print(f"  来源: {data['results'][0]['source']}")
        print(f"  时间: {data['results'][0]['time']}")
    else:
        print("未获取到结果")

    return data['total'] > 0


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("反爬虫增强测试")
    print("="*60)
    print("\n配置:")
    print("  - 并发数: 10")
    print("  - 随机延迟: 1-3秒")
    print("  - User-Agent 轮换: 7个不同UA")
    print("  - 浏览器反检测: 已增强")

    try:
        results = {
            "百度搜索": await test_search(),
            "百度新闻": await test_news(),
        }

        print("\n" + "="*60)
        print("测试结果汇总")
        print("="*60)

        for test_name, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"{status} - {test_name}")

        total_passed = sum(results.values())
        print(f"\n总计: {total_passed}/{len(results)} 测试通过")

        if total_passed == len(results):
            print("\n🎉 反爬虫增强成功！")
        else:
            print("\n⚠️ 部分测试失败，可能需要进一步调整")

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
