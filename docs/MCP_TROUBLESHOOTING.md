# MCP 服务器问题排查与解决方案

## 问题：工具被当作 bash 命令执行

### 症状
```
/usr/bin/bash: -c: line 1: `web-browser_baidu_news_search_tool("体育运动新闻", 30)'
```

工具没有被识别为 MCP 工具，而是被当作普通的 bash 命令执行。

### 根本原因

1. **相对导入错误**：直接运行 `mcp_server/web_browser/main.py` 会报错：
   ```
   ImportError: attempted relative import with no known parent package
   ```

2. **Python 无法识别相对导入**：当使用 `python script.py` 运行脚本时，Python 不知道包结构，导致 `from .config.settings` 这类相对导入失败。

### 解决方案

使用 Python 的 `-m` 参数将模块作为脚本运行，这样可以正确处理相对导入。

在 `opencode.json` 中配置：

```json
{
  "mcp": {
    "web_browser": {
      "type": "local",
      "command": [".venv/Scripts/python.exe", "-m", "mcp_server.web_browser.main"],
      "enabled": true
    }
  }
}
```

### 为什么这样可以工作？

1. **模块运行方式**：`-m` 参数将 `mcp_server.web_browser.main` 作为模块运行，Python 能够正确识别包结构。

2. **相对导入正常**：当使用 `-m` 运行模块时，相对导入 `from .config.settings` 可以正常工作。

3. **无需额外文件**：不需要在根目录创建启动脚本，保持项目结构整洁。

4. **MCP stdio 通信**：FastMCP 的 `server.run()` 默认使用 stdio 传输，这是 OpenCode 期望的通信方式。

### 验证方法

运行以下命令测试 MCP 服务器：

```bash
.venv/Scripts/python.exe -m mcp_server.web_browser.main
```

应该看到类似输出：
```
🔧 浏览器池初始化: max_browsers=2, max_contexts=5, context_pool_size=10
🚀 Web Browser MCP Server 启动
   启用的搜索引擎: baidu, bing, sogou, google, 360
```

服务器会保持运行并等待 stdin 输入（MCP 协议）。

### 其他注意事项

1. **工具名称格式**：FastMCP 不会自动添加服务器名前缀，需要在 `@server.tool()` 装饰器中手动指定：
   ```python
   @server.tool(name="web-browser_baidu_search_tool")
   async def baidu_search_tool(...):
       ...
   ```

2. **OpenCode 配置**：在 opencode.json 中启用工具：
   ```json
   "tools": {
     "web-browser*": true
   }
   ```

3. **重启 OpenCode**：修改配置后需要完全关闭并重新打开 VSCode 才能生效。

### 相关文件

- 启动脚本：`start_web_browser_mcp.py`
- MCP 服务器：`mcp_server/web_browser/main.py`
- 配置文件：`opencode.json`
- 测试脚本：`scripts/debug/test_mcp_path.py`
