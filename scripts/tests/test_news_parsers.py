"""
新闻搜索测试 - 使用 MCP 工具

直接调用 MCP 服务器的搜索工具进行测试
"""

import sys
import io
import asyncio
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# 导入 MCP 搜索工具
from mcp_server.web_browser.tools.search_tools import (
    baidu_news_search,
    bing_news_search,
    sogou_news_search,
    google_news_search,
    search_360_news,
    toutiao_news_search,
    tencent_news_search,
    wangyi_news_search,
    sina_news_search,
    sohu_news_search,
    multi_search,
)


# ==================== 工具映射 ====================

NEWS_SEARCH_TOOLS = {
    "baidu": baidu_news_search,
    "bing": bing_news_search,
    "sogou": sogou_news_search,
    "google": google_news_search,
    "360": search_360_news,
    "toutiao": toutiao_news_search,
    "tencent": tencent_news_search,
    "wangyi": wangyi_news_search,
    "sina": sina_news_search,
    "sohu": sohu_news_search,
}


async def test_news_search(engine_name: str, query: str, num_results: int = 10):
    """测试单个搜索引擎的新闻搜索

    Args:
        engine_name: 引擎名称
        query: 搜索关键词
        num_results: 返回结果数量

    Returns:
        (是否成功, 结果数据)
    """
    print(f"\n{'='*70}")
    print(f"🔍 测试 {engine_name.upper()} 新闻搜索")
    print(f"关键词: {query}")
    print("=" * 70)

    try:
        # 获取对应的搜索工具
        search_func = NEWS_SEARCH_TOOLS.get(engine_name)

        if not search_func:
            print(f"❌ 不支持的引擎: {engine_name}")
            return False, None

        # 调用 MCP 工具
        print(f"📡 调用 {engine_name}_news_search 工具...")
        result_json = await search_func(query, num_results)

        # 解析结果
        result_data = json.loads(result_json)

        # 检查是否有错误
        if result_data.get("error"):
            print(f"❌ 搜索出错: {result_data['error']}")
            return False, result_data

        # 显示结果
        print(f"\n📊 测试结果:")
        print(f"   引擎: {result_data.get('engine_name', 'N/A')}")
        print(f"   结果数: {result_data.get('total', 0)}")

        if result_data.get("blocked"):
            print(f"   ⚠️ 被拦截: {result_data.get('block_reason', 'N/A')}")

        # 显示所有搜索结果
        results = result_data.get("results", [])
        if results:
            print(f"\n📰 搜索结果:")
            print(f"{'-'*70}")
            for i, item in enumerate(results, 1):
                print(f"\n{i}. {item.get('title', 'N/A')}")
                print(f"   来源: {item.get('source', 'N/A')}")
                print(f"   时间: {item.get('time', 'N/A')}")
                url = item.get("url", "N/A")
                print(f"   链接: {url[:70] if url != 'N/A' else 'N/A'}...")
                if item.get("summary"):
                    print(f"   摘要: {item['summary'][:100]}...")

        return True, result_data

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_multi_engine_search(query: str, num_results: int = 10):
    """测试多引擎智能搜索

    Args:
        query: 搜索关键词
        num_results: 返回结果数量

    Returns:
        (是否成功, 结果数据)
    """
    print(f"\n{'='*70}")
    print(f"🔍 测试多引擎智能搜索")
    print(f"关键词: {query}")
    print("=" * 70)

    try:
        print(f"📡 调用 multi_search 工具...")
        result_json = await multi_search(query, "auto", num_results, "news")

        # 解析结果
        result_data = json.loads(result_json)

        # 检查是否有错误
        if result_data.get("error"):
            print(f"❌ 搜索出错: {result_data['error']}")
            return False, result_data

        # 显示结果
        print(f"\n📊 测试结果:")
        print(f"   引擎: {result_data.get('engine_name', 'N/A')}")
        print(f"   结果数: {result_data.get('total', 0)}")
        print(f"   可用引擎: {result_data.get('available_engines', 'N/A')}")
        print(f"   被禁用引擎: {result_data.get('banned_engines', 'N/A')}")

        if result_data.get("blocked"):
            print(f"   ⚠️ 被拦截: {result_data.get('block_reason', 'N/A')}")

        # 显示所有搜索结果
        results = result_data.get("results", [])
        if results:
            print(f"\n📰 搜索结果:")
            print(f"{'-'*70}")
            for i, item in enumerate(results, 1):
                print(f"\n{i}. {item.get('title', 'N/A')}")
                print(f"   来源: {item.get('source', 'N/A')}")
                print(f"   时间: {item.get('time', 'N/A')}")
                url = item.get("url", "N/A")
                print(f"   链接: {url[:70] if url != 'N/A' else 'N/A'}...")
                if item.get("summary"):
                    print(f"   摘要: {item['summary'][:100]}...")

        return True, result_data

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


# ==================== 配置和执行 ====================

async def main():
    """主函数 - 在这里配置参数并执行测试"""

    print("\n" + "="*70)
    print("🧪 新闻搜索测试 - MCP 工具")
    print("="*70)

    # ========== 配置区域 ==========
    # 修改这里的参数来测试不同的搜索引擎

    # 搜索关键词
    query = "人工智能"

    # 返回结果数量
    num_results = 10

    # 测试模式：single（单个引擎） 或 multi（多引擎智能搜索）
    test_mode = "single"

    # 要测试的搜索引擎（仅在 single 模式下生效）
    # 可选引擎: baidu, bing, sogou, google, 360, toutiao, tencent, wangyi, sina, sohu
    engines = [
        # "baidu",      # 百度
        # "bing",       # 必应
        # "sogou",      # 搜狗
        # "google",     # 谷歌
        # "360",        # 360搜索
        # "toutiao",    # 今日头条
        # "tencent",    # 腾讯新闻
        # "wangyi",     # 网易新闻
        # "sina",       # 新浪新闻
        # "sohu",       # 搜狐新闻
    ]

    # ========================

    print(f"\n📝 测试配置:")
    print(f"   关键词: {query}")
    print(f"   结果数: {num_results}")
    print(f"   测试模式: {test_mode}")

    if test_mode == "multi":
        print(f"\n🔧 使用多引擎智能搜索模式")
        success, result = await test_multi_engine_search(query, num_results)
    else:
        print(f"   测试引擎: {', '.join(engines)}")
        print(f"   引擎数量: {len(engines)}")

        # 执行测试
        all_results = []
        for engine in engines:
            success, result = await test_news_search(engine, query, num_results)
            all_results.append({
                "engine": engine,
                "success": success,
                "result": result
            })

        # 打印总结
        if len(engines) > 1:
            print("\n" + "="*70)
            print("📊 测试总结")
            print("="*70)

            success_engines = [r for r in all_results if r["success"]]
            failed_engines = [r for r in all_results if not r["success"]]

            print(f"\n✅ 成功 ({len(success_engines)}/{len(engines)}):")
            for r in success_engines:
                count = r["result"].get("total", 0) if r["result"] else 0
                print(f"   {r['engine']:10} - {count} 条结果")

            if failed_engines:
                print(f"\n❌ 失败 ({len(failed_engines)}/{len(engines)}):")
                for r in failed_engines:
                    print(f"   {r['engine']:10}")

    print("\n" + "="*70)
    print("✅ 测试完成！")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
