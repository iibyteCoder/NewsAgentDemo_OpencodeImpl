# NewsAgent Demo - 智能新闻聚合系统

一个基于 OpenCode 和 MCP (Model Context Protocol) 架构的智能新闻收集、分析和报告生成系统。

## 特性

- **多源新闻聚合**：自动从多个搜索引擎和网站收集新闻
- **智能事件聚合**：将相关新闻聚合成事件，识别关键信息
- **事件真实性验证**：主动探索验证事件真实性，交叉验证多个来源
- **时间轴构建**：构建事件发展的完整时间脉络
- **趋势预测**：基于历史数据和当前趋势预测事件未来发展
- **结构化报告生成**：自动生成包含时间轴、验证结果、预测分析的结构化报告
- **本地图片存储**：支持将新闻中的图片下载到本地，生成可离线查看的报告

## 架构

### MCP 服务器

项目包含三个 MCP 服务器，提供底层工具支持：

#### 1. Web Browser Server

- 网页内容抓取和解析
- 支持多种内容提取库（Trafilatura、Newspaper3k、Playwright、BeautifulSoup4）
- 智能内容清洗和提取

#### 2. Downloader Server

- 异步文件下载（支持单文件和批量下载）
- 图片批量下载和提取
- 异步文件操作，高性能

#### 3. News Storage Server

- 基于 SQLite + aiosqlite 的异步数据库
- 新闻数据持久化存储
- 支持按事件、来源、关键词等多维度搜索
- 自动去重（基于 URL）
- 图片 URL 和本地路径分离存储

### Agent 系统

采用事件驱动的多 Agent 架构：

#### 主 Agent

- **news-collector**：新闻收集智能体（S级）
  - 搜索和收集新闻
  - 调用子 Agent 进行深度分析
  - 生成最终报告

#### 子 Agent

- **event-aggregator**：事件聚合器
  - 将多条相关新闻聚合成事件
  - 识别事件的核心信息

- **validator**：事件验证器
  - 主动探索验证事件真实性
  - 交叉验证多个来源
  - 评估可信度

- **timeline-builder**：时间轴构建器
  - 构建事件发展的完整脉络
  - 按时间顺序组织关键事件
  - 主动探索补充缺失信息

- **predictor**：趋势预测器
  - 基于历史数据预测未来发展
  - 分析潜在影响和趋势

- **synthesizer**：报告生成器
  - 生成结构化 Markdown 报告
  - 整合时间轴、验证结果、预测分析
  - 下载并引用本地图片

- **event-processor**：事件处理器
  - 并发调度验证、时间轴、预测 Agent
  - 提高处理效率

## 技术栈

- **Python**: 3.13+
- **异步框架**: aiosqlite, aiofiles, httpx
- **内容提取**: Trafilatura, Newspaper3k, Playwright, BeautifulSoup4, lxml
- **MCP 框架**: Model Context Protocol
- **数据库**: SQLite (异步)
- **日志**: Loguru
- **包管理**: uv

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd OpencodeTest_1
```

### 2. 安装依赖

使用 uv（推荐）：

```bash
uv sync
```

或使用 pip：

```bash
pip install -e .
```

### 3. 安装 Playwright 浏览器

```bash
playwright install
```

## 配置

编辑 `opencode.json` 文件配置 MCP 服务器和 Agent：

```json
{
  "mcp": {
    "web_browser": {
      "command": [".venv/Scripts/python.exe", "-m", "mcp_server.web_browser.main"],
      "enabled": true
    },
    "downloader": {
      "command": [".venv/Scripts/python.exe", "-m", "mcp_server.downloader.main"],
      "enabled": true
    },
    "news_storage": {
      "command": [".venv/Scripts/python.exe", "-m", "mcp_server.news_storage.main"],
      "enabled": true
    }
  }
}
```

## 使用

### 启动新闻收集 Agent

```bash
# 使用 OpenCode CLI 启动
opencode agent news-collector
```

### MCP 工具使用示例

#### 保存新闻

```python
# news_storage_save
{
  "title": "AI技术突破",
  "url": "https://example.com/news/123",
  "summary": "AI领域取得重大突破...",
  "source": "科技日报",
  "publish_time": "2026-01-29",
  "keywords": '["AI", "技术"]',
  "image_urls": '["https://example.com/img1.jpg"]'
}
```

#### 搜索新闻

```python
# news_storage_search
{
  "search": "AI 技术",
  "event_name": "AI突破",
  "limit": 100
}
```

#### 下载图片

```python
# downloader_download_files
{
  "urls": '["https://example.com/img1.jpg", "https://example.com/img2.jpg"]',
  "save_path": "./output/report/images",
  "max_concurrent": 5
}
```

## 项目结构

```
OpencodeTest_1/
├── .opencode/              # Agent 配置文件
│   └── agents/            # 子 Agent 定义
├── mcp_server/            # MCP 服务器
│   ├── web_browser/       # 网页浏览服务器
│   ├── downloader/        # 下载服务器
│   └── news_storage/      # 新闻存储服务器
│       ├── core/          # 核心逻辑（数据库、模型）
│       └── tools/         # MCP 工具函数
├── prompts/               # Agent 提示词模板
├── templates/             # 报告模板
├── scripts/               # 测试和调试脚本
├── docs/                  # 文档
├── data/                  # 数据库文件
├── output/                # 生成的报告
└── opencode.json          # OpenCode 配置文件
```

## 数据库架构

### news 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| title | TEXT | 新闻标题 |
| url | TEXT | 新闻 URL（唯一） |
| summary | TEXT | 摘要 |
| source | TEXT | 来源 |
| publish_time | TEXT | 发布时间 |
| author | TEXT | 作者 |
| event_name | TEXT | 事件名称 |
| content | TEXT | 纯文本内容 |
| html_content | TEXT | HTML 内容 |
| keywords | TEXT | 关键词（JSON） |
| image_urls | TEXT | 图片 URL 列表（JSON） |
| local_image_paths | TEXT | 本地图片路径（JSON） |
| tags | TEXT | 标签（JSON） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 开发

### 运行测试

```bash
# 测试新闻存储
python scripts/test_news_storage_async.py

# 测试下载器
python scripts/test_async_downloader.py
```

### 添加新的 Agent

1. 在 `.opencode/agents/` 创建 Agent 配置文件
2. 在 `opencode.json` 中注册 Agent
3. 编写对应的提示词模板

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
