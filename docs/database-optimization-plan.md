# 数据库系统优化方案

## 文档信息

- 创建时间：2026-01-30
- 状态：设计方案已确认，待实现
- 目标：改进新闻存储系统的会话隔离和查询体验

---

## 一、当前问题分析

### 1.1 会话隔离缺失

**问题**：数据库没有会话隔离机制

- 所有历史数据和新数据混在一起
- Agent 查询时会返回历史会话的数据
- 上下文被污染，导致 Agent 决策混乱

**影响**：

- 搜索结果包含无关的历史数据
- Agent 无法区分"本次会话"和"历史数据"
- Token 浪费在处理无关信息上

### 1.2 搜索盲目性

**问题**：搜索依赖字符串精确匹配

- Agent 不知道数据库里有什么
- 搜索词不对就返回空结果
- 无法进行探索式查询

**当前实现**：

```python
# database.py:227-310
# 简单的 LIKE 匹配
term_pattern = f"%{term}%"
# 在 title/summary/keywords/content 中搜索
```

**问题场景**：

- Agent 搜索"AI芯片"，但数据库里存的是"人工智能芯片"
- 搜索"欧冠"，但数据存的是"欧洲冠军联赛"
- Agent 无法知道有哪些可用的搜索词

### 1.3 缺少数据发现机制

**问题**：没有"浏览型"工具

- Agent 只能盲目搜索
- 无法了解数据范围（有哪些来源、事件、标签）
- 不能进行分层导航

### 1.4 工具描述不足

**问题**：MCP 工具描述不够清晰

- LLM 不知道何时调用哪个工具
- 缺少使用流程指导
- 参数说明不明确

---

## 二、优化方案设计

### 2.1 核心改进点

| 改进项 | 当前状态 | 优化后 | 价值 |
|--------|---------|--------|------|
| **会话隔离** | ❌ 无 | ✅ session_id 字段 | 避免历史数据污染 |
| **意图分类** | ❌ 无 | ✅ category 字段 | 支持用户意图分类 |
| **分层导航** | ❌ 无 | ✅ 4层 API | 渐进式数据探索 |
| **数据发现** | ❌ 盲目搜索 | ✅ 发现型工具 | Agent 了解数据范围 |
| **工具描述** | ⚠️ 基础 | ✅ 流程化指导 | 改善 LLM 调用准确率 |

---

### 2.2 数据库改动

#### 2.2.1 新增字段

```sql
-- 会话ID：隔离不同对话的数据
ALTER TABLE news ADD COLUMN session_id TEXT NOT NULL DEFAULT '';

-- 类别：用户意图分类（科技/体育/财经/...）
ALTER TABLE news ADD COLUMN category TEXT NOT NULL DEFAULT '';
```

#### 2.2.2 新增索引

```sql
-- 会话索引（高频查询）
CREATE INDEX idx_news_session ON news(session_id);

-- 类别索引（高频查询）
CREATE INDEX idx_news_category ON news(category);

-- 组合索引（支持按会话+类别筛选）
CREATE INDEX idx_news_session_category ON news(session_id, category);
```

#### 2.2.3 数据隔离逻辑

```python
# 同一条新闻，不同类别 = 不同记录
# 例如：关于"皇马"的新闻

记录1: {
    session_id: "20260130-abc123",
    category: "体育",
    event_name: "欧冠皇马",
    url: "https://example.com/news/1"
}

记录2: {
    session_id: "20260130-abc123",
    category: "财经",
    event_name: "皇马商业价值",
    url: "https://example.com/news/1"
}
```

**设计原则**：

- 同一 URL 可以存在于不同类别中
- 同一 `event_name` 在不同类别中视为不同事件
- `session_id` + `category` + `event_name` 共同确定数据范围

---

### 2.3 分层 API 设计

#### 层级结构

```
层级 1: 数据概览（类别维度）
   ↓
层级 2: 按类别浏览事件
   ↓
层级 3: 按事件查看新闻列表（轻量级）
   ↓
层级 4: 获取新闻完整内容
```

#### 层级 1: 列出所有类别

```python
@server.tool(name="news_storage_list_categories")
async def list_categories(session_id: str) -> str:
    """列出本次会话中的所有新闻类别

    返回类别列表及其统计信息，帮助 Agent 了解数据分布。

    Args:
        session_id: 会话ID（必须传入）

    Returns:
        {
            "success": true,
            "categories": [
                {
                    "name": "科技",
                    "count": 85,          # 该类别的新闻总数
                    "events": 12          # 该类别的事件数量
                },
                {
                    "name": "体育",
                    "count": 45,
                    "events": 8
                }
            ]
        }
    """
```

#### 层级 2: 列出类别下的事件

```python
@server.tool(name="news_storage_list_events_by_category")
async def list_events_by_category(
    session_id: str,
    category: str,
    limit: int = 20
) -> str:
    """列出某个类别下的所有事件

    Args:
        session_id: 会话ID（必须传入）
        category: 类别名称（从 list_categories 获取）
        limit: 最大返回数量

    Returns:
        {
            "success": true,
            "category": "科技",
            "events": [
                {
                    "event_name": "AI技术突破",
                    "news_count": 15,
                    "latest_time": "2026-01-30",
                    "sources": ["新华网", "科技日报"]
                },
                {
                    "event_name": "芯片战争",
                    "news_count": 22,
                    "latest_time": "2026-01-29",
                    "sources": ["人民网", "环球网"]
                }
            ]
        }
    """
```

#### 层级 3: 列出事件下的新闻（轻量级）

```python
@server.tool(name="news_storage_list_news_by_event")
async def list_news_by_event(
    session_id: str,
    event_name: str,
    limit: int = 50
) -> str:
    """列出某个事件下的新闻（轻量级：只返回 title/url/summary）

    不包含完整内容，用于快速浏览。

    Args:
        session_id: 会话ID（必须传入）
        event_name: 事件名称（从 list_events_by_category 获取）
        limit: 最大返回数量

    Returns:
        {
            "success": true,
            "event_name": "AI技术突破",
            "count": 15,
            "news": [
                {
                    "title": "AI芯片技术重大突破",
                    "url": "https://example.com/news/1",
                    "summary": "简短摘要",
                    "source": "新华网",
                    "publish_time": "2026-01-30"
                },
                ...
            ]
        }
    """
```

#### 层级 4: 获取完整内容

```python
@server.tool(name="news_storage_get_detail")
async def get_news_detail(
    session_id: str,
    url: str
) -> str:
    """获取新闻完整内容

    返回包括正文、图片等所有信息。

    Args:
        session_id: 会话ID（必须传入）
        url: 新闻URL（从 list_news_by_event 获取）

    Returns:
        {
            "success": true,
            "data": {
                "title": "...",
                "url": "...",
                "summary": "...",
                "content": "完整正文内容",
                "html_content": "HTML原文",
                "keywords": ["AI", "芯片"],
                "image_urls": [...],
                "local_image_paths": [...],
                ...
            }
        }
    """
```

---

### 2.4 Agent 使用流程

#### 探索模式（不知道要查什么）

```
1. Agent 获取 session_id（从系统配置）
   ↓
2. list_categories(session_id)
   → 返回: ["科技", "体育", "财经"]
   ↓
3. Agent 选择感兴趣的类别，如"科技"
   ↓
4. list_events_by_category(session_id, category="科技")
   → 返回: ["AI技术突破", "芯片战争", ...]
   ↓
5. Agent 选择事件，如"AI技术突破"
   ↓
6. list_news_by_event(session_id, event_name="AI技术突破")
   → 返回: [news1, news2, ...]
   ↓
7. Agent 选择感兴趣的新闻
   ↓
8. get_news_detail(session_id, url="xxx")
   → 返回完整内容
```

#### 精确模式（知道要查什么）

```
1. list_events_by_category(session_id, category="科技")
   → 直接获取科技类事件
   ↓
2. list_news_by_event(session_id, event_name="AI技术突破")
   → 直接查看新闻
```

#### 保存数据流程

```
save_news(
    session_id="xxx",      # Agent 记住的会话ID
    category="科技",        # Agent 分析出的类别
    event_name="AI技术突破",
    title="...",
    url="...",
    ...
)
```

---

## 三、数据模型更新

### 3.1 NewsItem 模型

```python
@dataclass
class NewsItem:
    """新闻数据模型"""

    # 基本信息
    title: str
    url: str
    summary: str = ""
    source: str = ""
    publish_time: str = ""
    author: str = ""
    event_name: str = ""

    # 新增字段
    session_id: str = ""      # 会话ID
    category: str = ""        # 类别（科技/体育/财经/...）

    # 内容
    content: str = ""
    html_content: str = ""

    # 扩展信息
    keywords: List[str] = field(default_factory=list)
    image_urls: List[str] = field(default_factory=list)
    local_image_paths: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
```

### 3.2 SearchFilter 模型

```python
@dataclass
class SearchFilter:
    """搜索过滤器"""

    # 新增字段
    session_id: str          # 会话ID（必填）
    category: str = ""       # 类别筛选

    # 原有字段
    search_terms: Optional[List[str]] = None
    source: Optional[str] = None
    event_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 100
    offset: int = 0
```

---

## 四、数据库方法更新

### 4.1 save_news

```python
async def save_news(
    self,
    news: NewsItem,
    session_id: str,
    category: str
) -> bool:
    """保存单条新闻（自动关联会话和类别）"""
    news_dict = news.to_dict()
    news_dict["session_id"] = session_id
    news_dict["category"] = category

    # 插入时包含新字段
    await cursor.execute(
        """
        INSERT INTO news (
            title, url, summary, source, publish_time, author, event_name,
            content, html_content, keywords, image_urls, local_image_paths, tags,
            session_id, category,  -- 新增
            created_at, updated_at
        ) VALUES (?, ?, ?, ...)
        """,
        (...)
    )
```

### 4.2 search_news

```python
async def search_news(
    self,
    filter: SearchFilter,
    session_id: str,
    category: str = ""
) -> List[NewsItem]:
    """搜索新闻（自动过滤会话和类别）"""
    conditions = []
    params = []

    # 强制添加会话和类别过滤
    conditions.append("session_id = ?")
    params.append(session_id)

    if category:
        conditions.append("category = ?")
        params.append(category)

    # ... 其他条件

    # 执行查询
    query = f"""
        SELECT ... FROM news
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
```

### 4.3 新增方法

```python
async def get_categories(
    self,
    session_id: str
) -> List[dict]:
    """获取会话中的所有类别及统计"""
    await cursor.execute("""
        SELECT
            category,
            COUNT(*) as count,
            COUNT(DISTINCT event_name) as events
        FROM news
        WHERE session_id = ?
        GROUP BY category
        ORDER BY count DESC
    """, (session_id,))
    return ...

async def get_events_by_category(
    self,
    session_id: str,
    category: str,
    limit: int = 20
) -> List[dict]:
    """获取类别下的事件列表"""
    await cursor.execute("""
        SELECT
            event_name,
            COUNT(*) as news_count,
            MAX(publish_time) as latest_time,
            GROUP_CONCAT(DISTINCT source) as sources
        FROM news
        WHERE session_id = ? AND category = ?
        GROUP BY event_name
        ORDER BY latest_time DESC
        LIMIT ?
    """, (session_id, category, limit))
    return ...

async def get_news_titles_by_event(
    self,
    session_id: str,
    event_name: str,
    limit: int = 50
) -> List[dict]:
    """获取事件下的新闻标题列表（轻量级）"""
    await cursor.execute("""
        SELECT
            title, url, summary, source, publish_time
        FROM news
        WHERE session_id = ? AND event_name = ?
        ORDER BY publish_time DESC
        LIMIT ?
    """, (session_id, event_name, limit))
    return ...
```

---

## 五、会话管理

### 5.1 session_id 生成规则

```python
# 在 opencode.json 或启动脚本中配置
import uuid
from datetime import datetime

session_id = f"{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

# 示例输出：20260130-a3f7b2c1
```

### 5.2 Agent 提示词配置

```markdown
# 数据库操作指南

## 会话ID
你有一个固定的 session_id，整个对话过程中保持不变：
- session_id: 20260130-{random}

## 标准流程

### 探索数据（不知道要查什么）
1. 调用 `news_storage_list_categories(session_id)` 了解有哪些类别
2. 调用 `news_storage_list_events_by_category(session_id, category)` 查看事件
3. 调用 `news_storage_list_news_by_event(session_id, event_name)` 查看新闻列表
4. 调用 `news_storage_get_detail(session_id, url)` 获取完整内容

### 保存数据
- 调用 `news_storage_save()` 时必须传入 session_id 和 category
- category 由你根据用户意图分析得出（科技/体育/财经/...）

### 搜索数据
- 可以使用 `news_storage_search()` 进行灵活搜索
- 所有查询都会自动过滤 session_id，不会返回历史数据
```

---

## 六、实现清单

### 6.1 数据库层

- [ ] 添加 `session_id` 和 `category` 字段
- [ ] 创建相关索引
- [ ] 更新 `NewsItem` 模型
- [ ] 更新 `SearchFilter` 模型
- [ ] 更新 `save_news()` 方法
- [ ] 更新 `search_news()` 方法（添加过滤）
- [ ] 新增 `get_categories()` 方法
- [ ] 新增 `get_events_by_category()` 方法
- [ ] 新增 `get_news_titles_by_event()` 方法

### 6.2 工具层（MCP）

- [ ] 实现 `news_storage_list_categories` 工具
- [ ] 实现 `news_storage_list_events_by_category` 工具
- [ ] 实现 `news_storage_list_news_by_event` 工具
- [ ] 实现 `news_storage_get_detail` 工具
- [ ] 更新 `news_storage_save` 工具（添加 session_id/category 参数）
- [ ] 更新 `news_storage_search` 工具（添加 session_id/category 参数）
- [ ] 更新其他工具的参数

### 6.3 配置层

- [ ] 在 opencode.json 中配置 session_id 生成规则
- [ ] 更新 Agent 提示词，添加使用流程说明

---

## 七、预期效果

### 7.1 性能改进

- ✅ 查询只返回当前会话数据，减少无关结果
- ✅ 分层导航避免一次性加载大量数据
- ✅ 索引优化提升查询速度

### 7.2 Agent 体验改进

- ✅ 可以渐进式探索数据，不需要猜测
- ✅ 明确的调用流程，减少工具调用错误
- ✅ Token 使用更高效（按需获取数据）

### 7.3 可维护性

- ✅ 会话隔离便于数据管理和清理
- ✅ 类别字段支持更灵活的业务逻辑
- ✅ 分层 API 易于扩展

---

## 八、后续优化方向

### 8.1 短期（本次实现）

- 实现基础的会话隔离和分层导航
- 更新所有相关工具

### 8.2 中期

- 添加数据归档功能（自动清理旧会话）
- 添加会话统计工具
- 优化搜索算法（支持模糊匹配、同义词）

### 8.3 长期

- 引入向量搜索（语义检索）
- 添加自动分类功能（基于内容分析）
- 支持跨会话查询（可选）

---

## 九、风险评估

### 9.1 数据迁移

- **风险**：现有数据没有 session_id 和 category
- **应对**：
  - 旧数据 session_id 设为 "legacy"
  - 或者提供数据迁移脚本

### 9.2 Agent 适配

- **风险**：Agent 可能忘记传 session_id
- **应对**：
  - 在工具描述中强调
  - 在提示词中明确说明
  - 返回友好的错误提示

### 9.3 性能影响

- **风险**：添加过滤条件可能变慢
- **应对**：
  - 已添加索引
  - 组合索引优化常用查询

---

## 十、总结

本次优化解决的核心问题：

1. **会话隔离** - 避免历史数据污染
2. **数据发现** - 支持分层导航
3. **意图分类** - 支持 category 字段
4. **工具可用性** - 改进 LLM 调用体验

设计原则：

- Agent 自管理 session_id（在对话中记住）
- 渐进式数据探索（层级导航）
- 保持向后兼容（旧数据仍可访问）
- 性能优先（添加索引）
