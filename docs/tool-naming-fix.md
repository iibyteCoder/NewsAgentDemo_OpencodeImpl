# 工具命名和分类配置修复

## ✅ 已完成的修复

### 1. 工具名称统一（添加前缀）

所有工具现在都使用 `news-storage_` 前缀，保持一致性。

**修复前**:
```
save_report_section
get_report_section
get_all_report_sections
get_report_sections_summary
mark_section_failed
```

**修复后**:
```
news-storage_save_report_section
news-storage_get_report_section
news-storage_get_all_report_sections
news-storage_get_report_sections_summary
news-storage_mark_section_failed
```

### 2. 工具分类配置

创建工具分组系统，支持按需启用工具组。

**文件**: [config.py](../mcp_server/news_storage/config.py)

**工具组**:

| 组名 | 工具数 | 说明 |
|------|--------|------|
| `basic` | 11 | 基础存储工具（保存、读取、搜索） |
| `navigation` | 4 | 分层导航工具（类别→事件→新闻） |
| `report_sections` | 5 | 报告部分工具（新版架构） |

**配置方式**:

通过环境变量 `NEWS_STORAGE_ENABLED_GROUPS` 控制启用的工具组：

```bash
# 启用所有工具（默认）
export NEWS_STORAGE_ENABLED_GROUPS=basic,navigation,report_sections

# 只启用基础和导航工具
export NEWS_STORAGE_ENABLED_GROUPS=basic,navigation

# 只启用报告部分工具
export NEWS_STORAGE_ENABLED_GROUPS=report_sections
```

### 3. 更新的文件

#### MCP 配置
- [mcp_server/news_storage/main.py](../mcp_server/news_storage/main.py) - 工具注册（添加前缀）
- [mcp_server/news_storage/config.py](../mcp_server/news_storage/config.py) - 工具分类配置

#### 智能体提示词（工具引用更新）
- [prompts/event-validator.md](../prompts/event-validator.md)
- [prompts/event-timeline.md](../prompts/event-timeline.md)
- [prompts/event-predictor.md](../prompts/event-predictor.md)
- [prompts/event-analyzer.md](../prompts/event-analyzer.md)
- [prompts/report-assembler.md](../prompts/report-assembler.md)

#### 文档
- [docs/mcp-tools-configuration.md](mcp-tools-configuration.md) - 配置说明文档

---

## 📋 完整的工具列表

### 基础存储工具（basic）

| 工具名称 | 说明 |
|---------|------|
| `news-storage_save` | 保存单条新闻 |
| `news-storage_save_batch` | 批量保存新闻 |
| `news-storage_get_by_url` | 根据URL获取新闻 |
| `news-storage_search` | 搜索新闻 |
| `news-storage_get_recent` | 获取最近新闻 |
| `news-storage_update_content` | 更新新闻内容 |
| `news-storage_delete` | 删除新闻 |
| `news-storage_stats` | 获取统计信息 |
| `news-storage_update_event_name` | 更新事件名称 |
| `news-storage_batch_update_event_name` | 批量更新事件名称 |

### 分层导航工具（navigation）

| 工具名称 | 说明 |
|---------|------|
| `news-storage_list_categories` | 列出所有类别 |
| `news-storage_list_events_by_category` | 列出类别下的事件 |
| `news-storage_list_news_by_event` | 列出事件下的新闻 |
| `news-storage_get_images_by_event` | 获取事件的图片 |

### 报告部分工具（report_sections）

| 工具名称 | 说明 |
|---------|------|
| `news-storage_save_report_section` | 保存报告部分 |
| `news-storage_get_report_section` | 获取单个报告部分 |
| `news-storage_get_all_report_sections` | 获取所有报告部分 |
| `news-storage_get_report_sections_summary` | 获取报告部分摘要 |
| `news-storage_mark_section_failed` | 标记部分失败 |

---

## 🔧 Claude Desktop 配置示例

### 配置文件位置
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

### 示例配置

#### 全部工具启用
```json
{
  "mcpServers": {
    "news_storage": {
      "command": "python",
      "args": ["-m", "mcp_server.news_storage"],
      "env": {
        "NEWS_STORAGE_ENABLED_GROUPS": "basic,navigation,report_sections"
      }
    }
  }
}
```

#### 分离为两个服务器（推荐）
```json
{
  "mcpServers": {
    "news_storage": {
      "command": "python",
      "args": ["-m", "mcp_server.news_storage"],
      "env": {
        "NEWS_STORAGE_ENABLED_GROUPS": "basic,navigation"
      }
    },
    "news-storage_reports": {
      "command": "python",
      "args": ["-m", "mcp_server.news_storage"],
      "env": {
        "NEWS_STORAGE_ENABLED_GROUPS": "report_sections"
      }
    }
  }
}
```

---

## ✨ 优势

1. **命名一致性**: 所有工具都有统一的前缀，易于识别
2. **按需加载**: 可以只启用需要的工具组，减少工具数量
3. **灵活配置**: 支持单实例或多实例部署
4. **易于维护**: 工具按功能分组，便于管理和扩展

---

## 🧪 测试配置

运行测试脚本查看当前配置：

```bash
python -m mcp_server.news_storage.config
```

输出示例：
```
============================================================
News Storage MCP Server 工具配置
============================================================
启用的工具组: basic, navigation, report_sections
启用的工具数量: 20

【基础存储工具】(basic)
  描述: 新闻的保存、读取、搜索等基础操作
  工具: 11 个
    - news-storage_batch_update_event_name
    - news-storage_delete
    - news-storage_get_by_url
    ...

============================================================
```
