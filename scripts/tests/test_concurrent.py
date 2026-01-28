"""
MCP Server 并发性能测试

测试不同并发级别下的性能表现
"""

import sys
import io
import time
import asyncio
from typing import List, Dict
import json

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from mcp_server.baidu_search.main import (
    baidu_search,
    baidu_news_search,
    baidu_hot_search,
)
from mcp_server.baidu_search.browser_pool import get_browser_pool


class ConcurrentTester:
    """并发测试器"""

    def __init__(self):
        self.browser_pool = get_browser_pool()
        self.results = []

    async def test_single_search(self, query: str, index: int) -> Dict:
        """执行单个搜索测试"""
        start_time = time.time()
        try:
            result = await baidu_news_search(query=query, num_results=10)
            elapsed = time.time() - start_time

            data = json.loads(result)
            success = data.get("total", 0) > 0

            return {
                "index": index,
                "query": query,
                "success": success,
                "elapsed": elapsed,
                "result_count": data.get("total", 0),
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "index": index,
                "query": query,
                "success": False,
                "elapsed": elapsed,
                "error": str(e),
            }

    async def test_concurrent_searches(
        self,
        queries: List[str],
        concurrency: int,
        batch_name: str,
    ) -> Dict:
        """测试并发搜索

        Args:
            queries: 搜索关键词列表
            concurrency: 并发数量
            batch_name: 批次名称

        Returns:
            测试结果统计
        """
        print(f"\n{'='*60}")
        print(f"📊 测试批次: {batch_name}")
        print(f"   并发数: {concurrency}")
        print(f"   请求数: {len(queries)}")
        print(f"{'='*60}")

        start_time = time.time()

        # 使用 Semaphore 控制并发
        semaphore = asyncio.Semaphore(concurrency)

        async def bounded_search(query: str, index: int):
            async with semaphore:
                return await self.test_single_search(query, index)

        # 并发执行所有搜索
        tasks = [bounded_search(query, i) for i, query in enumerate(queries)]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - success_count
        elapsed_times = [r["elapsed"] for r in results if r["success"]]

        stats = {
            "batch_name": batch_name,
            "concurrency": concurrency,
            "total_requests": len(queries),
            "success_count": success_count,
            "failed_count": failed_count,
            "total_time": total_time,
            "avg_time": sum(elapsed_times) / len(elapsed_times) if elapsed_times else 0,
            "min_time": min(elapsed_times) if elapsed_times else 0,
            "max_time": max(elapsed_times) if elapsed_times else 0,
            "throughput": len(queries) / total_time if total_time > 0 else 0,
            "results": results,
        }

        # 打印统计
        print(f"\n✅ 测试完成！")
        print(f"   成功: {success_count} | 失败: {failed_count}")
        print(f"   总耗时: {total_time:.2f}秒")
        print(f"   平均响应时间: {stats['avg_time']:.2f}秒")
        print(f"   最快: {stats['min_time']:.2f}秒 | 最慢: {stats['max_time']:.2f}秒")
        print(f"   吞吐量: {stats['throughput']:.2f} 请求/秒")

        return stats

    async def test_progressive_concurrency(self):
        """渐进式并发测试

        从低并发到高并发，逐步测试
        """
        print("\n" + "="*60)
        print("🚀 开始渐进式并发测试")
        print("="*60)

        # 测试数据（不同关键词）
        test_queries = [
            "人工智能",
            "机器学习",
            "深度学习",
            "Python编程",
            "数据科学",
            "区块链技术",
            "云计算",
            "网络安全",
            "5G技术",
            "量子计算",
        ]

        all_stats = []

        # 测试不同并发级别
        concurrency_levels = [1, 2, 3, 5, 8, 10]

        for concurrency in concurrency_levels:
            # 选择对应数量的查询
            queries = (test_queries * ((concurrency // len(test_queries)) + 1))[:concurrency]

            stats = await self.test_concurrent_searches(
                queries=queries,
                concurrency=concurrency,
                batch_name=f"并发级别 {concurrency}",
            )
            all_stats.append(stats)

            # 等待一下，避免连续测试影响
            await asyncio.sleep(2)

        # 打印总结
        self._print_summary(all_stats)

        return all_stats

    def _print_summary(self, all_stats: List[Dict]):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📊 并发测试总结")
        print("="*60)
        print(f"\n{'并发数':<8} {'请求数':<8} {'成功数':<8} {'总耗时':<10} {'平均响应':<10} {'吞吐量':<12}")
        print("-"*60)

        for stats in all_stats:
            print(
                f"{stats['concurrency']:<8} "
                f"{stats['total_requests']:<8} "
                f"{stats['success_count']:<8} "
                f"{stats['total_time']:<10.2f} "
                f"{stats['avg_time']:<10.2f} "
                f"{stats['throughput']:<12.2f}"
            )

        # 性能分析
        print("\n🔍 性能分析:")

        # 找出最佳并发数
        best_throughput = max(all_stats, key=lambda x: x["throughput"])
        print(f"   • 最佳吞吐量: {best_throughput['throughput']:.2f} 请求/秒 (并发={best_throughput['concurrency']})")

        # 找出最快平均响应
        best_avg_time = min(all_stats, key=lambda x: x["avg_time"])
        print(f"   • 最快平均响应: {best_avg_time['avg_time']:.2f}秒 (并发={best_avg_time['concurrency']})")

        # 成功率
        total_success = sum(s["success_count"] for s in all_stats)
        total_requests = sum(s["total_requests"] for s in all_stats)
        success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
        print(f"   • 整体成功率: {success_rate:.1f}% ({total_success}/{total_requests})")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("🔥 MCP Server 并发性能测试")
    print("="*60)

    # 打印浏览器池配置
    browser_pool = get_browser_pool()
    print(f"\n📋 浏览器池配置:")
    print(f"   • 最大并发数: {browser_pool.max_concurrent_browsers}")
    print(f"   • 最大上下文数: {browser_pool.max_contexts_per_browser}")

    tester = ConcurrentTester()

    try:
        # 运行渐进式并发测试
        await tester.test_progressive_concurrency()

        # 打印浏览器池统计
        stats = browser_pool.get_stats()
        print(f"\n📊 浏览器池统计:")
        print(f"   • 总请求数: {stats['total_requests']}")
        print(f"   • 当前活跃: {stats['active_requests']}")
        print(f"   • 浏览器状态: {'运行中' if stats['browser_alive'] else '已关闭'}")

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
    asyncio.run(main())
