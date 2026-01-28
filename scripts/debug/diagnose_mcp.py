#!/usr/bin/env python
"""
诊断 MCP Server 连接问题
"""
import sys
import io
import asyncio

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def main():
    print("=" * 60)
    print("MCP Server 连接诊断")
    print("=" * 60)

    # 1. 检查服务器名称
    print("\n1. 检查服务器配置...")
    try:
        from mcp_server.web_browser.main import server
        print(f"   ✅ MCP服务器名称: {server.name}")

        # 2. 列出所有工具
        print("\n2. 列出已注册的工具...")
        tools = await server.list_tools()
        print(f"   ✅ 找到 {len(tools)} 个工具:")

        print("\n   工具名称列表:")
        for i, tool in enumerate(tools, 1):
            print(f"   {i:2d}. {tool.name}")

        # 3. 检查工具名称格式
        print("\n3. 检查工具名称格式...")
        print("\n   预期格式: <server-name>_<function-name>")
        print(f"   例如: {server.name}_baidu_news_search_tool")

        # 4. OpenCode配置
        print("\n4. OpenCode 配置要求...")
        print("   在 opencode.json 中:")
        print('   ```json')
        print('   "mcp": {')
        print(f'     "{server.name}": {{ "enabled": true }}')
        print('   },')
        print('   "agent": {')
        print('     "your-agent": {')
        print(f'       "tools": {{ "{server.name}_*": true }}')
        print('     }')
        print('   }')
        print('   ```')

        # 5. 模拟MCP协议通信
        print("\n5. 模拟MCP协议...")
        print("\n   当OpenCode连接到MCP服务器时:")
        print(f"   - 服务器名: {server.name}")
        print(f"   - 工具前缀: {server.name}_")
        print(f"   - 工具匹配模式: {server.name}_*")

        print("\n6. 配置文件检查...")
        import json
        from pathlib import Path

        config_path = Path("opencode.json")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 检查MCP配置
            if "mcp" in config:
                mcp_config = config["mcp"]
                print(f"\n   配置的MCP服务器: {list(mcp_config.keys())}")

                for server_name, server_config in mcp_config.items():
                    enabled = server_config.get("enabled", False)
                    print(f"   - {server_name}: {'✅ 启用' if enabled else '❌ 禁用'}")

            # 检查agent配置
            if "agent" in config:
                for agent_name, agent_config in config["agent"].items():
                    if "tools" in agent_config:
                        tools_config = agent_config["tools"]
                        matching_tools = [k for k in tools_config.keys() if server.name in k]
                        if matching_tools:
                            print(f"\n   Agent '{agent_name}' 的工具配置:")
                            for tool in matching_tools:
                                print(f"   - {tool}: {tools_config[tool]}")

        print("\n" + "=" * 60)
        print("✅ 诊断完成！")
        print("=" * 60)

        print("\n📋 结论:")
        print(f"1. MCP服务器内部名称: '{server.name}'")
        print(f"2. 工具注册前缀: '{server.name}_'")
        print(f"3. opencode.json应使用: '{server.name}' 作为服务器名")
        print(f"4. 工具配置应使用: '{server.name}_*' 匹配模式")
        print(f"\n5. 实际注册的工具名示例: '{server.name}_baidu_news_search_tool'")

        print("\n🚀 下一步:")
        print("如果配置正确但工具仍不可用，请:")
        print("1. 完全关闭VSCode")
        print("2. 重新打开VSCode")
        print("3. 重新加载项目")

    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
