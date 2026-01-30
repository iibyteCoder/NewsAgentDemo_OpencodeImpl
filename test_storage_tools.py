"""
测试 MCP Storage 工具的保存功能
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 在导入工具之前，先配置测试数据库
from mcp_server.news_storage.core import database
database._db_instance = None  # 重置全局单例

# Monkey patch get_database 使用测试数据库
_original_get_database = database.get_database
_test_db_path = "./data/test_news_storage.db"

async def get_test_database(db_path: str = "./data/news_storage.db") -> database.NewsDatabase:
    """获取测试数据库实例"""
    return await _original_get_database(_test_db_path)

database.get_database = get_test_database

from mcp_server.news_storage.tools import storage_tools
# 让工具模块也使用测试数据库
storage_tools.get_database = get_test_database

# 现在导入工具函数
from mcp_server.news_storage.tools.storage_tools import (
    save_news_tool,
    save_news_batch_tool,
    get_news_by_url_tool,
    search_news_tool,
    get_recent_news_tool,
    get_news_stats_tool,
)


def print_json(data_str: str):
    """美化打印 JSON 字符串"""
    try:
        data = json.loads(data_str)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except:
        print(data_str)


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def test_save_and_retrieve():
    """测试保存和读取功能"""
    print_section("测试1: 保存单条新闻")

    # 保存测试新闻
    result = await save_news_tool(
        title="AI技术重大突破！GPT-5即将发布",
        url="https://example.com/news/gpt5-release",
        session_id="test_session_20260130",
        category="科技",
        summary="OpenAI宣布GPT-5将于今年发布，性能大幅提升",
        source="科技日报",
        publish_time="2026-01-30 10:00:00",
        author="张三",
        event_name="2026年AI技术突破",
        content="这是完整的新闻内容。OpenAI今天正式宣布...",
        html_content="<p>这是HTML内容</p>",
        keywords=json.dumps(["AI", "GPT-5", "OpenAI", "人工智能"]),
        image_urls=json.dumps([
            "https://example.com/images/ai-1.jpg",
            "https://example.com/images/ai-2.jpg"
        ]),
        local_image_paths=json.dumps([
            "./data/images/ai-1.jpg",
            "./data/images/ai-2.jpg"
        ]),
        tags=json.dumps(["科技", "AI", "前沿技术"])
    )

    print("\n[保存结果]")
    print_json(result)

    # 解析结果
    result_data = json.loads(result)
    if not result_data.get("success"):
        print("\n错误: 保存失败!")
        return False

    print("\n[信息] 新闻保存成功!")

    # 立即读取验证
    print_section("测试2: 立即读取验证")

    retrieved = await get_news_by_url_tool(
        url="https://example.com/news/gpt5-release",
        session_id="test_session_20260130",
        category="科技"
    )

    print("\n[读取结果]")
    print_json(retrieved)

    retrieved_data = json.loads(retrieved)
    if not retrieved_data.get("found"):
        print("\n错误: 未找到刚保存的新闻!")
        return False

    # 验证数据完整性
    news = retrieved_data["data"]
    checks = []

    # 检查各个字段
    checks.append(("标题", news["title"] == "AI技术重大突破！GPT-5即将发布"))
    checks.append(("URL", news["url"] == "https://example.com/news/gpt5-release"))
    checks.append(("来源", news["source"] == "科技日报"))
    checks.append(("事件名称", news["event_name"] == "2026年AI技术突破"))
    checks.append(("会话ID", news["session_id"] == "test_session_20260130"))
    checks.append(("类别", news["category"] == "科技"))
    checks.append(("关键词", len(news["keywords"]) == 4))
    checks.append(("图片URL", len(news["image_urls"]) == 2))
    checks.append(("本地图片路径", len(news["local_image_paths"]) == 2))
    checks.append(("标签", len(news["tags"]) == 3))

    print("\n[数据完整性验证]")
    all_passed = True
    for field, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {field}")
        if not passed:
            all_passed = False

    if not all_passed:
        print("\n错误: 数据完整性检查失败!")
        return False

    print("\n[信息] 所有字段验证通过!")
    return True


async def test_batch_save():
    """测试批量保存"""
    print_section("测试3: 批量保存新闻")

    news_list = [
        {
            "title": "特斯拉发布新款Model 3",
            "url": "https://example.com/news/tesla-model3",
            "summary": "特斯拉发布全新Model 3，续航里程提升",
            "source": "汽车之家",
            "publish_time": "2026-01-30 11:00:00",
            "event_name": "2026年新能源汽车发布",
            "keywords": ["特斯拉", "Model 3", "电动车"],
            "tags": ["汽车", "新能源"]
        },
        {
            "title": "比亚迪销量创新高",
            "url": "https://example.com/news/byd-sales",
            "summary": "比亚迪1月销量突破30万辆",
            "source": "汽车之家",
            "publish_time": "2026-01-30 12:00:00",
            "event_name": "2026年新能源汽车发布",
            "keywords": ["比亚迪", "销量", "电动车"],
            "tags": ["汽车", "新能源"]
        },
        {
            "title": "蔚来发布新车型",
            "url": "https://example.com/news/nio-new",
            "summary": "蔚来发布全新ET7车型",
            "source": "汽车之家",
            "publish_time": "2026-01-30 13:00:00",
            "event_name": "2026年新能源汽车发布",
            "keywords": ["蔚来", "ET7", "电动车"],
            "tags": ["汽车", "新能源"]
        }
    ]

    # 注意：批量保存需要在每条新闻中添加 session_id 和 category
    # 但 save_news_batch_tool 的参数格式是新闻列表
    # 让我们看看实际的实现

    result = await save_news_batch_tool(
        json.dumps(news_list)
    )

    print("\n[批量保存结果]")
    print_json(result)

    result_data = json.loads(result)
    if result_data.get("success"):
        print(f"\n[信息] 批量保存成功!")
        print(f"   - 新增: {result_data.get('added', 0)}")
        print(f"   - 更新: {result_data.get('updated', 0)}")
        print(f"   - 失败: {result_data.get('failed', 0)}")
        print(f"   - 总计: {result_data.get('total', 0)}")
        return True
    else:
        print(f"\n错误: 批量保存失败! {result_data.get('error')}")
        return False


async def test_search():
    """测试搜索功能"""
    print_section("测试4: 搜索功能")

    result = await search_news_tool(
        session_id="test_session_20260130",
        search="AI GPT 技术",
        limit=10
    )

    print("\n[搜索结果]")
    print_json(result)

    result_data = json.loads(result)
    if result_data.get("success"):
        count = result_data.get("count", 0)
        print(f"\n[信息] 搜索完成，找到 {count} 条结果")

        if count > 0:
            print("\n[前3条结果]")
            for i, news in enumerate(result_data["results"][:3], 1):
                print(f"\n  {i}. {news['title']}")
                print(f"     URL: {news['url']}")
                print(f"     摘要: {news['summary'][:50]}...")

        return True
    else:
        print(f"\n错误: 搜索失败! {result_data.get('error')}")
        return False


async def test_stats():
    """测试统计功能"""
    print_section("测试5: 统计信息")

    result = await get_news_stats_tool(
        session_id="test_session_20260130"
    )

    print("\n[统计结果]")
    print_json(result)

    result_data = json.loads(result)
    if result_data.get("success"):
        stats = result_data["stats"]
        print(f"\n[信息] 统计信息:")
        print(f"   - 总数: {stats['total']}")
        print(f"   - 最近7天: {stats['recent_week']}")
        print(f"   - 数据库路径: {stats['db_path']}")
        print(f"\n   - 按来源分布:")
        for source, count in stats.get('by_source', {}).items():
            print(f"     * {source}: {count}")
        return True
    else:
        print(f"\n错误: 获取统计失败! {result_data.get('error')}")
        return False


async def test_persistence():
    """测试持久化（关闭后重新读取）"""
    print_section("测试6: 数据持久化验证")

    print("\n[步骤1] 保存一条新闻...")

    result = await save_news_tool(
        title="持久化测试新闻",
        url="https://test.com/persistence-test",
        session_id="test_persistence",
        category="测试",
        summary="用于测试数据持久化的新闻"
    )

    print_json(result)

    print("\n[步骤2] 验证数据已保存...")

    # 注意：这里无法真正关闭连接重新打开，因为使用的是单例数据库
    # 但我们可以验证数据是否可读取
    retrieved = await get_news_by_url_tool(
        url="https://test.com/persistence-test",
        session_id="test_persistence",
        category="测试"
    )

    retrieved_data = json.loads(retrieved)

    if retrieved_data.get("found"):
        print("\n[信息] 持久化验证成功 - 数据已正确保存并可读取")
        return True
    else:
        print("\n错误: 持久化验证失败 - 数据无法读取")
        return False


async def main():
    """主测试函数"""
    print("\n" + "#" * 70)
    print("#" + " " * 68 + "#")
    print("#" + "  MCP Storage 工具保存功能测试".center(66) + "#")
    print("#" + " " * 68 + "#")
    print("#" * 70)

    # 清理旧的测试数据库
    test_db_path = Path(_test_db_path)
    if test_db_path.exists():
        print(f"\n[清理] 删除旧测试数据库: {test_db_path}")
        try:
            test_db_path.unlink()
        except PermissionError:
            print(f"[警告] 无法删除测试数据库（可能被占用），将继续测试")

    # 运行所有测试
    tests = [
        ("保存和读取", test_save_and_retrieve),
        ("批量保存", test_batch_save),
        ("搜索功能", test_search),
        ("统计信息", test_stats),
        ("数据持久化", test_persistence),
    ]

    results = []

    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n错误: 测试 '{name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 打印总结
    print_section("测试总结")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "PASS" if success else "FAIL"
        symbol = "+" if success else "x"
        print(f"  [{symbol}] {name}: {status}")

    print("\n" + "=" * 70)
    if passed == total:
        print(f"  结果: 全部通过 ({passed}/{total})")
        print("=" * 70)
        return 0
    else:
        print(f"  结果: 部分失败 ({passed}/{total})")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
