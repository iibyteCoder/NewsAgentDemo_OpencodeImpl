"""
测试各搜索引擎新闻解析器 - 重构版
"""

import sys
import io
import asyncio

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 使用新的模块结构
from mcp_server.baidu_search.config.settings import get_settings
from mcp_server.baidu_search.core import get_browser_pool, RateLimiter
from mcp_server.baidu_search.engines import EngineFactory
from mcp_server.baidu_search.utils.helpers import get_random_user_agent, search_result_to_dict


async def test_engine_news(engine_name: str, query: str):
    """测试单个搜索引擎的新闻解析"""
    print(f"\n{'='*60}")
    print(f"测试 {engine_name} 新闻搜索")
    print(f"关键词: {query}")
    print('='*60)

    # 初始化
    settings = get_settings()
    browser_pool = get_browser_pool(settings)
    rate_limiter = RateLimiter(
        time_window=settings.rate_limit_time_window,
        max_domain_requests=settings.max_domain_requests_per_second,
        max_engine_requests=settings.max_engine_requests_per_second,
    )
    engine_factory = EngineFactory(enabled_engines=settings.enabled_engines)

    try:
        # 获取引擎
        engine = engine_factory.get_engine(engine_name)
        if not engine:
            print(f"\n❌ 引擎 {engine_name} 不可用")
            return False

        # 应用速率限制
        search_url = engine.get_search_url(query, 10, "news")
        domain = engine.extract_domain(search_url)
        await rate_limiter.acquire(domain=domain, engine=engine_name)

        # 执行搜索
        user_agent = get_random_user_agent()
        async with browser_pool.get_page(user_agent=user_agent) as page:
            await page.goto(search_url, timeout=30000)

            # 解析结果
            results = await engine.search(page, query, 10, "news")

            # 转换为字典
            results_dict = [search_result_to_dict(r) for r in results]

            print(f"\n引擎: {engine.config.name}")
            print(f"查询: {query}")
            print(f"结果数量: {len(results_dict)}")

            # 显示前5条结果
            print(f"\n前5条结果:")
            print(f"{'-'*60}")

            for i, item in enumerate(results_dict[:5], 1):
                print(f"\n{i}. {item.get('title', 'N/A')}")
                print(f"   来源: {item.get('source', 'N/A')}")
                print(f"   时间: {item.get('time', 'N/A')}")
                url = item.get('url', 'N/A')
                print(f"   链接: {url[:80] if url != 'N/A' else 'N/A'}...")
                if item.get('summary'):
                    print(f"   摘要: {item['summary'][:100]}...")

            return len(results_dict) > 0

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await browser_pool.close()


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🔥 搜索引擎新闻解析器测试")
    print("="*60)

    test_query = "你好"

    engines = [
        # "baidu",
        # "bing",
        # "google",
        # "sogou",
        "360",
    ]

    success_count = 0
    total_count = len(engines)

    for engine in engines:
        success = await test_engine_news(engine, test_query)
        if success:
            success_count += 1

        # 等待一下，避免请求过快
        await asyncio.sleep(3)

    # 打印总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    print(f"成功: {success_count}/{total_count}")

    if success_count == total_count:
        print("\n✅ 所有引擎测试通过！")
    else:
        print(f"\n⚠️ {total_count - success_count} 个引擎测试失败")


if __name__ == "__main__":
    asyncio.run(main())
