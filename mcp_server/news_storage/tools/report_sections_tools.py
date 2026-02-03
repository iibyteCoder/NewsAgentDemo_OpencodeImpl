"""
报告部分工具函数 - 使用新的 Repository 模式
"""

import json

from loguru import logger

from ..db import ReportSectionRepository, SectionType, get_db_manager

# 全局仓储实例（延迟初始化）
_report_section_repo: ReportSectionRepository | None = None


def _get_report_section_repo() -> ReportSectionRepository:
    """获取报告部分仓储实例（单例）"""
    global _report_section_repo
    if _report_section_repo is None:
        db_manager = get_db_manager()
        _report_section_repo = ReportSectionRepository(db_manager)
    return _report_section_repo


async def save_report_section_tool(
    section_type: str,
    session_id: str,
    event_name: str,
    category: str,
    content_data: str,
) -> str:
    """保存报告部分 - 💾 存储分析结果到数据库

    【核心功能】
    - 保存报告部分的完整数据到数据库
    - 支持：验证结果、时间轴、预测、摘要、新闻列表、图片
    - 避免上下文过长，数据存储在数据库中
    - 返回 section_id 供后续使用

    【使用场景】
    - validator 完成验证后保存结果
    - timeline-builder 完成时间轴后保存结果
    - predictor 完成预测后保存结果

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
        content_data: 内容数据（任意格式字符串，无需严格 JSON）

    Returns:
        JSON格式：{success, section_id, message, section_type}
    """
    try:
        repo = _get_report_section_repo()

        # 验证 section_type
        if not SectionType.is_valid(section_type):
            valid_types = ", ".join(SectionType.all())
            return json.dumps(
                {
                    "success": False,
                    "error": f"无效的 section_type: {section_type}。有效值为: {valid_types}",
                },
                ensure_ascii=False,
                indent=2,
            )

        # 直接保存原始字符串（不解析 JSON，避免格式错误）
        section_id = await repo.save(
            section_type=section_type,
            session_id=session_id,
            event_name=event_name,
            category=category,
            content_data=content_data or "",
        )

        result = {
            "success": True,
            "section_id": section_id,
            "message": f"报告部分已保存: {section_type}",
            "section_type": section_type,
        }

        logger.info(f"✅ 保存报告部分: {section_type} - {event_name}")
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

    【核心功能】
    - 从数据库读取单个报告部分的完整数据
    - 用于报告生成时按需读取
    - 避免上下文传递大量数据

    【使用场景】
    - report-assembler 读取 validation 数据
    - report-assembler 读取 timeline 数据
    - report-assembler 读取 prediction 数据

    Args:
        session_id: 会话ID
        event_name: 事件名称
        section_type: 部分类型

    Returns:
        JSON格式：{success, found, section, content}
    """
    try:
        repo = _get_report_section_repo()

        section = await repo.get(session_id, event_name, section_type)

        if section:
            result = {
                "success": True,
                "found": True,
                "section": section.to_dict(),
            }
            logger.info(f"✅ 找到报告部分: {section_type} - {event_name}")
        else:
            result = {
                "success": True,
                "found": False,
                "section": None,
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

    【核心功能】
    - 获取事件的所有已保存部分
    - 返回各部分的完整数据
    - 用于报告组装器

    【使用场景】
    - report-assembler 获取所有部分数据

    Args:
        session_id: 会话ID
        event_name: 事件名称

    Returns:
        JSON格式：{success, count, sections}
    """
    try:
        repo = _get_report_section_repo()

        sections = await repo.get_all(session_id, event_name)

        result = {
            "success": True,
            "count": len(sections),
            "sections": [s.to_dict() for s in sections],
        }

        logger.info(f"✅ 获取所有报告部分: {event_name} 有 {len(sections)} 个部分")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取所有报告部分失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )


async def get_report_sections_summary_tool(session_id: str, event_name: str) -> str:
    """获取报告部分摘要 - 📊 状态概览

    【核心功能】
    - 获取事件各部分的状态摘要
    - 不包含完整内容，只包含状态信息
    - 用于检查哪些部分已完成

    【使用场景】
    - event-processor 检查各部分完成状态
    - report-assembler 确定哪些部分需要生成

    Args:
        session_id: 会话ID
        event_name: 事件名称

    Returns:
        JSON格式：{success, summary, total, completed, failed}
    """
    try:
        repo = _get_report_section_repo()

        summary = await repo.get_summary(session_id, event_name)

        # 统计状态
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

        logger.info(f"✅ 获取报告部分摘要: {event_name}")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ 获取报告部分摘要失败: {e}")
        return json.dumps(
            {"success": False, "error": str(e)}, ensure_ascii=False, indent=2
        )
