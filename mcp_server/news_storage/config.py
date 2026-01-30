"""
News Storage MCP Server 工具分类配置

通过环境变量控制哪些工具组被启用，避免一次性加载过多工具。
"""

import os
from typing import Set


class ToolConfig:
    """工具配置管理器"""

    # 工具组定义
    TOOL_GROUPS = {
        "basic": {
            "name": "基础存储工具",
            "description": "新闻的保存、读取、搜索等基础操作",
            "tools": {
                "news-storage_save",
                "news-storage_save_batch",
                "news-storage_get_by_url",
                "news-storage_search",
                "news-storage_get_recent",
                "news-storage_update_content",
                "news-storage_delete",
                "news-storage_stats",
                "news-storage_update_event_name",
                "news-storage_batch_update_event_name",
            },
        },
        "navigation": {
            "name": "分层导航工具",
            "description": "按类别→事件→新闻的层级浏览",
            "tools": {
                "news-storage_list_categories",
                "news-storage_list_events_by_category",
                "news-storage_list_news_by_event",
                "news-storage_get_images_by_event",
            },
        },
        "report_sections": {
            "name": "报告部分工具",
            "description": "新版架构：保存和读取报告各部分数据",
            "tools": {
                "news-storage_save_report_section",
                "news-storage_get_report_section",
                "news-storage_get_all_report_sections",
                "news-storage_get_report_sections_summary",
                "news-storage_mark_section_failed",
            },
        },
    }

    @classmethod
    def get_enabled_groups(cls) -> Set[str]:
        """获取启用的工具组

        通过环境变量 NEWS_STORAGE_ENABLED_GROUPS 控制，格式：逗号分隔的组名
        例如：export NEWS_STORAGE_ENABLED_GROUPS=basic,navigation

        默认：所有组都启用
        """
        enabled_str = os.getenv("NEWS_STORAGE_ENABLED_GROUPS", "")
        if not enabled_str:
            return set(cls.TOOL_GROUPS.keys())

        enabled = {g.strip() for g in enabled_str.split(",")}
        # 验证组名
        invalid = enabled - set(cls.TOOL_GROUPS.keys())
        if invalid:
            raise ValueError(f"无效的工具组: {invalid}. 可用的组: {list(cls.TOOL_GROUPS.keys())}")

        return enabled

    @classmethod
    def is_tool_enabled(cls, tool_name: str) -> bool:
        """检查工具是否启用

        Args:
            tool_name: 工具名称（带前缀）

        Returns:
            是否启用
        """
        enabled_groups = cls.get_enabled_groups()

        for group_name, group_config in cls.TOOL_GROUPS.items():
            if group_name not in enabled_groups:
                continue
            if tool_name in group_config["tools"]:
                return True

        return False

    @classmethod
    def get_enabled_tools(cls) -> Set[str]:
        """获取所有启用的工具名称

        Returns:
            启用的工具名称集合
        """
        enabled_groups = cls.get_enabled_groups()
        enabled_tools: Set[str] = set()

        for group_name in enabled_groups:
            enabled_tools.update(cls.TOOL_GROUPS[group_name]["tools"])

        return enabled_tools

    @classmethod
    def print_config(cls):
        """打印当前配置（用于调试）"""
        enabled_groups = cls.get_enabled_groups()
        enabled_tools = cls.get_enabled_tools()

        print("=" * 60)
        print("News Storage MCP Server 工具配置")
        print("=" * 60)
        print(f"启用的工具组: {', '.join(enabled_groups)}")
        print(f"启用的工具数量: {len(enabled_tools)}")
        print()

        for group_name in enabled_groups:
            group = cls.TOOL_GROUPS[group_name]
            print(f"【{group['name']}】({group_name})")
            print(f"  描述: {group['description']}")
            print(f"  工具: {len(group['tools'])} 个")
            for tool in sorted(group['tools']):
                print(f"    - {tool}")
            print()

        print("=" * 60)


# 使用示例
if __name__ == "__main__":
    # 打印默认配置（所有工具）
    ToolConfig.print_config()

    # 模拟只启用基础和导航工具
    os.environ["NEWS_STORAGE_ENABLED_GROUPS"] = "basic,navigation"
    print("\n只启用 basic 和 navigation 工具组:")
    print("-" * 60)
    ToolConfig.print_config()
