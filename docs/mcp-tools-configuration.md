# News Storage MCP 工具分类配置

## 工具分组

### 1️⃣ 基础存储工具（basic）

**数量**: 11 个工具

**用途**: 新闻的保存、读取、搜索等基础操作

**工具列表**:
- `news-storage_save` - 保存单条新闻
- `news-storage_save_batch` - 批量保存新闻
- `news-storage_get_by_url` - 根据URL获取新闻
- `news-storage_search` - 搜索新闻（支持多词搜索）
- `news-storage_get_recent` - 获取最近添加的新闻
- `news-storage_update_content` - 更新新闻内容
- `news-storage_delete` - 删除新闻
- `news-storage_stats` - 获取统计信息
- `news-storage_update_event_name` - 更新事件名称
- `news-storage_batch_update_event_name` - 批量更新事件名称

---

### 2️⃣ 分层导航工具（navigation）

**数量**: 4 个工具

**用途**: 按类别→事件→新闻的层级浏览

**工具列表**:
- `news-storage_list_categories` - 列出所有类别
- `news-storage_list_events_by_category` - 列出类别下的事件
- `news-storage_list_news_by_event` - 列出事件下的新闻
- `news-storage_get_images_by_event` - 获取事件的图片

**使用流程**:
```
1. list_categories (查看有哪些类别)
   ↓
2. list_events_by_category (查看类别下的事件)
   ↓
3. list_news_by_event (查看事件下的新闻)
```

---

### 3️⃣ 报告部分工具（report_sections）

**数量**: 5 个工具

**用途**: 新版架构 - 保存和读取报告各部分数据

**工具列表**:
- `news-storage_save_report_section` - 保存报告部分到数据库
- `news-storage_get_report_section` - 获取单个报告部分
- `news-storage_get_all_report_sections` - 获取所有报告部分
- `news-storage_get_report_sections_summary` - 获取报告部分摘要（状态）
- `news-storage_mark_section_failed` - 标记部分失败

**使用场景**:
- **validator**: 完成验证后调用 `save_report_section`
- **timeline-builder**: 完成时间轴后调用 `save_report_section`
- **predictor**: 完成预测后调用 `save_report_section`
- **event-analyzer**: 使用 `get_report_sections_summary` 检查状态
- **report-assembler**: 使用 `get_report_section` 按需读取数据

---

## Claude Desktop 配置

### 方案1: 全部启用（默认）

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

### 方案2: 只启用基础和导航工具

如果你的工作流不需要报告生成功能：

```json
{
  "mcpServers": {
    "news_storage": {
      "command": "python",
      "args": ["-m", "mcp_server.news_storage"],
      "env": {
        "NEWS_STORAGE_ENABLED_GROUPS": "basic,navigation"
      }
    }
  }
}
```

### 方案3: 只启用报告部分工具（新版架构）

如果你只需要报告生成功能：

```json
{
  "mcpServers": {
    "news_storage": {
      "command": "python",
      "args": ["-m", "mcp_server.news_storage"],
      "env": {
        "NEWS_STORAGE_ENABLED_GROUPS": "report_sections"
      }
    }
  }
}
```

### 方案4: 分离为两个服务器实例

如果你希望完全分离基础功能和报告功能：

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

## 智能体提示词中的工具引用

### 基础存储工具

**适用于**: news-processor, category-handler 等需要操作数据库的智能体

```yaml
可用工具:
- news-storage_save - 保存新闻
- news-storage_search - 搜索新闻
- news-storage_get_recent - 获取最近新闻
```

### 导航工具

**适用于**: 需要浏览数据库结构的智能体

```yaml
可用工具:
- news-storage_list_categories - 列出类别
- news-storage_list_events_by_category - 列出事件
- news-storage_list_news_by_event - 列出新闻
```

### 报告部分工具

**适用于**: validator, timeline-builder, predictor, event-analyzer, report-assembler

```yaml
可用工具:
- news-storage_save_report_section - 保存分析结果
- news-storage_get_report_section - 读取分析结果
- news-storage_get_report_sections_summary - 检查状态
```

---

## 测试配置

运行测试脚本查看当前启用的工具：

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

【基础存储工具】
  描述: 新闻的保存、读取、搜索等基础操作
  工具: 11 个
    - news-storage_batch_update_event_name
    - news-storage_delete
    ...

【分层导航工具】
  描述: 按类别→事件→新闻的层级浏览
  工具: 4 个
    - news-storage_list_categories
    ...

【报告部分工具】
  描述: 新版架构：保存和读取报告各部分数据
  工具: 5 个
    - news-storage_save_report_section
    ...
============================================================
```
