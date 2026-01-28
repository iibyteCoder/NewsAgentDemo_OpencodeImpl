"""
测试 News Storage MCP Server
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.news_storage.core.database import get_database
from mcp_server.news_storage.core.models import NewsItem, SearchFilter
from loguru import logger


async def test_basic_operations():
    """测试基本操作"""
    logger.info("=" * 50)
    logger.info("测试1: 基本CRUD操作")
    logger.info("=" * 50)

    db = get_database("./data/test_news.db")

    # 测试1: 创建新闻
    logger.info("\n1️⃣ 创建新闻...")
    news1 = NewsItem(
        title="AI技术取得重大突破",
        url="https://example.com/news/ai-breakthrough-001",
        summary="人工智能领域迎来重大技术突破，新算法性能提升300%",
        source="科技日报",
        publish_time="2026-01-29",
        author="张三",
        event_name="2026年AI技术突破事件",
        content="这是完整的新闻内容...",
        html_content="<p>这是HTML原文内容</p>",
        keywords=["AI", "技术", "突破"],
        images=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
        tags=["科技", "前沿"],
    )

    is_new = db.save_news(news1)
    logger.info(f"   结果: {'新增' if is_new else '更新'}")
    logger.info(f"   事件名称: {news1.event_name}")

    # 测试2: 根据URL查询
    logger.info("\n2️⃣ 根据URL查询...")
    found_news = db.get_news_by_url(news1.url)
    if found_news:
        logger.info(f"   找到: {found_news.title}")
        logger.info(f"   摘要: {found_news.summary[:50]}...")
    else:
        logger.error("   未找到！")

    # 测试3: 更新内容
    logger.info("\n3️⃣ 更新新闻内容...")
    success = db.update_news_content(
        news1.url,
        "这是更新后的完整新闻正文内容，包含了更多细节...",
        "<p>HTML内容</p>",
    )
    logger.info(f"   结果: {'成功' if success else '失败'}")

    # 测试4: 创建更多新闻
    logger.info("\n4️⃣ 批量创建新闻...")
    news_list = [
        NewsItem(
            title="量子计算新进展",
            url="https://example.com/news/quantum-001",
            summary="量子计算机成功实现1000量子比特稳定运行",
            source="新华网",
            publish_time="2026-01-28",
            keywords=["量子", "计算"],
            tags=["科技"],
        ),
        NewsItem(
            title="新能源汽车销量激增",
            url="https://example.com/news/ev-001",
            summary="本月新能源汽车销量同比增长200%",
            source="财经网",
            publish_time="2026-01-27",
            keywords=["汽车", "新能源"],
            tags=["财经"],
        ),
    ]

    for news in news_list:
        db.save_news(news)

    logger.info(f"   创建了 {len(news_list)} 条新闻")

    # 测试5: 获取最近新闻
    logger.info("\n5️⃣ 获取最近新闻...")
    recent = db.get_recent_news(limit=10)
    logger.info(f"   找到 {len(recent)} 条最近新闻")
    for news in recent[:3]:
        logger.info(f"   - {news.title} ({news.source})")

    # 测试6: 搜索功能
    logger.info("\n6️⃣ 搜索功能测试...")

    # 关键词搜索
    filter1 = SearchFilter(keyword="AI", limit=10)
    results1 = db.search_news(filter1)
    logger.info(f"   关键词'AI': 找到 {len(results1)} 条")

    # 按来源筛选
    filter2 = SearchFilter(source="科技日报", limit=10)
    results2 = db.search_news(filter2)
    logger.info(f"   来源'科技日报': 找到 {len(results2)} 条")

    # 按标签筛选
    filter3 = SearchFilter(tags=["科技"], limit=10)
    results3 = db.search_news(filter3)
    logger.info(f"   标签'科技': 找到 {len(results3)} 条")

    # 按事件名称筛选
    filter4 = SearchFilter(event_name="2026年AI技术突破事件", limit=10)
    results4 = db.search_news(filter4)
    logger.info(f"   事件名称'2026年AI技术突破事件': 找到 {len(results4)} 条")

    # 测试7: 统计信息
    logger.info("\n7️⃣ 获取统计信息...")
    stats = db.get_stats()
    logger.info(f"   总数: {stats['total']}")
    logger.info(f"   最近7天: {stats['recent_week']}")
    logger.info(f"   来源分布:")
    for source, count in stats['by_source'].items():
        logger.info(f"     - {source}: {count}")

    # 测试8: 删除新闻
    logger.info("\n8️⃣ 删除新闻...")
    delete_url = "https://example.com/news/ev-001"
    success = db.delete_news(delete_url)
    logger.info(f"   删除结果: {'成功' if success else '失败'}")

    logger.info("\n✅ 基本操作测试完成！")


async def test_batch_operations():
    """测试批量操作"""
    logger.info("\n" + "=" * 50)
    logger.info("测试2: 批量操作")
    logger.info("=" * 50)

    db = get_database("./data/test_news.db")

    # 批量保存
    logger.info("\n1️⃣ 批量保存新闻...")
    batch_news = [
        NewsItem(
            title=f"测试新闻 {i}",
            url=f"https://example.com/test/batch-{i}",
            summary=f"这是第 {i} 条测试新闻",
            source="测试来源",
            keywords=["测试"],
        )
        for i in range(10)
    ]

    stats = db.save_news_batch(batch_news)
    logger.info(f"   新增: {stats['added']}")
    logger.info(f"   更新: {stats['updated']}")
    logger.info(f"   失败: {stats['failed']}")

    # 再次保存相同数据（测试去重）
    logger.info("\n2️⃣ 测试去重（再次保存相同数据）...")
    stats = db.save_news_batch(batch_news)
    logger.info(f"   新增: {stats['added']} (应该为0)")
    logger.info(f"   更新: {stats['updated']} (应该为10)")

    logger.info("\n✅ 批量操作测试完成！")


async def test_search_features():
    """测试搜索功能"""
    logger.info("\n" + "=" * 50)
    logger.info("测试3: 高级搜索功能")
    logger.info("=" * 50)

    db = get_database("./data/test_news.db")

    # 创建不同类型的新闻
    logger.info("\n1️⃣ 创建测试数据...")
    test_data = [
        NewsItem(
            title="Python 3.13发布",
            url="https://example.com/tech/python-313",
            summary="Python 3.13正式发布，性能大幅提升",
            source="技术社区",
            keywords=["Python", "编程"],
            tags=["技术", "编程语言"],
        ),
        NewsItem(
            title="JavaScript框架对比",
            url="https://example.com/tech/js-frameworks",
            summary="React vs Vue vs Angular，哪个更好？",
            source="前端周刊",
            keywords=["JavaScript", "前端"],
            tags=["技术", "前端开发"],
        ),
        NewsItem(
            title="Rust语言入门指南",
            url="https://example.com/tech/rust-guide",
            summary="Rust语言详细教程，从零开始",
            source="技术社区",
            keywords=["Rust", "编程"],
            tags=["技术", "系统编程"],
        ),
    ]

    for news in test_data:
        db.save_news(news)

    # 测试各种搜索
    logger.info("\n2️⃣ 测试关键词搜索...")
    filters = [
        SearchFilter(keyword="Python", limit=10),
        SearchFilter(keyword="JavaScript", limit=10),
        SearchFilter(keyword="性能", limit=10),
    ]

    for f in filters:
        results = db.search_news(f)
        logger.info(f"   关键词'{f.keyword}': {len(results)} 条")

    logger.info("\n3️⃣ 测试来源筛选...")
    filter_source = SearchFilter(source="技术社区", limit=10)
    results = db.search_news(filter_source)
    logger.info(f"   来源'技术社区': {len(results)} 条")

    logger.info("\n4️⃣ 测试标签筛选...")
    filter_tags = SearchFilter(tags=["技术"], limit=10)
    results = db.search_news(filter_tags)
    logger.info(f"   标签'技术': {len(results)} 条")

    logger.info("\n5️⃣ 测试组合搜索...")
    filter_combo = SearchFilter(
        keyword="编程", source="技术社区", limit=10
    )
    results = db.search_news(filter_combo)
    logger.info(f"   关键词'编程' + 来源'技术社区': {len(results)} 条")

    logger.info("\n✅ 搜索功能测试完成！")


async def main():
    """运行所有测试"""
    logger.info("🚀 News Storage 测试开始\n")

    try:
        await test_basic_operations()
        await test_batch_operations()
        await test_search_features()

        logger.info("\n" + "=" * 50)
        logger.info("🎉 所有测试通过！")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
