"""测试 MCP 工具注册"""
import asyncio
import sys

from mcp.server.fastmcp import FastMCP

# 导入服务器
from mcp_server.web_browser.main import server


async def check_tools():
    """检查已注册的工具"""
    print("=" * 60)
    print("MCP 服务器信息")
    print("=" * 60)
    print(f"服务器名称: {server.name}")
    print(f"服务器类型: {type(server)}")

    # 尝试不同的方式获取工具列表
    if hasattr(server, '_tools'):
        print(f"\n已注册工具数: {len(server._tools)}")
        for tool_name, tool_def in server._tools.items():
            print(f"  - {tool_name}: {tool_def}")
    elif hasattr(server, 'tools'):
        print(f"\n已注册工具数: {len(server.tools)}")
        for tool in server.tools:
            print(f"  - {tool}")
    else:
        print("\n无法获取工具列表")
        print(f"可用属性: {[attr for attr in dir(server) if not attr.startswith('__')]}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(check_tools())
