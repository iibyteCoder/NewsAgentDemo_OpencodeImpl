"""验证所有工具名称"""
import asyncio
from mcp_server.web_browser.main import server


async def main():
    tools = await server.list_tools()
    print(f"Total tools: {len(tools)}\n")
    for tool in tools:
        print(f"  {tool.name}")

    # 验证所有工具都有前缀
    expected_prefix = "web-browser_"
    invalid_tools = [t.name for t in tools if not t.name.startswith(expected_prefix)]

    if invalid_tools:
        print(f"\n❌ 以下工具缺少前缀 '{expected_prefix}':")
        for name in invalid_tools:
            print(f"  - {name}")
    else:
        print(f"\n✅ 所有工具都有正确的前缀 '{expected_prefix}'")


if __name__ == "__main__":
    asyncio.run(main())
