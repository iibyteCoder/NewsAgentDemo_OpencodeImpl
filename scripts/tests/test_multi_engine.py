"""
测试多搜索引擎功能
"""

import sys
import io
import asyncio
import json

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from mcp_server.baidu_search.multi_engine import get_multi_engine
from mcp_server.baidu_search.browser_pool import get_browser_pool
from mcp_server.baidu_search.main import RateLimiter


async def test_all_engines():
    """测试所有搜索引擎"""
    print("\n" + "="*60)
    print("🔥 多搜索引擎测试")
    print("="*60)

    # 初始化
    browser_pool = get_browser_pool(
        max_concurrent=1,
        proxy={"server": "localhost:7897"}
    )
    rate_limiter = RateLimiter(max_requests=1, time_window=1.0)
    multi_engine = get_multi_engine(browser_pool, rate_limiter)

    test_query = "人工智能"
    test_results = {}

    try:
        # 测试百度搜索
        print("\n📊 测试 1: 百度搜索")
        result = await multi_engine.search(
            query=test_query,
            engine="baidu",
            num_results=10,
            search_type="web"
        )
        data = json.loads(result)
        test_results["百度"] = {
            "success": data.get("total", 0) > 0,
            "count": data.get("total", 0)
        }
        print(f"   结果数: {data.get('total', 0)}")
        if data.get("results"):
            print(f"   第一个结果: {data['results'][0]['title'][:50]}...")

        await asyncio.sleep(3)

        # 测试必应搜索
        print("\n📊 测试 2: 必应搜索")
        result = await multi_engine.search(
            query=test_query,
            engine="bing",
            num_results=10,
            search_type="web"
        )
        data = json.loads(result)
        test_results["必应"] = {
            "success": data.get("total", 0) > 0,
            "count": data.get("total", 0)
        }
        print(f"   结果数: {data.get('total', 0)}")
        if data.get("results"):
            print(f"   第一个结果: {data['results'][0]['title'][:50]}...")

        await asyncio.sleep(3)

        # 测试搜狗搜索
        print("\n📊 测试 3: 搜狗搜索")
        result = await multi_engine.search(
            query=test_query,
            engine="sogou",
            num_results=10,
            search_type="web"
        )
        data = json.loads(result)
        test_results["搜狗"] = {
            "success": data.get("total", 0) > 0,
            "count": data.get("total", 0)
        }
        print(f"   结果数: {data.get('total', 0)}")
        if data.get("results"):
            print(f"   第一个结果: {data['results'][0]['title'][:50]}...")

        await asyncio.sleep(3)

        # 测试随机引擎
        print("\n📊 测试 4: 随机引擎 (auto)")
        result = await multi_engine.search(
            query=test_query,
            engine="auto",
            num_results=10,
            search_type="web"
        )
        data = json.loads(result)
        engine_name = data.get("engine_name", "Unknown")
        test_results[f"随机({engine_name})"] = {
            "success": data.get("total", 0) > 0,
            "count": data.get("total", 0)
        }
        print(f"   使用的引擎: {engine_name}")
        print(f"   结果数: {data.get('total', 0)}")

        # 测试新闻搜索
        print("\n📊 测试 5: 必应新闻搜索")
        result = await multi_engine.search(
            query="科技",
            engine="bing",
            num_results=10,
            search_type="news"
        )
        data = json.loads(result)
        test_results["必应新闻"] = {
            "success": data.get("total", 0) > 0,
            "count": data.get("total", 0)
        }
        print(f"   结果数: {data.get('total', 0)}")

        # 打印总结
        print("\n" + "="*60)
        print("📊 测试结果总结")
        print("="*60)

        for engine, result in test_results.items():
            status = "✅ 成功" if result["success"] else "❌ 失败"
            print(f"{status} - {engine}: {result['count']} 条结果")

        total_success = sum(1 for r in test_results.values() if r["success"])
        print(f"\n总计: {total_success}/{len(test_results)} 测试通过")

        if total_success == len(test_results):
            print("\n🎉 所有搜索引擎测试通过！")
        else:
            print("\n⚠️ 部分引擎测试失败，可能需要调整配置")

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        await browser_pool.close()
        print("✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_all_engines())
