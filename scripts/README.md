# Scripts 目录

此目录包含所有测试、诊断和工具脚本。

## 目录结构

### `/tests/` - 测试脚本
- `test_mcp_server.py` - MCP 服务器单元测试
- `test_mcp_tools.py` - MCP 工具功能测试
- `test_mcp_registration.py` - 测试 MCP 工具注册
- `test_mcp_list_tools.py` - 列出所有已注册的 MCP 工具
- `verify_tool_names.py` - 验证工具名称格式
- `test_anti_scraping.py` - 反爬虫测试
- `test_concurrent.py` - 并发测试
- `test_engine_speed.py` - 搜索引擎速度测试
- `test_google_parser.py` - Google 解析器测试
- `test_multi_engine.py` - 多引擎测试
- `test_news_parsers.py` - 新闻解析器测试

### `/debug/` - 诊断脚本
- `check_mcp_tools.py` - 检查 MCP 工具注册情况
- `verify_config.py` - 验证 opencode.json 配置
- `diagnose_mcp.py` - MCP 服务器诊断
- `analyze_html.py` - HTML 结构分析
- `analyze_stable_structure.py` - 稳定结构分析
- `debug_baidu_news.py` - 百度新闻调试
- `debug_google.py` - Google 调试
- `debug_parsers.py` - 解析器调试

### `/tools/` - 工具脚本
- `collect_sports_news.py` - 体育新闻收集工具
- `manual_verify.py` - 手动验证工具
- `remove_data_images.py` - 删除数据图片
- `save_search_pages.py` - 保存搜索页面

### `/data/` - 数据目录
存储测试数据和运行时数据

### 根目录脚本
- `start_mcp_server.py` - 启动 MCP 服务器

## 使用方法

### 运行测试
```bash
# 运行所有测试
python -m pytest scripts/tests/

# 运行特定测试
python scripts/tests/test_mcp_tools.py
```

### 运行诊断
```bash
# 验证配置
python scripts/debug/verify_config.py

# 检查工具注册
python scripts/debug/check_mcp_tools.py
```

### 启动 MCP 服务器
```bash
python scripts/start_mcp_server.py
```
