"""
测试数据库保存功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径到系统路径
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.news_storage.core.database import NewsDatabase
from mcp_server.news_storage.core.models import NewsItem


async def test_database_operations():
    """测试数据库的基本操作"""

    # 使用测试数据库
    test_db_path = "./data/test_news_storage.db"
    db = NewsDatabase(test_db_path)

    print("=" * 60)
    print("开始测试数据库保存功能")
    print("=" * 60)

    # 测试1: 保存单条新闻
    print("\n[测试1] 保存单条新闻...")
    test_news = NewsItem(
        title="测试新闻标题",
        url="https://example.com/test1",
        summary="这是一条测试新闻的摘要",
        source="测试来源",
        publish_time="2026-01-30 10:00:00",
        author="测试作者",
        event_name="测试事件",
        content="这是测试新闻的完整内容...",
        keywords=["测试", "数据库", "保存"],
        image_urls=["https://example.com/image1.jpg"],
        tags=["标签1", "标签2"]
    )

    session_id = "test_session_001"
    category = "测试类别"

    try:
        result = await db.save_news(test_news, session_id=session_id, category=category)
        print(f"✅ 保存成功: {result}")
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

    # 测试2: 立即读取验证
    print("\n[测试2] 立即读取验证...")
    try:
        retrieved_news = await db.get_news_by_url(
            test_news.url,
            session_id=session_id,
            category=category
        )
        if retrieved_news:
            print(f"✅ 读取成功:")
            print(f"   - 标题: {retrieved_news.title}")
            print(f"   - URL: {retrieved_news.url}")
            print(f"   - 摘要: {retrieved_news.summary}")
            print(f"   - 来源: {retrieved_news.source}")
            print(f"   - 关键词: {retrieved_news.keywords}")
            print(f"   - 会话ID: {retrieved_news.session_id}")
            print(f"   - 类别: {retrieved_news.category}")

            # 验证数据一致性
            if retrieved_news.title != test_news.title:
                print(f"❌ 数据不一致! 标题不匹配")
                return False
            if retrieved_news.session_id != session_id:
                print(f"❌ 数据不一致! session_id不匹配")
                return False
            if retrieved_news.category != category:
                print(f"❌ 数据不一致! category不匹配")
                return False

            print("✅ 数据一致性验证通过")
        else:
            print("❌ 读取失败: 未找到数据")
            return False
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return False

    # 测试3: 批量保存
    print("\n[测试3] 批量保存多条新闻...")
    news_list = []
    for i in range(5):
        news = NewsItem(
            title=f"批量测试新闻 {i+1}",
            url=f"https://example.com/batch_{i+1}",
            summary=f"这是第{i+1}条批量测试新闻",
            source="批量测试来源",
            keywords=["批量", "测试", f"编号{i+1}"]
        )
        news_list.append(news)

    try:
        result = await db.save_news_batch(news_list)
        print(f"✅ 批量保存完成: {result}")
    except Exception as e:
        print(f"❌ 批量保存失败: {e}")
        return False

    # 测试4: 搜索验证
    print("\n[测试4] 搜索验证...")
    from mcp_server.news_storage.core.models import SearchFilter

    search_filter = SearchFilter(
        session_id=session_id,
        category=category,
        search_terms=["测试"],
        limit=10
    )

    try:
        results = await db.search_news(search_filter)
        print(f"✅ 搜索成功，找到 {len(results)} 条结果")
        for i, news in enumerate(results[:3], 1):
            print(f"   {i}. {news.title[:50]}")
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False

    # 测试5: 获取统计信息
    print("\n[测试5] 获取统计信息...")
    try:
        stats = await db.get_stats(session_id=session_id)
        print(f"✅ 统计信息:")
        print(f"   - 总数: {stats['total']}")
        print(f"   - 最近7天: {stats['recent_week']}")
        print(f"   - 按来源: {stats['by_source']}")
    except Exception as e:
        print(f"❌ 获取统计失败: {e}")
        return False

    # 测试6: 关闭连接后重新打开验证持久化
    print("\n[测试6] 测试数据持久化...")
    await db.close()
    print("   数据库连接已关闭")

    # 重新连接
    db2 = NewsDatabase(test_db_path)
    try:
        retrieved_news2 = await db2.get_news_by_url(
            test_news.url,
            session_id=session_id,
            category=category
        )
        if retrieved_news2:
            print(f"✅ 持久化验证成功: 重启后数据仍然存在")
            print(f"   - 标题: {retrieved_news2.title}")
        else:
            print("❌ 持久化验证失败: 重启后数据丢失")
            return False
    except Exception as e:
        print(f"❌ 持久化验证失败: {e}")
        return False

    await db2.close()

    print("\n" + "=" * 60)
    print("✅ 所有测试通过!")
    print("=" * 60)
    return True


async def test_with_commit_verification():
    """专门测试 commit 问题"""
    print("\n" + "=" * 60)
    print("专门测试 commit 机制")
    print("=" * 60)

    test_db_path = "./data/test_commit.db"
    db = NewsDatabase(test_db_path)

    # 清空测试数据库
    import os
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print("\n[步骤1] 保存一条新闻...")
    news = NewsItem(
        title="Commit测试新闻",
        url="https://test.com/commit_test",
        summary="测试commit是否正常工作"
    )

    result = await db.save_news(news, session_id="test", category="test")
    print(f"   保存返回: {result}")

    print("\n[步骤2] 检查数据库文件...")
    if Path(test_db_path).exists():
        file_size = Path(test_db_path).stat().st_size
        print(f"   ✅ 数据库文件存在，大小: {file_size} 字节")
    else:
        print(f"   ❌ 数据库文件不存在!")
        return False

    print("\n[步骤3] 立即查询...")
    retrieved = await db.get_news_by_url(
        news.url,
        session_id="test",
        category="test"
    )
    if retrieved:
        print(f"   ✅ 查询成功: {retrieved.title}")
    else:
        print(f"   ❌ 查询失败: 未找到数据")
        return False

    print("\n[步骤4] 关闭连接，重新打开...")
    await db.close()

    db2 = NewsDatabase(test_db_path)
    retrieved2 = await db2.get_news_by_url(
        news.url,
        session_id="test",
        category="test"
    )

    if retrieved2:
        print(f"   ✅ 重启后查询成功: {retrieved2.title}")
    else:
        print(f"   ❌ 重启后查询失败: 数据未持久化")
        await db2.close()
        return False

    await db2.close()

    print("\n✅ Commit 测试通过!")
    return True


async def main():
    """主测试函数"""
    # 测试基本操作
    success1 = await test_database_operations()

    # 测试commit机制
    success2 = await test_with_commit_verification()

    if success1 and success2:
        print("\n" + "🎉" * 30)
        print("所有测试完成! 数据库保存功能正常!")
        print("🎉" * 30)
    else:
        print("\n" + "⚠️" * 30)
        print("测试失败! 请检查数据库实现!")
        print("⚠️" * 30)


if __name__ == "__main__":
    asyncio.run(main())
