"""
分层导航工具 - 使用新的 Repository 模式
"""

import json

from loguru import logger

from ..db import NewsRepository, get_db_manager

# 全局仓储实例（延迟初始化）
_news_repo: NewsRepository | None = None


def _get_news_repo() -> NewsRepository:
    """获取新闻仓储实例（单例）"""
    global _news_repo
    if _news_repo is None:
        db_manager = get_db_manager()
        _news_repo = NewsRepository(db_manager)
    return _news_repo


async def list_categories_tool(session_id: str) -> str:
    """列出本次会话中的所有新闻类别 - 第一步：了解数据维度

    【何时使用】
    - 开始探索数据库时首先调用
    - 了解本次会话中有哪些类别（科技/体育/财经/...）

    【使用流程】
    1. 调用此工具获取类别列表
    2. 选择感兴趣的类别
    3. 调用 news_storage_list_events_by_category 查看该类别的事件

    Args:
        session_id: 会话ID（必须传入）

    Returns:
        JSON格式：{"success": true, "categories": [{"name": "科技", "count": 85, "events": 12}]}
    """
    try:
        repo = _get_news_repo()

        if not session_id:
            return json.dumps(
                {"success": False, "error": "session_id 是必填参数"},
                ensure_ascii=False,
                indent=2,
            )

        categories = await repo.get_categories(session_id)

        result = {
            "success": True,
            "categories": categories,
        }

        logger.info(f"✅ 获取类别列表: {len(categories)} 个类别")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取类别失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)},
            ensure_ascii=False,
            indent=2,
        )


async def list_events_by_category_tool(
    session_id: str, category: str, limit: int = 20
) -> str:
    """列出某个类别下的所有事件 - 第二步：按类别浏览事件

    【何时使用】
    - 已调用 news_storage_list_categories 了解有哪些类别
    - 想查看某个类别下有哪些事件

    【使用流程】
    1. 从 list_categories 的返回值中选择一个 category
    2. 调用此工具获取该类别下的事件列表
    3. 选择感兴趣的事件，调用 news_storage_list_news_by_event 查看新闻

    Args:
        session_id: 会话ID（必须传入）
        category: 类别名称（从 list_categories 获取）
        limit: 最大返回数量（默认20）

    Returns:
        JSON格式：{"success": true, "category": "科技", "events": [...]}
    """
    try:
        repo = _get_news_repo()

        if not session_id:
            return json.dumps(
                {"success": False, "error": "session_id 是必填参数"},
                ensure_ascii=False,
                indent=2,
            )

        if not category:
            return json.dumps(
                {"success": False, "error": "category 是必填参数"},
                ensure_ascii=False,
                indent=2,
            )

        events = await repo.get_events_by_category(session_id, category, limit)

        result = {
            "success": True,
            "category": category,
            "events": events,
        }

        logger.info(f"✅ 获取事件列表: {category} 类别有 {len(events)} 个事件")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取事件列表失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)},
            ensure_ascii=False,
            indent=2,
        )


async def list_news_by_event_tool(
    session_id: str, event_name: str, limit: int = 50
) -> str:
    """列出某个事件下的新闻（轻量级）- 第三步：查看新闻列表

    【何时使用】
    - 已调用 news_storage_list_events_by_category 了解有哪些事件
    - 想查看某个事件下的具体新闻

    【使用流程】
    1. 从 list_events_by_category 的返回值中选择一个 event_name
    2. 调用此工具获取该事件下的新闻列表（轻量级，包含图片URL）
    3. 根据标题和摘要，选择感兴趣的新闻
    4. 调用 news_storage_get_by_url 获取完整内容（包括 content）

    Args:
        session_id: 会话ID（必须传入）
        event_name: 事件名称（从 list_events_by_category 获取）
        limit: 最大返回数量（默认50）

    Returns:
        JSON格式：{"success": true, "event_name": "...", "news": [...]}
    """
    try:
        repo = _get_news_repo()

        if not session_id:
            return json.dumps(
                {"success": False, "error": "session_id 是必填参数"},
                ensure_ascii=False,
                indent=2,
            )

        if not event_name:
            return json.dumps(
                {"success": False, "error": "event_name 是必填参数"},
                ensure_ascii=False,
                indent=2,
            )

        news_list = await repo.get_news_by_event(session_id, event_name, limit)

        # 转换 image_urls 字典为列表
        for news in news_list:
            news["image_urls"] = list(news.get("image_urls", {}).values())

        result = {
            "success": True,
            "event_name": event_name,
            "count": len(news_list),
            "news": news_list,
        }

        logger.info(f"✅ 获取新闻列表: {event_name} 有 {len(news_list)} 条新闻")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取新闻列表失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)},
            ensure_ascii=False,
            indent=2,
        )


async def get_images_by_event_tool(session_id: str, event_name: str) -> str:
    """获取事件下所有新闻的图片URL - 用于报告生成

    【何时使用】
    - 生成报告时需要获取某个事件的所有图片
    - 需要下载事件相关的图片素材

    【使用流程】
    1. 调用此工具获取事件的所有图片URL
    2. 使用 downloader 工具批量下载图片
    3. 在报告中引用本地图片路径

    Args:
        session_id: 会话ID（必须传入）
        event_name: 事件名称（从 list_events_by_category 获取）

    Returns:
        JSON格式：{
            "success": true,
            "event_name": "AI技术突破",
            "count": 25,
            "images": [
                {
                    "url": "https://example.com/img1.jpg",
                    "source_news_title": "AI芯片技术重大突破",
                    "source_news_url": "https://example.com/news/1"
                },
                ...
            ]
        }
    """
    try:
        repo = _get_news_repo()

        if not session_id:
            return json.dumps(
                {"success": False, "error": "session_id 是必填参数"},
                ensure_ascii=False,
                indent=2,
            )

        if not event_name:
            return json.dumps(
                {"success": False, "error": "event_name 是必填参数"},
                ensure_ascii=False,
                indent=2,
            )

        images = await repo.get_images_by_event(session_id, event_name)

        result = {
            "success": True,
            "event_name": event_name,
            "count": len(images),
            "images": images,
        }

        logger.info(f"✅ 获取图片列表: {event_name} 有 {len(images)} 张图片")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取图片列表失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)},
            ensure_ascii=False,
            indent=2,
        )
