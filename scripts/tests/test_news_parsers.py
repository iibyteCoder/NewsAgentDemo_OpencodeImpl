"""
测试各搜索引擎新闻解析器 - 完整测试版

测试覆盖：
- 10个搜索引擎（百度、必应、搜狗、谷歌、360、今日头条、腾讯、网易、新浪、搜狐）
- 反爬虫检测
- 自动禁用机制
- 多引擎智能搜索
"""

import sys
import io
import asyncio
import time

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 使用新的模块结构
from mcp_server.web_browser.config.settings import get_settings
from mcp_server.web_browser.core import get_browser_pool, RateLimiter
from mcp_server.web_browser.engines.factory import EngineFactory
from mcp_server.web_browser.engines.base import SearchResult
from mcp_server.web_browser.tools.search_tools import (
    multi_search,
    _check_anti_bot,
)
from mcp_server.web_browser.utils.helpers import get_random_user_agent, search_result_to_dict

from loguru import logger
from playwright.async_api import Page


# ==================== 测试单个搜索引擎 ====================

async def test_engine_news(engine_name: str, query: str, num_results: int = 10):
    """测试单个搜索引擎的新闻解析

    Args:
        engine_name: 引擎名称
        query: 搜索关键词
        num_results: 返回结果数量

    Returns:
        (是否成功, 结果数量, 耗时秒数)
    """
    print(f"\n{'='*70}")
    print(f"🔍 测试 {engine_name.upper()} 新闻搜索")
    print(f"关键词: {query}")
    print('='*70)

    start_time = time.time()

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
        # 检查引擎是否被禁用
        if engine_factory.is_engine_banned(engine_name):
            print(f"\n⚠️ 引擎 {engine_name} 当前被禁用")
            return False, 0, 0

        # 获取引擎
        engine = engine_factory.get_engine(engine_name)
        if not engine:
            print(f"\n❌ 引擎 {engine_name} 不可用（可能未启用）")
            return False, 0, 0

        print(f"✅ 引擎名称: {engine.config.name}")

        # 应用速率限制
        search_url = engine.get_search_url(query, num_results, "news")
        domain = engine.extract_domain(search_url)
        await rate_limiter.acquire(domain=domain, engine=engine_name)

        # 执行搜索
        user_agent = get_random_user_agent()
        async with browser_pool.get_page(user_agent=user_agent) as page:
            print(f"📡 访问URL: {search_url[:80]}...")
            await page.goto(search_url, timeout=30000)

            # 反爬虫检测
            print(f"🔍 执行反爬虫检测...")
            is_blocked, block_reason = await _check_anti_bot(page, search_url)
            if is_blocked:
                print(f"\n🚨 检测到反爬虫拦截: {block_reason}")
                # 禁用该引擎
                engine_factory.ban_engine(engine_name, block_reason)
                return False, 0, 0

            print(f"✅ 反爬虫检测通过")

            # 解析结果
            results = await engine.search(page, query, num_results, "news")

            # 转换为字典
            results_dict = [search_result_to_dict(r) for r in results]

            elapsed = time.time() - start_time

            print(f"\n📊 测试结果:")
            print(f"   结果数量: {len(results_dict)}/{num_results}")
            print(f"   耗时: {elapsed:.2f}秒")

            # 显示前3条结果
            if results_dict:
                print(f"\n📰 前3条结果:")
                print(f"{'-'*70}")

                for i, item in enumerate(results_dict[:3], 1):
                    print(f"\n{i}. {item.get('title', 'N/A')}")
                    print(f"   来源: {item.get('source', 'N/A')}")
                    print(f"   时间: {item.get('time', 'N/A')}")
                    url = item.get('url', 'N/A')
                    print(f"   链接: {url[:70] if url != 'N/A' else 'N/A'}...")
                    if item.get('summary'):
                        print(f"   摘要: {item['summary'][:80]}...")

            return len(results_dict) > 0, len(results_dict), elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, elapsed

    finally:
        await browser_pool.close()


# ==================== 测试所有搜索引擎 ====================

async def test_all_engines():
    """测试所有10个搜索引擎"""
    print("\n" + "="*70)
    print("🔥 搜索引擎新闻解析器测试 - 全引擎测试")
    print("="*70)

    test_query = "人工智能"

    # 所有10个搜索引擎
    engines = [
        "baidu",      # 百度
        "bing",       # 必应
        "sogou",      # 搜狗
        "google",     # 谷歌
        "360",        # 360搜索
        "toutiao",    # 今日头条
        "tencent",    # 腾讯新闻
        "wangyi",     # 网易新闻
        "sina",       # 新浪新闻
        "sohu",       # 搜狐新闻
    ]

    results = []

    for engine in engines:
        success, count, elapsed = await test_engine_news(engine, test_query)
        results.append({
            "engine": engine,
            "success": success,
            "count": count,
            "elapsed": elapsed
        })

        # 等待一下，避免请求过快
        await asyncio.sleep(2)

    # 打印总结
    print("\n" + "="*70)
    print("📊 测试总结")
    print("="*70)

    # 按成功/失败分组
    success_engines = [r for r in results if r["success"]]
    failed_engines = [r for r in results if not r["success"]]

    print(f"\n✅ 成功 ({len(success_engines)}/{len(engines)}):")
    for r in success_engines:
        print(f"   {r['engine']:10} - {r['count']} 条结果, {r['elapsed']:.2f}秒")

    if failed_engines:
        print(f"\n❌ 失败 ({len(failed_engines)}/{len(engines)}):")
        for r in failed_engines:
            print(f"   {r['engine']:10} - {r['elapsed']:.2f}秒")

    # 性能统计
    if success_engines:
        avg_results = sum(r["count"] for r in success_engines) / len(success_engines)
        avg_elapsed = sum(r["elapsed"] for r in success_engines) / len(success_engines)
        print(f"\n⚡ 性能统计:")
        print(f"   平均结果数: {avg_results:.1f} 条")
        print(f"   平均耗时: {avg_elapsed:.2f} 秒")

    print()


# ==================== 测试多引擎智能搜索 ====================

async def test_multi_search():
    """测试多引擎智能搜索（含自动降级）"""
    print("\n" + "="*70)
    print("🔥 多引擎智能搜索测试")
    print("="*70)

    test_query = "科技新闻"

    # 测试 auto 模式
    print(f"\n📡 测试 AUTO 模式")
    print(f"关键词: {test_query}")
    print('-'*70)

    result = await multi_search(test_query, "auto", 20, "news")

    import json
    result_data = json.loads(result)

    print(f"\n📊 搜索结果:")
    print(f"   引擎: {result_data.get('engine_name', 'N/A')}")
    print(f"   结果数: {result_data.get('total', 0)}")
    print(f"   可用引擎: {result_data.get('available_engines', 'N/A')}")
    print(f"   被禁用引擎: {result_data.get('banned_engines', 'N/A')}")

    if result_data.get("blocked"):
        print(f"   ⚠️ 被拦截: {result_data.get('block_reason', 'N/A')}")

    if result_data.get("results"):
        print(f"\n📰 前3条结果:")
        for i, item in enumerate(result_data["results"][:3], 1):
            print(f"\n{i}. {item.get('title', 'N/A')}")
            print(f"   来源: {item.get('source', 'N/A')}")

    print()


# ==================== 测试引擎禁用机制 ====================

async def test_ban_mechanism():
    """测试引擎禁用和解禁机制"""
    print("\n" + "="*70)
    print("🔥 引擎禁用机制测试")
    print("="*70)

    engine_factory = EngineFactory()

    test_engine = "baidu"

    print(f"\n📝 测试引擎: {test_engine}")

    # 初始状态
    print(f"\n1️⃣ 初始状态:")
    print(f"   是否被禁用: {engine_factory.is_engine_banned(test_engine)}")
    print(f"   被禁用引擎数: {engine_factory.get_banned_engine_count()}")
    print(f"   可用引擎数: {engine_factory.get_available_engine_count()}")

    # 禁用引擎（第1次）
    print(f"\n2️⃣ 禁用引擎（第1次）:")
    engine_factory.ban_engine(test_engine, "测试禁用1")
    ban_info = engine_factory._banned_engines.get(test_engine)
    if ban_info:
        ban_duration = ban_info['unban_time'] - time.time()
        print(f"   禁用时长: {ban_duration//60} 分钟")
        print(f"   禁用次数: {ban_info['ban_count']}")
    print(f"   是否被禁用: {engine_factory.is_engine_banned(test_engine)}")
    print(f"   被禁用引擎数: {engine_factory.get_banned_engine_count()}")
    print(f"   可用引擎数: {engine_factory.get_available_engine_count()}")

    # 禁用引擎（第2次 - 模拟递增）
    print(f"\n3️⃣ 禁用引擎（第2次 - 测试递增机制）:")
    engine_factory.ban_engine(test_engine, "测试禁用2")
    ban_info = engine_factory._banned_engines.get(test_engine)
    if ban_info:
        ban_duration = ban_info['unban_time'] - time.time()
        print(f"   禁用时长: {ban_duration//60} 分钟")
        print(f"   禁用次数: {ban_info['ban_count']}")
    print(f"   是否被禁用: {engine_factory.is_engine_banned(test_engine)}")

    print()


# ==================== 测试新闻聚合平台 ====================

async def test_news_aggregators():
    """测试5个中文新闻聚合平台"""
    print("\n" + "="*70)
    print("🔥 新闻聚合平台专项测试")
    print("="*70)

    test_query = "体育新闻"

    # 5个新闻聚合平台
    aggregators = ["toutiao", "tencent", "wangyi", "sina", "sohu"]

    print(f"\n关键词: {test_query}")
    print(f"测试平台: {', '.join(aggregators)}")

    results = []

    for engine in aggregators:
        success, count, elapsed = await test_engine_news(engine, test_query)
        results.append({
            "engine": engine,
            "success": success,
            "count": count,
            "elapsed": elapsed
        })

        await asyncio.sleep(2)

    # 总结
    print("\n" + "="*70)
    print("📊 新闻聚合平台测试总结")
    print("="*70)

    success_engines = [r for r in results if r["success"]]
    failed_engines = [r for r in results if not r["success"]]

    print(f"\n✅ 成功 ({len(success_engines)}/{len(aggregators)}):")
    for r in success_engines:
        print(f"   {r['engine']:10} - {r['count']} 条结果, {r['elapsed']:.2f}秒")

    if failed_engines:
        print(f"\n❌ 失败 ({len(failed_engines)}/{len(aggregators)}):")
        for r in failed_engines:
            print(f"   {r['engine']:10} - {r['elapsed']:.2f}秒")

    print()


# ==================== 主菜单 ====================

async def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("🧪 搜索引擎测试套件")
    print("="*70)

    print("\n请选择测试类型:")
    print("1. 测试所有10个搜索引擎")
    print("2. 测试多引擎智能搜索")
    print("3. 测试引擎禁用机制")
    print("4. 测试新闻聚合平台（5个）")
    print("5. 运行全部测试")

    # 默认运行全部测试
    choice = "5"

    if choice == "1":
        await test_all_engines()
    elif choice == "2":
        await test_multi_search()
    elif choice == "3":
        await test_ban_mechanism()
    elif choice == "4":
        await test_news_aggregators()
    elif choice == "5":
        print("\n🚀 开始运行全部测试...\n")

        await test_all_engines()
        await asyncio.sleep(1)

        await test_multi_search()
        await asyncio.sleep(1)

        await test_ban_mechanism()
        await asyncio.sleep(1)

        await test_news_aggregators()

        print("\n" + "="*70)
        print("✅ 全部测试完成！")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
