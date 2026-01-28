"""测试 MCP 工具注册 - 使用 list_tools"""
import asyncio
import sys

from mcp.server.fastmcp import FastMCP

# 导入服务器
from mcp_server.web_browser.main import server


async def check_tools():
    """检查已注册的工具"""
    print("=" * 60)
    print("MCP 服务器工具列表")
    print("=" * 60)
    print(f"服务器名称: {server.name}\n")

    # 使用 list_tools 方法
    tools = await server.list_tools()

    print(f"已注册工具数: {len(tools)}\n")

    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"  Description: {tool.description[:100]}...")
        print()

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_tools())
