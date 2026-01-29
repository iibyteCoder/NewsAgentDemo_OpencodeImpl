"""测试关键词搜索优化 - 验证存储和搜索的一致性"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import json
from loguru import logger
from mcp_server.news_storage.core.database import get_database
from mcp_server.news_storage.core.models import NewsItem, SearchFilter


def test_keyword_search():
    """测试关键词搜索功能"""

    logger.info("🧪 开始测试关键词搜索优化")

    db = get_database()

    # 1. 清空测试数据（可选）
    # logger.info("📝 准备测试数据...")

    # 2. 保存测试新闻
    test_news = [
        NewsItem(
            title="英超六队进欧冠淘汰赛",
            url="https://test.com/news/1",
            summary="英超球队在欧冠中表现出色",
            source="测试来源1",
            keywords=["欧冠", "英超", "淘汰赛", "历史意义"],
        ),
        NewsItem(
            title="AI技术取得重大突破",
            url="https://test.com/news/2",
            summary="人工智能领域迎来新进展",
            source="测试来源2",
            keywords=["AI", "技术", "突破"],
        ),
        NewsItem(
            title="皇马巴黎圣日耳曼淘汰赛恢复能力分析",
            url="https://test.com/news/3",
            summary="两支豪门球队的淘汰赛表现",
            source="测试来源3",
            keywords=["皇马", "巴黎圣日耳曼", "淘汰赛", "恢复能力"],
        ),
    ]

    # 保存测试数据
    for news in test_news:
        db.save_news(news)
    logger.success(f"✅ 保存了 {len(test_news)} 条测试新闻")

    # 3. 测试不同的搜索方式

    # 测试1: 使用 keywords 参数（精确匹配关键词字段）
    logger.info("\n🔍 测试1: 使用 keywords 参数搜索 ['欧冠', '英超']")
    filter1 = SearchFilter(keywords=["欧冠", "英超"], limit=10)
    results1 = db.search_news(filter1)
    logger.info(f"   找到 {len(results1)} 条结果:")
    for r in results1:
        logger.info(f"   - {r.title} | keywords: {r.keywords}")

    # 测试2: 使用 keywords 参数搜索单个关键词
    logger.info("\n🔍 测试2: 使用 keywords 参数搜索 ['AI']")
    filter2 = SearchFilter(keywords=["AI"], limit=10)
    results2 = db.search_news(filter2)
    logger.info(f"   找到 {len(results2)} 条结果:")
    for r in results2:
        logger.info(f"   - {r.title} | keywords: {r.keywords}")

    # 测试3: 使用 keywords 参数搜索多个关键词（任意匹配）
    logger.info("\n🔍 测试3: 使用 keywords 参数搜索 ['皇马', 'AI']（应该找到2条）")
    filter3 = SearchFilter(keywords=["皇马", "AI"], limit=10)
    results3 = db.search_news(filter3)
    logger.info(f"   找到 {len(results3)} 条结果:")
    for r in results3:
        logger.info(f"   - {r.title} | keywords: {r.keywords}")

    # 测试4: 使用 keyword 参数（全文模糊搜索）
    logger.info("\n🔍 测试4: 使用 keyword 参数全文搜索 '淘汰赛'")
    filter4 = SearchFilter(keyword="淘汰赛", limit=10)
    results4 = db.search_news(filter4)
    logger.info(f"   找到 {len(results4)} 条结果:")
    for r in results4:
        logger.info(f"   - {r.title} | summary: {r.summary[:30]}...")

    # 测试5: 组合使用 keyword 和 keywords
    logger.info("\n🔍 测试5: 组合使用 keyword='技术' 和 keywords=['欧冠']")
    filter5 = SearchFilter(keyword="技术", keywords=["欧冠"], limit=10)
    results5 = db.search_news(filter5)
    logger.info(f"   找到 {len(results5)} 条结果:")
    for r in results5:
        logger.info(f"   - {r.title} | keywords: {r.keywords}")

    # 4. 验证结果
    logger.info("\n✅ 测试完成！")
    logger.info("📊 结果分析:")
    logger.info(f"   - keywords=['欧冠', '英超']: 找到 {len(results1)} 条（应为1条）")
    logger.info(f"   - keywords=['AI']: 找到 {len(results2)} 条（应为1条）")
    logger.info(f"   - keywords=['皇马', 'AI']: 找到 {len(results3)} 条（应为2条）")
    logger.info(f"   - keyword='淘汰赛': 找到 {len(results4)} 条（应为3条，标题和摘要都包含）")
    logger.info(f"   - 组合搜索: 找到 {len(results5)} 条（应为0条，没有同时满足的）")

    # 清理测试数据
    logger.info("\n🧹 清理测试数据...")
    for news in test_news:
        db.delete_news(news.url)
    logger.success("✅ 测试数据已清理")


if __name__ == "__main__":
    test_keyword_search()
