"""
测试异步新闻存储功能
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from mcp_server.news_storage.core.database import get_database, NewsItem


async def test_database():
    """测试数据库所有功能"""

    logger.info("🚀 开始测试异步数据库功能")

    # 1. 获取数据库实例
    db = await get_database()
    logger.info("✅ 数据库连接成功")

    # 2. 测试保存单条新闻
    logger.info("\n📝 测试保存单条新闻...")
    news1 = NewsItem(
        title="AI技术重大突破！GPT-5即将发布",
        url="https://example.com/news/ai-breakthrough",
        summary="OpenAI宣布将在下个月发布GPT-5，性能提升显著",
        source="科技日报",
        publish_time="2026-01-29",
        author="张三",
        event_name="2026年AI技术突破",
        content="这是完整的新闻内容...",
        html_content="<p>这是HTML内容</p>",
        keywords=["AI", "GPT-5", "科技"],
        image_urls=["https://example.com/img1.jpg"],
        local_image_paths=["./data/images/img1.jpg"],
        tags=["科技", "人工智能"],
    )
    is_new = await db.save_news(news1)
    logger.info(f"{'✅ 新增成功' if is_new else '🔄 更新成功'}: {news1.title}")

    # 3. 测试保存第二条新闻
    logger.info("\n📝 测试保存第二条新闻...")
    news2 = NewsItem(
        title="欧冠联赛：皇马逆转巴黎圣日耳曼",
        url="https://example.com/sports/ufcl",
        summary="皇马在主场3-2逆转巴黎圣日耳曼，晋级欧冠八强",
        source="体育周刊",
        publish_time="2026-01-28",
        author="李四",
        event_name="欧冠联赛",
        keywords=["欧冠", "皇马", "足球"],
        tags=["体育", "足球"],
    )
    await db.save_news(news2)
    logger.info(f"✅ 保存成功: {news2.title}")

    # 4. 测试批量保存
    logger.info("\n📦 测试批量保存...")
    news_batch = [
        NewsItem(
            title=f"测试新闻{i}",
            url=f"https://example.com/test/{i}",
            source="测试源",
            keywords=["测试"],
        )
        for i in range(3, 6)
    ]
    stats = await db.save_news_batch(news_batch)
    logger.info(f"✅ 批量保存完成: {stats}")

    # 5. 测试根据URL获取新闻
    logger.info("\n🔍 测试根据URL获取新闻...")
    found_news = await db.get_news_by_url(news1.url)
    if found_news:
        logger.info(f"✅ 找到新闻: {found_news.title}")
        logger.info(f"   关键词: {found_news.keywords}")
        logger.info(f"   本地图片: {found_news.local_image_paths}")
    else:
        logger.error("❌ 未找到新闻")

    # 6. 测试搜索功能
    logger.info("\n🔎 测试搜索功能...")

    # 搜索AI相关
    from mcp_server.news_storage.core.models import SearchFilter

    filter1 = SearchFilter(search_terms=["AI", "GPT"], limit=10)
    results1 = await db.search_news(filter1)
    logger.info(f"✅ 搜索 'AI GPT': 找到 {len(results1)} 条结果")
    for news in results1:
        logger.info(f"   - {news.title}")

    # 按来源筛选
    filter2 = SearchFilter(source="科技日报", limit=10)
    results2 = await db.search_news(filter2)
    logger.info(f"✅ 按来源 '科技日报' 筛选: 找到 {len(results2)} 条结果")

    # 按事件名称筛选
    filter3 = SearchFilter(event_name="欧冠联赛", limit=10)
    results3 = await db.search_news(filter3)
    logger.info(f"✅ 按事件 '欧冠联赛' 筛选: 找到 {len(results3)} 条结果")

    # 7. 测试获取最近新闻
    logger.info("\n📰 测试获取最近新闻...")
    recent = await db.get_recent_news(limit=5)
    logger.info(f"✅ 最近 {len(recent)} 条新闻:")
    for news in recent:
        logger.info(f"   - {news.title} ({news.created_at})")

    # 8. 测试更新新闻内容
    logger.info("\n✏️ 测试更新新闻内容...")
    success = await db.update_news_content(
        url=news1.url,
        content="更新后的完整内容...",
        html_content="<p>更新后的HTML内容</p>",
    )
    logger.info(f"{'✅ 更新成功' if success else '❌ 更新失败'}")

    # 9. 测试更新事件名称
    logger.info("\n🏷️ 测试更新事件名称...")
    success = await db.update_event_name(news2.url, "欧冠联赛2026")
    logger.info(f"{'✅ 事件名称更新成功' if success else '❌ 更新失败'}")

    # 10. 测试批量更新事件名称
    logger.info("\n📦 测试批量更新事件名称...")
    urls = [f"https://example.com/test/{i}" for i in range(3, 6)]
    batch_stats = await db.batch_update_event_name(urls, "测试事件2026")
    logger.info(f"✅ 批量更新事件名称: {batch_stats}")

    # 11. 测试获取统计信息
    logger.info("\n📊 测试获取统计信息...")
    stats = await db.get_stats()
    logger.info("✅ 统计信息:")
    logger.info(f"   总数: {stats['total']}")
    logger.info(f"   最近7天新增: {stats['recent_week']}")
    logger.info(f"   按来源分布: {stats['by_source']}")

    # 12. 测试删除新闻
    logger.info("\n🗑️ 测试删除新闻...")
    delete_url = "https://example.com/test/3"
    success = await db.delete_news(delete_url)
    logger.info(f"{'✅ 删除成功' if success else '❌ 删除失败'}: {delete_url}")

    # 13. 再次获取统计信息验证删除
    logger.info("\n📊 验证删除后的统计信息...")
    stats_after = await db.get_stats()
    logger.info(f"✅ 删除后总数: {stats_after['total']} (之前: {stats['total']})")

    # 14. 关闭数据库连接
    logger.info("\n🔒 关闭数据库连接...")
    await db.close()
    logger.info("✅ 测试完成！")


async def test_storage_tools():
    """测试存储工具函数"""
    from mcp_server.news_storage.tools.storage_tools import (
        save_news_tool,
        get_news_by_url_tool,
        search_news_tool,
        get_recent_news_tool,
    )

    logger.info("\n🔧 测试存储工具函数...")

    # 测试保存新闻工具
    result = json.loads(
        await save_news_tool(
            title="工具函数测试新闻",
            url="https://example.com/tool-test",
            summary="这是通过工具函数保存的新闻",
            source="测试源",
            keywords='["测试", "工具"]',
            tags='["测试"]',
        )
    )
    logger.info(f"✅ 保存工具结果: {result}")

    # 测试获取新闻工具
    result = json.loads(await get_news_by_url_tool("https://example.com/tool-test"))
    logger.info(f"✅ 获取工具结果: found={result.get('found')}")

    # 测试搜索工具
    result = json.loads(await search_news_tool(search="测试 工具", limit=10))
    logger.info(f"✅ 搜索工具结果: count={result.get('count')}")

    # 测试最近新闻工具
    result = json.loads(await get_recent_news_tool(limit=3))
    logger.info(f"✅ 最近新闻工具结果: count={result.get('count')}")


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )

    # 运行测试
    asyncio.run(test_database())
    asyncio.run(test_storage_tools())
