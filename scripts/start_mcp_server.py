#!/usr/bin/env python
"""
启动 Web Browser MCP Server

提供智能浏览器与搜索功能：
- 多引擎搜索（百度、必应、搜狗、谷歌、360）
- 网页内容获取与解析
- 热点追踪

使用方法:
    python start_mcp_server.py
"""

import sys
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

if __name__ == "__main__":
    from mcp_server.web_browser.main import server
    server.run()
