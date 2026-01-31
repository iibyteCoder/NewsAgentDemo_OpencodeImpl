# NewsAgent 业务流程文档

## 概述

本文档详细描述 NewsAgent 智能新闻聚合系统的完整业务流程，包括系统架构、各层级的并行处理策略、数据流转过程以及关键优化点。

---

## 目录

1. [系统架构](#系统架构)
2. [并行处理层级](#并行处理层级)
3. [完整业务流程](#完整业务流程)
4. [数据流转](#数据流转)
5. [关键优化策略](#关键优化策略)
6. [错误处理机制](#错误处理机制)

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户请求                                │
│         "收集今日体育、政治、科技新闻"                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Coordinator (主协调器)                          │
│  • 生成全局参数 (session_id, report_timestamp)              │
│  • 识别查询模式 (广泛/精确)                                   │
│  • 并行启动所有类别任务                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │ 体育   │  │ 政治   │  │ 科技   │  ← Category-Handler
    └───┬────┘  └───┬────┘  └───┬────┘
        │           │           │
        ▼           ▼           ▼
    并行处理   并行处理   并行处理
    新闻链接   新闻链接   新闻链接
        │           │           │
        ▼           ▼           ▼
    聚合为事件 → 聚合为事件 → 聚合为事件
        │           │           │
        ▼           ▼           ▼
    并行处理   并行处理   并行处理
    所有事件   所有事件   所有事件
        │           │           │
        ▼           ▼           ▼
    ┌─────────────────────────────────────┐
    │      Event-Analyzer (事件分析器)     │
    │  • 并发启动三个分析任务               │
    │  • 检查完成状态                      │
    │  • 生成事件报告                      │
    └───┬───────────┬──────────┬──────────┘
        │           │          │
        ▼           ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │Validator││Timeline ││Predictor│
   │ 验证器  ││ 构建器  ││ 预测器  │
   └────────┘ └────────┘ └────────┘
        │           │          │
        ▼           ▼          ▼
   保存到数据库 (report_sections 表)
        │           │          │
        └───────────┼──────────┘
                    ▼
         ┌──────────────────┐
         │ Report-Assembler │
         │  • 按需读取数据   │
         │  • 并行生成各部分 │
         │  • 文件合并报告   │
         └─────────┬────────┘
                   │
                   ▼
         ┌──────────────────┐
         │ Category-Indexer │
         │  生成类别索引文件 │
         └─────────┬────────┘
                   │
                   ▼
         ┌──────────────────┐
         │   总索引文件     │
         │  (coordinator)   │
         └──────────────────┘
```

---

## 并行处理层级

系统采用**四层并行架构**，最大化处理效率：

### 第一层：类别级并行 (Coordinator)

**位置**: `coordinator.md:105-111`

**职责**: 同时启动多个类别的收集任务

**示例**:
```text
输入: "收集今日体育、政治、科技新闻"

并行启动:
├── Category-Handler (体育)
├── Category-Handler (政治)
└── Category-Handler (科技)

所有任务同时执行，而非串行
```

**关键代码**:
- ✅ 所有类别任务同时启动（并行执行）
- ✅ 每个类别使用相同的 `report_timestamp`
- ✅ 传递 `session_id` 和 `report_timestamp`

---

### 第二层：新闻级并行 (Category-Handler)

**位置**: `category-handler.md:105-120`

**职责**: 并行处理单个类别内的所有新闻链接

**示例**:
```text
搜索到 30 个新闻链接

并行调用 @news-processor:
├── @news-processor url1
├── @news-processor url2
├── @news-processor url3
├── ... (共30个)
└── @news-processor url30

❌ 错误: 处理 url1 → 等待 → 处理 url2 → 等待 → ...
✅ 正确: 同时启动 30 个 @news-processor 实例
```

**关键代码**:
- ✅ 一次性并行调用所有链接
- ❌ 不要串行逐个处理链接
- ❌ 不要批量处理多个链接

**性能提升**: 假设每个链接处理耗时 10 秒
- 串行: 30 × 10 = 300 秒
- 并行: ~10-15 秒

---

### 第三层：事件级并行 (Category-Handler)

**位置**: `category-handler.md:130-132`

**职责**: 并行处理单个类别内的所有事件

**示例**:
```text
聚合后得到 10 个事件

并行启动 @event-processor:
├── @event-processor 事件1
├── @event-processor 事件2
├── @event-processor 事件3
├── ... (共10个)
└── @event-processor 事件10

所有事件同时进行分析
```

---

### 第四层：分析级并行 (Event-Analyzer)

**位置**: `event-analyzer.md:72-83`

**职责**: 并发执行单个事件的三个分析任务

**示例**:
```text
单个事件: "美国大选"

并行启动:
├── @validator - 验证事件真实性
├── @timeline-builder - 构建事件时间轴
└── @predictor - 预测事件发展趋势

三个任务同时执行，全部完成后进入下一步
```

**关键代码**:
- ✅ 三个任务必须同时启动（并行执行）
- ❌ 不要等待一个任务完成后再启动下一个

---

### 第五层：搜索结果并行 (Validator/Timeline/Predictor)

**位置**:
- `event-validator.md:76,98-103`
- `event-timeline.md:80,104-109`
- `event-predictor.md:80,102-107`

**职责**: 并行处理搜索到的所有链接

**示例**:
```text
@validator 搜索到 10 个验证来源

并行调用 @news-processor:
├── @news-processor url1
├── @news-processor url2
├── ... (共10个)
└── @news-processor url10

所有结果同时获取和处理
```

---

### 第六层：报告部分并行 (Report-Assembler)

**位置**: `report-assembler.md:103-117`

**职责**: 并行生成报告的各个部分

**示例**:
```text
事件报告包含 6 个部分

并行生成:
├── 01-summary.md (事件摘要)
├── 02-news.md (新闻来源)
├── 03-validation.md (真实性验证)
├── 04-timeline.md (事件时间轴)
├── 05-prediction.md (趋势预测)
└── 06-images.md (相关图片)

所有部分同时生成，最后通过文件合并组装
```

**关键代码**:
- ✅ 所有部分生成任务同时启动（并行执行）
- ✅ 每个部分直接写入文件，不返回内容到上下文

---

## 完整业务流程

### 阶段 0: 初始化 (Coordinator)

**文件**: `coordinator.md`

**步骤**:

1. **生成全局参数** (只生成一次)
   ```python
   session_id = "20260130-a3b4c6d9"
   report_timestamp = "report_20260130_153000"
   ```

2. **识别查询模式**
   - 纯类别查询: "体育新闻"
   - 类别+事件查询: "体育新闻中的NBA"
   - 纯事件查询: "NBA" (推断类别)

3. **并行启动类别任务**
   ```text
   为每个类别启动 @category-processor
   ├── 传递 session_id
   ├── 传递 report_timestamp
   └── 传递 category, specific_events
   ```

---

### 阶段 1: 新闻收集 (Category-Handler)

**文件**: `category-handler.md`

#### 步骤 1.1: 搜索新闻

```text
根据模式搜索:
- 广泛模式: 搜索类别名称
- 精确模式: 搜索 "类别 + 事件名称"

一次搜索获取 30-50 条新闻
```

#### 步骤 1.2: 并行处理所有新闻链接

**关键步骤**: 并行调用 `@news-processor`

```text
✅ 正确做法:
@news-processor 处理 url1 session_id=xxx category=体育
@news-processor 处理 url2 session_id=xxx category=体育
@news-processor 处理 url3 session_id=xxx category=体育
... (所有链接同时调用)

❌ 错误做法:
处理 url1 → 等待完成 → 处理 url2 → 等待完成 → ...
```

**@news-processor 的职责**:
1. 获取文章内容 (使用 `fetch_article_content`)
2. 格式化时间 (转换为 `YYYY-MM-DD HH:MM:SS`)
3. 清洗各字段
4. 保存到数据库
5. 返回处理结果

**优化点**:
- ❌ **不再检查重复性** (移除 `news-storage_get_by_url`)
- 直接并行处理所有链接

---

#### 步骤 1.3: 聚合为事件

**文件**: `news-aggregator.md`

```text
调用 @event-aggregator:
1. 读取最近新闻
2. 按标题相似度聚类
3. 聚合为事件 (多个媒体报道同一件事 → 一个事件)
4. 批量更新数据库

示例:
- 新浪体育-NBA总决赛 → 事件: "NBA总决赛"
- 腾讯体育-NBA总决赛 → 事件: "NBA总决赛"
- 搜狐体育-NBA总决赛 → 事件: "NBA总决赛"

结果: 1 个事件，3 条新闻
```

---

#### 步骤 1.4: 事件过滤 (仅精确模式)

```text
如果是精确模式:
- 只保留与 specific_events 匹配的事件
- 过滤掉无关事件

示例:
- 搜索: 体育新闻中的 NBA
- 聚合结果: 10 个事件
- 过滤后: 只保留 2 个 NBA 相关事件
```

---

#### 步骤 1.5: 并行处理所有事件

**关键步骤**: 并行启动 `@event-processor`

```text
假设有 10 个事件

并行启动:
├── @event-processor 事件1
├── @event-processor 事件2
├── ... (共10个)
└── @event-processor 事件10

所有事件同时进入分析阶段
```

---

### 阶段 2: 事件分析 (Event-Analyzer)

**文件**: `event-analyzer.md`

#### 步骤 2.1: 读取事件新闻

```text
使用 news-storage_search 读取该事件的所有新闻
验证数据完整性
```

---

#### 步骤 2.2: 并发启动三个分析任务

**关键步骤**: 必须并行调用三个子任务

```text
✅ 正确做法:
@validator 验证事件真实性
@timeline-builder 构建事件时间轴
@predictor 预测事件发展趋势

三个任务同时启动，不要等待

❌ 错误做法:
启动 validator → 等待完成 → 启动 timeline-builder → ...
```

---

#### 步骤 2.3: 等待任务完成

```text
使用 news-storage_get_report_sections_summary 检查状态

{
  "summary": {
    "validation": {"status": "completed"},
    "timeline": {"status": "completed"},
    "prediction": {"status": "failed"}
  },
  "completed": 2,
  "failed": 1
}
```

---

#### 步骤 2.4: 生成事件报告

```text
调用 @report-generator 生成报告
- 只传递基本参数
- @report-generator 会从数据库按需读取数据
```

---

### 阶段 3: 事件子任务分析

#### 3.1 验证事件真实性 (Validator)

**文件**: `event-validator.md`

**流程**:

1. 读取已有信息
2. 分析验证点
3. 针对性搜索 (2-3轮)
4. **并行保存搜索结果** ← 关键优化
5. 综合判断
6. 保存到数据库

**并行示例**:
```text
搜索到 10 个验证来源

并行调用 @news-processor:
├── @news-processor url1
├── @news-processor url2
├── ... (共10个)
└── @news-processor url10

所有结果同时保存到数据库
```

**输出**:
```json
{
  "credibility_score": 85,
  "confidence_level": "高",
  "evidence_chain": [...],
  "analysis": "...",
  "sources": [...]
}
```

---

#### 3.2 构建事件时间轴 (Timeline-Builder)

**文件**: `event-timeline.md`

**流程**:

1. 读取已有信息
2. 按时间排序
3. 识别时间缺口
4. 针对性搜索 (2-3轮)
5. **并行处理并保存搜索结果** ← 关键优化
6. 重新读取数据库
7. 构建时间轴
8. 保存到数据库

**并行示例**:
```text
每轮搜索后立即并行调用 @news-processor 处理所有结果
```

**输出**:
```json
{
  "milestones": [
    {
      "date": "2026-01-15",
      "event": "NBA常规赛开赛",
      "importance": "高",
      "source_url": "..."
    }
  ],
  "development_path": "...",
  "causal_relationships": [...]
}
```

---

#### 3.3 预测事件发展趋势 (Predictor)

**文件**: `event-predictor.md`

**流程**:

1. 读取已有信息
2. 识别预测需求
3. 针对性搜索 (1-2轮)
4. **并行保存搜索结果** ← 关键优化
5. 构建多情景预测
6. 保存到数据库

**并行示例**:
```text
搜索到 8 个专家观点来源

并行调用 @news-processor 处理所有结果
```

**输出**:
```json
{
  "scenarios": [
    {
      "scenario": "乐观情景",
      "probability": 0.3,
      "evidence": [...],
      "timeframe": "3个月内"
    }
  ],
  "key_factors": [...],
  "conclusion": "..."
}
```

---

### 阶段 4: 报告生成 (Report-Assembler)

**文件**: `report-assembler.md`

#### 步骤 4.1: 检查数据状态

```text
使用 news-storage_get_report_sections_summary
确定哪些部分已完成、哪些缺失
```

---

#### 步骤 4.2: 按需读取数据

```text
只读取需要的数据:
- news-storage_search 读取事件新闻
- news-storage_get_report_section 读取 validation
- news-storage_get_report_section 读取 timeline
- news-storage_get_report_section 读取 prediction

每个部分生成器只接收自己需要的数据
```

---

#### 步骤 4.3: 并行生成各部分文件

**关键步骤**: 并行调用所有部分生成器

```text
✅ 正确做法:
@report-section-generator summary
@report-section-generator news
@report-section-generator validation
@report-section-generator timeline
@report-section-generator prediction

所有部分同时生成，直接写入文件

❌ 错误做法:
生成 summary → 等待 → 生成 news → 等待 → ...
```

---

#### 步骤 4.4: 下载图片

```text
1. 从新闻数据中收集所有图片URL
2. 创建图片文件夹
3. 批量下载图片
4. 生成 06-images.md 部分
```

---

#### 步骤 4.5: 纯文件操作组装报告

**关键优化**: 使用文件合并，不读取到上下文

```text
推荐: Python 脚本合并
┌────────────────────────┐
│  合并脚本 (merge.py)    │
│  1. 读取 01-summary.md  │
│  2. 读取 02-news.md     │
│  3. 读取 03-validation.md│
│  4. ...                 │
│  5. 写入最终报告        │
└────────────────────────┘

优势:
- 不占用上下文
- 支持大文件
- 跨平台兼容
```

---

### 阶段 5: 生成索引

#### 5.1 类别索引 (Category-Indexer)

**文件**: `category-indexer.md`

```text
1. 扫描已生成的事件报告文件
2. 生成类别索引文件

输出: index.md
- 事件列表
- 新闻数量
- 相对路径链接
```

---

#### 5.2 总索引 (Coordinator)

```text
1. 读取总索引模板
2. 准备数据（分类索引内容、统计信息）
3. 格式化模板并写入总索引文件

输出: output/report_xxx/index.md
```

---

## 数据流转

### 数据库表结构

#### news 表

```sql
CREATE TABLE news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    summary TEXT,
    content TEXT,
    source TEXT,
    author TEXT,
    publish_time TEXT,
    keywords TEXT,
    tags TEXT,
    images TEXT,
    category TEXT,
    event_name TEXT,
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### report_sections 表

```sql
CREATE TABLE report_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id TEXT UNIQUE NOT NULL,
    session_id TEXT,
    event_name TEXT,
    section_type TEXT,
    status TEXT,
    content TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

### 数据流转图

```
用户请求
    │
    ├─> Coordinator (生成 session_id, report_timestamp)
    │       │
    │       └─> Category-Handler (接收参数)
    │               │
    │               ├─> 搜索新闻 (30-50条)
    │               │
    │               ├─> 并行调用 @news-processor (30-50个实例)
    │               │       │
    │               │       └─> 保存到 news 表 (30-50条记录)
    │               │
    │               ├─> 聚合为事件
    │               │       │
    │               │       └─> 更新 news 表 (event_name 字段)
    │               │
    │               └─> 并行调用 @event-processor (10个事件)
    │                       │
    │                       └─> Event-Analyzer
    │                               │
    │                               ├─> 并行启动三个任务
    │                               │       │
    │                               ├─> Validator
    │                               │       ├─> 搜索验证
    │                               │       ├─> 并行处理结果
    │                               │       └─> 保存到 report_sections (type=validation)
    │                               │
    │                               ├─> Timeline-Builder
    │                               │       ├─> 搜索历史
    │                               │       ├─> 并行处理结果
    │                               │       └─> 保存到 report_sections (type=timeline)
    │                               │
    │                               └─> Predictor
    │                                       ├─> 搜索预测
    │                                       ├─> 并行处理结果
    │                                       └─> 保存到 report_sections (type=prediction)
    │
    └─> Report-Assembler
            │
            ├─> 按需读取 news 表
            ├─> 按需读取 report_sections 表
            │
            ├─> 并行生成各部分文件
            │       ├─> 01-summary.md
            │       ├─> 02-news.md
            │       ├─> 03-validation.md
            │       ├─> 04-timeline.md
            │       ├─> 05-prediction.md
            │       └─> 06-images.md
            │
            └─> 文件合并 → 最终报告 (事件名称.md)
```

---

## 关键优化策略

### 1. 移除重复性检查

**位置**: `news-processor.md`

**变更**:
```diff
- 工作流程:
-   1. 接收新闻链接
-   2. 检查是否已存在 (news-storage_get_by_url)
-   3. 获取文章内容
-   ...

+ 工作流程:
+   1. 接收新闻链接
+   2. 获取文章内容
+   3. 格式化时间
+   ...
```

**原因**:
- 重复性检查会阻塞并行处理
- 数据库唯一索引会自动处理重复
- 即使重复保存也不会影响结果

---

### 2. 六层并行架构

**性能提升计算**:

假设处理 3 个类别，每个类别 30 条新闻，聚合为 10 个事件

```
串行执行时间:
= 3类别 × (30新闻 × 10秒 + 10事件 × 60秒)
= 3 × (300秒 + 600秒)
= 2700秒 (45分钟)

并行执行时间:
= max(30新闻 × 10秒, 10事件 × 60秒)
= max(300秒, 600秒)
= 600秒 (10分钟)

性能提升: 4.5倍
```

---

### 3. 数据库存储架构

**旧版问题**:
```
所有数据通过上下文传递 → 上下文过长 → 信息丢失
```

**新版方案**:
```
分析结果保存到数据库 → 按需读取 → 完整保留
```

**优势**:
- 避免上下文累积
- 各部分独立上下文
- 支持并行处理
- 错误隔离

---

### 4. 分步报告生成

**旧版**:
```
一次性生成报告 → 上下文过长 → 信息丢失 ❌
```

**新版**:
```
数据 → 各部分独立生成 → 文件合并 → 完整报告 ✓
       (避免上下文累积)    (纯文件操作)
```

**优势**:
- 每个部分独立生成
- 使用文件合并，不占用上下文
- 支持并行生成
- 错误隔离

---

## 错误处理机制

### 1. 任务级容错

**示例**: Event-Analyzer

```text
如果某个任务失败:
- validation: failed
- timeline: completed
- prediction: completed

操作:
1. 使用默认值继续
2. 标记报告为"部分完成"
3. 生成报告时标注缺失部分
```

---

### 2. 部分隔离

**示例**: Report-Assembler

```text
如果某个部分生成失败:
- 03-validation.md 生成失败

操作:
1. 跳过该部分
2. 继续生成其他部分
3. 最终报告标注"验证部分缺失"
```

---

### 3. 降级策略

**示例**: Category-Handler

```text
步骤接近上限时的降级:
- 无法完成所有事件分析 → 只完成核心事件
- 无法生成完整报告 → 生成基础报告
- 无法下载图片 → 跳过图片部分
```

---

## 性能指标

### 典型场景: 3个类别，每个类别30条新闻

| 阶段 | 串行时间 | 并行时间 | 提升 |
|------|----------|----------|------|
| 类别处理 | 1350秒 | 450秒 | 3x |
| 新闻处理 | 300秒 | 10-15秒 | 20-30x |
| 事件分析 | 600秒 | 200秒 | 3x |
| 报告生成 | 60秒 | 15秒 | 4x |
| **总计** | **2310秒** | **680秒** | **3.4x** |

---

## 总结

NewsAgent 采用**六层并行架构**，实现了高效的新闻处理流程：

1. **类别级并行**: 同时处理多个类别
2. **新闻级并行**: 同时处理所有新闻链接
3. **事件级并行**: 同时分析所有事件
4. **分析级并行**: 同时执行验证、时间轴、预测
5. **搜索结果并行**: 同时处理所有搜索结果
6. **报告部分并行**: 同时生成报告的各个部分

配合**数据库存储架构**和**分步报告生成**，系统在保证信息完整性的同时，实现了**3-4倍的性能提升**。

---

*文档版本: v1.0*
*最后更新: 2026-01-30*
