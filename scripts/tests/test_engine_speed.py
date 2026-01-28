"""
测试搜索引擎速度并排序
"""

import sys
import io
import asyncio
import json
from typing import List, Dict
import time

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from mcp_server.baidu_search.multi_engine import MultiSearchEngine, get_multi_engine
from mcp_server.baidu_search.browser_pool import get_browser_pool
from mcp_server.baidu_search.main import rate_limiter


async def test_engine_speed(
    engine_name: str,
    query: str = "你好",
    search_type: str = "news",
    repeat: int = 3
) -> Dict:
    """测试单个搜索引擎的速度

    Args:
        engine_name: 搜索引擎名称
        query: 搜索关键词
        search_type: 搜索类型 (web/news)
        repeat: 重复测试次数

    Returns:
        包含速度统计的字典
    """
    print(f"\n{'='*60}")
    print(f"测试 {engine_name} 搜索引擎速度")
    print(f"关键词: {query}")
    print(f"重复次数: {repeat}")
    print('='*60)

    # 初始化
    browser_pool = get_browser_pool(
        max_concurrent=1,
        proxy={"server": "localhost:7897"}
    )
    multi_engine = get_multi_engine(browser_pool, rate_limiter)

    times = []
    success_count = 0
    error_count = 0

    for i in range(repeat):
        try:
            print(f"\n第 {i+1}/{repeat} 次测试...")

            start_time = time.time()

            # 执行搜索
            result_json = await multi_engine.search(
                query=query,
                engine=engine_name,
                num_results=10,
                search_type=search_type
            )

            end_time = time.time()
            elapsed = end_time - start_time

            # 解析结果
            result = json.loads(result_json)

            if result.get('error'):
                print(f"   ❌ 错误: {result['error']}")
                error_count += 1
            else:
                total = result.get('total', 0)
                print(f"   ✅ 成功! 耗时: {elapsed:.2f}秒, 结果数: {total}")
                times.append(elapsed)
                success_count += 1

        except Exception as e:
            print(f"   ❌ 异常: {e}")
            error_count += 1

        # 每次测试之间等待一下
        if i < repeat - 1:
            await asyncio.sleep(2)

    # 计算统计数据
    stats = {
        "engine": engine_name,
        "success_count": success_count,
        "error_count": error_count,
        "times": times,
    }

    if times:
        stats["avg_time"] = sum(times) / len(times)
        stats["min_time"] = min(times)
        stats["max_time"] = max(times)
        stats["success_rate"] = success_count / repeat
    else:
        stats["avg_time"] = float('inf')
        stats["min_time"] = float('inf')
        stats["max_time"] = float('inf')
        stats["success_rate"] = 0.0

    # 打印统计
    print(f"\n📊 统计结果:")
    print(f"   成功次数: {success_count}/{repeat}")
    print(f"   失败次数: {error_count}")
    if times:
        print(f"   平均耗时: {stats['avg_time']:.2f}秒")
        print(f"   最快: {stats['min_time']:.2f}秒")
        print(f"   最慢: {stats['max_time']:.2f}秒")
    print(f"   成功率: {stats['success_rate']*100:.1f}%")

    await browser_pool.close()

    return stats


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🚀 搜索引擎速度测试")
    print("="*60)

    test_query = "人工智能"
    search_type = "news"
    repeat = 3  # 每个引擎测试3次

    # 要测试的引擎列表
    engines = [
        "baidu",
        "bing",
        "sogou",
        "google",
        "360",
    ]

    # 测试所有引擎
    all_stats = []
    for engine in engines:
        try:
            stats = await test_engine_speed(engine, test_query, search_type, repeat)
            all_stats.append(stats)
        except Exception as e:
            print(f"\n❌ 测试 {engine} 时发生异常: {e}")
            import traceback
            traceback.print_exc()

    # 排序引擎（按平均耗时）
    print("\n" + "="*60)
    print("📊 最终排名（按平均速度排序）")
    print("="*60)

    # 只保留成功的测试
    successful_stats = [s for s in all_stats if s['times']]

    if not successful_stats:
        print("\n❌ 所有引擎测试都失败了！")
        return

    # 按平均时间排序（越短越好）
    successful_stats.sort(key=lambda x: x['avg_time'])

    print(f"\n{'排名':<6}{'引擎':<12}{'平均耗时':<12}{'最快':<10}{'最慢':<10}{'成功率':<10}")
    print("-" * 60)

    for rank, stats in enumerate(successful_stats, 1):
        print(
            f"{rank:<6}"
            f"{stats['engine']:<12}"
            f"{stats['avg_time']:.2f}秒     "
            f"{stats['min_time']:.2f}秒  "
            f"{stats['max_time']:.2f}秒  "
            f"{stats['success_rate']*100:.0f}%"
        )

    # 生成推荐的引擎顺序配置
    print("\n" + "="*60)
    print("🔧 推荐的引擎优先级配置")
    print("="*60)

    recommended_order = [s['engine'] for s in successful_stats]

    print(f"\n引擎顺序 = {recommended_order}")
    print(f"\n说明: 速度快的引擎优先使用，可以提高整体响应速度。")

    # 保存到文件
    with open('engine_speed_ranking.json', 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_query': test_query,
            'search_type': search_type,
            'repeat': repeat,
            'ranking': successful_stats,
            'recommended_order': recommended_order
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 详细结果已保存到: engine_speed_ranking.json")


if __name__ == "__main__":
    asyncio.run(main())
