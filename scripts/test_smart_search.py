"""测试智能搜索功能 - 一个参数搞定所有搜索"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from loguru import logger
from mcp_server.news_storage.core.database import get_database
from mcp_server.news_storage.core.models import NewsItem, SearchFilter


def test_smart_search():
    """测试智能搜索功能"""

    logger.info("🧪 开始测试智能搜索功能")

    db = get_database()

    # 1. 保存测试新闻
    test_news = [
        NewsItem(
            title="英超六队进欧冠淘汰赛",
            url="https://test.com/news/1",
            summary="英超球队在欧冠中表现出色",
            source="体育周刊",
            keywords=["欧冠", "英超", "淘汰赛", "历史意义"],
        ),
        NewsItem(
            title="AI技术取得重大突破",
            url="https://test.com/news/2",
            summary="人工智能领域迎来新进展，机器学习算法优化",
            source="科技日报",
            keywords=["AI", "技术", "突破", "机器学习"],
        ),
        NewsItem(
            title="皇马巴黎圣日耳曼淘汰赛恢复能力分析",
            url="https://test.com/news/3",
            summary="两支豪门球队在欧冠淘汰赛的恢复能力对比",
            source="足球报",
            keywords=["皇马", "巴黎圣日耳曼", "欧冠", "淘汰赛", "恢复能力"],
        ),
        NewsItem(
            title="阿森纳伤病频发考验阵容深度",
            url="https://test.com/news/4",
            summary="英超阿森纳球队遭遇伤病危机，阵容深度面临考验",
            source="体育新闻",
            keywords=["阿森纳", "英超", "伤病", "阵容深度"],
        ),
    ]

    # 保存测试数据
    for news in test_news:
        db.save_news(news)
    logger.success(f"✅ 保存了 {len(test_news)} 条测试新闻")

    # 2. 测试不同的搜索场景

    # 测试1: 单个词搜索
    logger.info("\n🔍 测试1: 单个词搜索 '欧冠'")
    filter1 = SearchFilter(search_terms=["欧冠"], limit=10)
    results1 = db.search_news(filter1)
    logger.info(f"   找到 {len(results1)} 条结果:")
    for r in results1:
        logger.info(f"   - {r.title} | keywords: {r.keywords}")

    # 测试2: 多个词搜索（空格分词，OR关系）
    logger.info("\n🔍 测试2: 多个词搜索 '皇马 巴黎 淘汰赛'")
    filter2 = SearchFilter(search_terms=["皇马", "巴黎", "淘汰赛"], limit=10)
    results2 = db.search_news(filter2)
    logger.info(f"   找到 {len(results2)} 条结果:")
    for r in results2:
        logger.info(f"   - {r.title} | keywords: {r.keywords}")

    # 测试3: 搜索不同字段
    logger.info("\n🔍 测试3: 搜索内容字段 '机器学习'")
    filter3 = SearchFilter(search_terms=["机器学习"], limit=10)
    results3 = db.search_news(filter3)
    logger.info(f"   找到 {len(results3)} 条结果:")
    for r in results3:
        logger.info(f"   - {r.title} | summary: {r.summary[:40]}...")

    # 测试4: 组合搜索（搜索词 + 来源）
    logger.info("\n🔍 测试4: 组合搜索 '英超' + source='体育周刊'")
    filter4 = SearchFilter(search_terms=["英超"], source="体育周刊", limit=10)
    results4 = db.search_news(filter4)
    logger.info(f"   找到 {len(results4)} 条结果:")
    for r in results4:
        logger.info(f"   - {r.title} | source: {r.source}")

    # 测试5: 验证覆盖范围
    logger.info("\n🔍 测试5: 验证所有字段都能被搜索 '阵容深度'")
    filter5 = SearchFilter(search_terms=["阵容深度"], limit=10)
    results5 = db.search_news(filter5)
    logger.info(f"   找到 {len(results5)} 条结果:")
    for r in results5:
        logger.info(f"   - {r.title} | keywords: {r.keywords}")

    # 6. 验证结果
    logger.info("\n✅ 测试完成！")
    logger.info("📊 验证结果:")
    logger.info(f"   - '欧冠' 在标题和keywords中: {len(results1)} 条")
    logger.info(f"   - 多词搜索(OR关系): {len(results2)} 条")
    logger.info(f"   - 内容字段搜索: {len(results3)} 条")
    logger.info(f"   - 组合筛选: {len(results4)} 条")
    logger.info(f"   - keywords字段搜索: {len(results5)} 条")

    # 清理测试数据
    logger.info("\n🧹 清理测试数据...")
    for news in test_news:
        db.delete_news(news.url)
    logger.success("✅ 测试数据已清理")


if __name__ == "__main__":
    test_smart_search()
