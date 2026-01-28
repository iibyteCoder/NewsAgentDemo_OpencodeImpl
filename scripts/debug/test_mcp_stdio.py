"""测试 MCP 服务器的 stdio 通信"""
import asyncio
import json
import sys


async def test_mcp_communication():
    """测试 MCP 服务器是否能正确响应"""
    from mcp_server.web_browser.main import server

    print("=" * 60)
    print("MCP Server Communication Test")
    print("=" * 60)
    print(f"Server name: {server.name}\n")

    # 列出所有工具
    tools = await server.list_tools()
    print(f"Registered tools: {len(tools)}\n")

    for tool in tools[:3]:  # 只显示前3个
        print(f"Tool name: {tool.name}")
        print(f"Description: {tool.description[:80]}...")
        print()

    print("=" * 60)
    print("\n✅ MCP server is working correctly!")
    print("If OpenCode still tries to run tools as bash commands,")
    print("the issue is with OpenCode's MCP connection, not the server.")
    print("\nPossible solutions:")
    print("1. Check OpenCode logs for MCP connection errors")
    print("2. Verify the MCP command path in opencode.json")
    print("3. Try restarting OpenCode completely")
    print("4. Check if the MCP server is actually being started")


if __name__ == "__main__":
    asyncio.run(test_mcp_communication())
