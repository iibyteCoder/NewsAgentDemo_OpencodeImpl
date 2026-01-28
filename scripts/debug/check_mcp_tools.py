#!/usr/bin/env python
"""
检查 MCP Server 实际注册的工具列表
"""
import sys
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from mcp_server.web_browser.main import server

async def check_tools():
    """检查注册的工具"""
    print("=" * 60)
    print("MCP Server 实际注册的工具列表")
    print("=" * 60)

    print(f"\n服务器名称: {server.name}\n")

    # 使用 list_tools 方法获取工具列表
    tools = await server.list_tools()

    print(f"已注册的工具 ({len(tools)} 个):\n")

    for tool in tools:
        print(f"  🔧 {tool.name}")
        if tool.description:
            print(f"     描述: {tool.description[:80]}...")
        print()

    print("=" * 60)
    print("配置问题分析:")
    print("=" * 60)

    print("\n❌ 当前 opencode.json 配置:")
    print('   "web-browser_*": true')
    print("   (连字符 + 单星号)")

    print("\n✅ 正确的配置应该是:")
    print('   "web_browser__*": true')
    print("   (双下划线 + 双星号)")
    print("\n或者更宽松的配置:")
    print('   "*__*": true')
    print("   (匹配所有MCP工具)")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_tools())
