"""
报告部分存储工具函数

提供 MCP 工具接口，用于保存和获取报告部分数据。
"""

import json
from loguru import logger

from ..core.database import get_database
from ..core.report_sections_database import ReportSectionsDatabase


async def save_report_section_tool(
    section_type: str,
    session_id: str,
    event_name: str,
    category: str,
    content_data: str,
) -> str:
    """保存报告部分 - 💾 存储分析结果

    功能：
    - 保存报告部分的完整数据到数据库
    - 支持：验证结果、时间轴、预测、摘要、新闻列表、图片
    - 避免上下文过长，数据存储在数据库中
    - 返回 section_id 供后续使用

    Args:
        section_type: 部分类型
            - "validation": 真实性验证结果
            - "timeline": 事件时间轴
            - "prediction": 趋势预测
            - "summary": 事件摘要
            - "news": 新闻列表
            - "images": 图片列表
        session_id: 会话ID
        event_name: 事件名称
        category: 类别
        content_data: 内容数据（JSON字符串）

    Returns:
        JSON格式的操作结果，包含：
        - success: 是否成功
        - section_id: 部分唯一标识
        - message: 结果消息

    Examples:
        >>> # 保存验证结果
        >>> save_report_section_tool(
        ...     section_type="validation",
        ...     session_id="20260130-abc123",
        ...     event_name="美国大选",
        ...     category="政治",
        ...     content_data='{"credibility_score": 85, "evidence_chain": [...]}'
        ... )

        >>> # 保存时间轴
        >>> save_report_section_tool(
        ...     section_type="timeline",
        ...     session_id="20260130-abc123",
        ...     event_name="美国大选",
        ...     category="政治",
        ...     content_data='{"milestones": [...], "development_path": "..."}'
        ... )
    """
    try:
        db = await get_database()
        sections_db = ReportSectionsDatabase(db)

        # 解析内容数据
        content = json.loads(content_data) if content_data else {}

        # 保存
        section_id = await sections_db.save_section(
            section_type=section_type,
            session_id=session_id,
            event_name=event_name,
            category=category,
            content_data=content,
        )

        result = {
            "success": True,
            "section_id": section_id,
            "message": f"报告部分已保存: {section_type}",
            "section_type": section_type,
        }

        logger.info(f"✅ 报告部分已保存: {section_type} - {event_name}")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 保存报告部分失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def get_report_section_tool(
    session_id: str, event_name: str, section_type: str
) -> str:
    """获取报告部分 - 🔍 读取分析结果

    功能：
    - 从数据库读取单个报告部分的完整数据
    - 用于报告生成时按需读取
    - 避免上下文传递大量数据

    Args:
        session_id: 会话ID
        event_name: 事件名称
        section_type: 部分类型

    Returns:
        JSON格式的部分数据，包含：
        - success: 是否成功
        - found: 是否找到
        - section: 部分数据（如果找到）
        - content: 内容数据（解析后的字典）

    Examples:
        >>> # 获取验证结果
        >>> get_report_section_tool(
        ...     session_id="20260130-abc123",
        ...     event_name="美国大选",
        ...     section_type="validation"
        ... )
    """
    try:
        db = await get_database()
        sections_db = ReportSectionsDatabase(db)

        section = await sections_db.get_section(session_id, event_name, section_type)

        if section:
            content = section.get_content()
            result = {
                "success": True,
                "found": True,
                "section": {
                    "section_id": section.section_id,
                    "section_type": section.section_type,
                    "session_id": section.session_id,
                    "event_name": section.event_name,
                    "category": section.category,
                    "status": section.status,
                    "created_at": section.created_at,
                    "updated_at": section.updated_at,
                },
                "content": content,
            }
            logger.info(f"✅ 找到报告部分: {section_type} - {event_name}")
        else:
            result = {
                "success": True,
                "found": False,
                "section": None,
                "content": None,
            }
            logger.info(f"⚠️ 未找到报告部分: {section_type} - {event_name}")

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取报告部分失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def get_all_report_sections_tool(session_id: str, event_name: str) -> str:
    """获取事件的所有报告部分 - 📋 完整概览

    功能：
    - 获取事件的所有已保存部分
    - 返回各部分的完整数据
    - 用于报告组装器

    Args:
        session_id: 会话ID
        event_name: 事件名称

    Returns:
        JSON格式的结果，包含：
        - success: 是否成功
        - count: 部分数量
        - sections: 部分列表（包含内容和元数据）

    Examples:
        >>> # 获取事件的所有部分
        >>> get_all_report_sections_tool(
        ...     session_id="20260130-abc123",
        ...     event_name="美国大选"
        ... )
    """
    try:
        db = await get_database()
        sections_db = ReportSectionsDatabase(db)

        sections = await sections_db.get_all_sections(session_id, event_name)

        result_sections = []
        for section in sections:
            result_sections.append(
                {
                    "section_id": section.section_id,
                    "section_type": section.section_type,
                    "session_id": section.session_id,
                    "event_name": section.event_name,
                    "category": section.category,
                    "status": section.status,
                    "created_at": section.created_at,
                    "updated_at": section.updated_at,
                    "content": section.get_content(),
                }
            )

        result = {
            "success": True,
            "count": len(result_sections),
            "sections": result_sections,
        }

        logger.info(f"✅ 获取所有报告部分: {event_name}, 共 {len(result_sections)} 个")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取所有报告部分失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def get_report_sections_summary_tool(session_id: str, event_name: str) -> str:
    """获取报告部分摘要 - 📊 状态概览

    功能：
    - 获取事件各部分的状态摘要
    - 不包含完整内容，只包含状态信息
    - 用于检查哪些部分已完成

    Args:
        session_id: 会话ID
        event_name: 事件名称

    Returns:
        JSON格式的摘要，包含：
        - success: 是否成功
        - summary: 各部分状态字典
        - total: 总数
        - completed: 完成数量
        - failed: 失败数量

    Examples:
        >>> # 检查事件各部分状态
        >>> get_report_sections_summary_tool(
        ...     session_id="20260130-abc123",
        ...     event_name="美国大选"
        ... )
    """
    try:
        db = await get_database()
        sections_db = ReportSectionsDatabase(db)

        summary = await sections_db.get_sections_summary(session_id, event_name)

        total = len(summary)
        completed = sum(1 for s in summary.values() if s["status"] == "completed")
        failed = sum(1 for s in summary.values() if s["status"] == "failed")

        result = {
            "success": True,
            "summary": summary,
            "total": total,
            "completed": completed,
            "failed": failed,
        }

        logger.info(f"✅ 获取报告部分摘要: {event_name}, {completed}/{total} 完成")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取报告部分摘要失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def mark_section_failed_tool(
    session_id: str, event_name: str, section_type: str, error_message: str
) -> str:
    """标记报告部分失败 - ❌ 记录错误

    功能：
    - 标记某个部分生成失败
    - 记录错误信息
    - 用于后续错误处理

    Args:
        session_id: 会话ID
        event_name: 事件名称
        section_type: 部分类型
        error_message: 错误信息

    Returns:
        JSON格式的操作结果

    Examples:
        >>> # 标记验证失败
        >>> mark_section_failed_tool(
        ...     session_id="20260130-abc123",
        ...     event_name="美国大选",
        ...     section_type="validation",
        ...     error_message="无法获取足够的验证信息"
        ... )
    """
    try:
        db = await get_database()
        sections_db = ReportSectionsDatabase(db)

        await sections_db.mark_section_failed(
            session_id=session_id,
            event_name=event_name,
            section_type=section_type,
            error_message=error_message,
        )

        result = {
            "success": True,
            "message": f"已标记部分失败: {section_type}",
            "section_type": section_type,
        }

        logger.warning(f"⚠️ 标记部分失败: {section_type} - {event_name}")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 标记部分失败时出错: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )
