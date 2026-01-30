# 目录结构设计文档

## 文档信息

- **创建日期**: 2026-01-30
- **版本**: 1.0
- **状态**: 设计阶段

---

## 1. 目标目录结构

### 1.1 整体结构

```
output/
└── report_{timestamp}/          ← 统一时间戳，一次query的所有内容都在这里
    ├── index.md                 ← 总索引（所有类别）
    ├── 体育新闻/
    │   └── 2026-01-30/
    │       └── 资讯汇总与摘要/
    │           ├── index.md     ← 类别索引
    │           ├── 事件1.md     ← 事件报告
    │           ├── 事件1/       ← 事件图片文件夹（与md文件同名）
    │           │   ├── 图片1.png
    │           │   └── 图片2.png
    │           └── 事件2.md
    ├── 科技新闻/
    │   └── 2026-01-30/
    │       └── 资讯汇总与摘要/
    │           ├── index.md
    │           └── ...
    └── 政治新闻/
        └── 2026-01-30/
            └── 资讯汇总与摘要/
                └── ...
```

### 1.2 设计原则

1. **时间戳统一性**：一次 query（总流程执行）生成的所有内容都在同一个 `report_{timestamp}/` 目录下
2. **避免覆盖**：时间戳格式为 `report_YYYYMMDD_HHMMSS`，避免多次独立用户 query 之间的文件覆盖
3. **层级清晰**：分类 → 日期 → 资讯汇总与摘要 → 事件
4. **图片组织**：每个事件的图片放在与 md 文件同名的文件夹下
5. **索引完整**：总索引 + 类别索引，确保可导航性

---

## 2. 问题诊断

### 2.1 当前生成的目录结构（错误）

```
output/
├── 20260130_1530/                    ❌ 缺少 "report_" 前缀
├── 20260130_153000/                  ❌ 缺少 "report_" 前缀
├── 20260130_160000/                  ❌ 缺少 "report_" 前缀
├── report_20260130_120000/           ✅ 有前缀
├── report_2026-01-30/                ❌ 日期格式不一致
└── report_2026-01-30_03-08-35/       ❌ 时间格式不一致
```

### 2.2 根本原因分析

#### 问题1：时间戳未统一传递 ⭐⭐⭐（核心问题）

**现状**：
- `news-coordinator` 生成 `session_id`，但**没有生成统一的 `report_timestamp`**
- 各个智能体（`event-report-generator`）独立生成自己的时间戳
- 导致生成多个不同时间戳的目录，无法集中到同一个 `report_{timestamp}/` 下

**证据**：
```bash
# output 目录下有多个不同时间戳的目录
20260130_1530/          # 没有report_前缀
20260130_153000/        # 没有report_前缀
report_20260130_120000/ # 有前缀，但与其他不统一
```

#### 问题2：图片引用路径错误 ⭐⭐⭐

**当前生成的引用**（错误）：
```markdown
![极氪9X交付周期](../../../../../20260130_1530/汽车/2026-01-29/资讯汇总与摘要/极氪9X产能提升与等车补贴政策/img_pic_1769655355.jpg)
```

**正确的引用应该是**（根据目标结构）：
```markdown
# 如果 md 文件和图片文件夹 同级
![极氪9X交付周期](./事件1/图片1.png)
```

**原因**：
- `event-report-generator.txt` 没有明确定义正确的相对路径生成规则
- 图片下载后，数据库没有正确更新本地路径信息

#### 问题3：index.md 文件缺失 ⭐⭐

**现状**：
- 没有生成日期级索引 `资讯汇总与摘要/index.md`
- 没有生成总索引 `report_{timestamp}/index.md`

**原因**：
- `category-processor` 的工作流程中没有明确调用 `synthesizer` 生成索引
- `synthesizer` 的职责定位不清楚

#### 问题4：智能体职责划分不清晰 ⭐⭐

**职责重叠**：
- `category-processor` 应该调用 `synthesizer` 生成报告
- `event-processor` 调用 `event-report-generator` 生成报告
- 两者都在"生成报告"，边界不清晰

**正确划分**：
- `event-processor` + `event-report-generator`：生成单个事件的 md 文件
- `synthesizer`：生成类别级的 index.md
- `news-coordinator`：生成总 index.md

#### 问题5：参数传递不完整 ⭐

**发现的问题**：
1. `event-report-generator` 需要知道：`report_timestamp`, `category`, `date`, `event_name`
2. 但从 `event-processor` 的调用来看，只传递了基本信息
3. 导致 `event-report-generator` 需要自己生成时间戳，但缺少统一的规则

---

## 3. 修复方案

### 3.1 核心设计

**统一时间戳生成和传递**：
- `news-coordinator` 在启动时生成 `report_timestamp = "report_YYYYMMDD_HHMMSS"`
- 所有子智能体使用这个统一的时间戳，不再自己生成
- 所有文件操作都使用这个时间戳

**参数传递链**：
```
news-coordinator
  ├─ 生成：session_id, report_timestamp
  └─ 传递给 @category-processor(session_id, report_timestamp)
      └─ 传递给 @event-processor(session_id, report_timestamp)
          └─ 传递给 @event-report-generator(session_id, report_timestamp)
```

### 3.2 目录结构规范

**根目录**：
```
./output/{report_timestamp}/
```

**类别目录**：
```
./output/{report_timestamp}/{category}/
```

**日期目录**：
```
./output/{report_timestamp}/{category}/{date}/资讯汇总与摘要/
```

**事件文件**：
```
./output/{report_timestamp}/{category}/{date}/资讯汇总与摘要/{event_name}.md
./output/{report_timestamp}/{category}/{date}/资讯汇总与摘要/{event_name}/
./output/{report_timestamp}/{category}/{date}/资讯汇总与摘要/{event_name}/*.png
```

**图片引用**（在 `{event_name}.md` 中）：
```markdown
![描述](./{event_name}/图片文件名.png)
```

### 3.3 时间戳格式规范

**格式**：`report_YYYYMMDD_HHMMSS`

**示例**：
- `report_20260130_153000`
- `report_20260130_160000`

**规则**：
- 必须以 `report_` 开头
- 使用下划线分隔日期和时间
- 日期格式：`YYYYMMDD`
- 时间格式：`HHMMSS`
- 不允许其他格式（如 `report_2026-01-30`、`20260130_1530` 等）

---

## 4. 数据流设计

### 4.1 完整的数据流

```
news-coordinator（启动）
  │
  ├─ 生成：session_id = "20260130-abc123"
  └─ 生成：report_timestamp = "report_20260130_153000"  ← 统一时间戳
      │
      ├─ 并行调用所有类别
      │
      ├─ @category-processor(体育, session_id, report_timestamp)
      │   │
      │   ├─ 搜索体育新闻 → 保存到数据库（使用 session_id）
      │   ├─ 调用 @event-aggregator(session_id, category)
      │   │   └─ 聚合为事件列表
      │   │
      │   ├─ 为每个事件并行调用 @event-processor(事件名, session_id, report_timestamp, category, date)
      │   │   │
      │   │   ├─ 并发启动三个分析任务
      │   │   │   ├─ @validator(session_id, event_name)
      │   │   │   ├─ @timeline-builder(session_id, event_name)
      │   │   │   └─ @predictor(session_id, event_name)
      │   │   │
      │   │   └─ 调用 @event-report-generator(事件名, session_id, report_timestamp, category, date)
      │   │       │
      │   │       ├─ 创建目录：./output/{report_timestamp}/体育/2026-01-30/资讯汇总与摘要/{事件名}/
      │   │       ├─ 下载图片到：./output/{report_timestamp}/体育/2026-01-30/资讯汇总与摘要/{事件名}/
      │   │       ├─ 生成 md：./output/{report_timestamp}/体育/2026-01-30/资讯汇总与摘要/{事件名}.md
      │   │       │   图片引用：./{事件名}/图片.png  ← 使用相对路径
      │   │       └─ 更新数据库：local_image_paths
      │   │
      │   └─ 调用 @synthesizer(体育, session_id, report_timestamp, date)
      │       └─ 生成：./output/{report_timestamp}/体育/2026-01-30/资讯汇总与摘要/index.md
      │
      ├─ @category-processor(科技, session_id, report_timestamp)
      │   └─ （同上）
      │
      └─ 所有类别完成后，生成总索引
          └─ 生成：./output/{report_timestamp}/index.md
```

### 4.2 参数传递规范

**主 Agent (news-coordinator) 生成**：
- `session_id`：用于数据库隔离，格式 `YYYYMMDD-xxxxxxxx`
- `report_timestamp`：用于目录组织，格式 `report_YYYYMMDD_HHMMSS`

**传递给 Sub Agent**：
```python
# 格式
prompt=f"@{agent_name} {task_description}, session_id={session_id}, report_timestamp={report_timestamp}"

# 示例
prompt=f"@category-processor 处理体育类别的完整流程，session_id={session_id}, report_timestamp={report_timestamp}"
prompt=f"@event-processor 处理事件'极氪9X产能提升'，session_id={session_id}, report_timestamp={report_timestamp}"
```

**每个 Agent 接收参数**：
- 从 prompt 中解析 `session_id` 和 `report_timestamp`
- 数据库操作使用 `session_id`
- 文件操作使用 `report_timestamp`
- 传递给子 Agent 时继续传递这两个参数

---

## 5. 智能体职责划分

### 5.1 职责清单

| 智能体 | 核心职责 | 输入 | 输出 | 使用的参数 |
|--------|---------|------|------|-----------|
| **news-coordinator** | 顶层协调、生成统一时间戳、生成总索引 | 用户query | 总索引 | session_id, report_timestamp |
| **category-processor** | 单类别完整流程（搜索→聚合→分析→报告） | 类别名称 | 类别报告 | session_id, report_timestamp |
| **event-aggregator** | 将多条新闻聚合为事件 | 新闻列表 | 事件列表 | session_id |
| **event-processor** | 并发分析单个事件 | 事件名称 | 分析结果 + 调用报告生成 | session_id, report_timestamp |
| **validator** | 验证事件真实性 | 事件名称 | 验证结果 | session_id |
| **timeline-builder** | 构建事件时间轴 | 事件名称 | 时间轴 | session_id |
| **predictor** | 预测事件发展趋势 | 事件名称 | 预测结果 | session_id |
| **event-report-generator** | 生成单个事件的 md 文件 + 下载图片 | 事件名称 | md 文件 | session_id, report_timestamp |
| **synthesizer** | 生成类别级的 index.md | 类别名称 | index.md | session_id, report_timestamp |

### 5.2 职责边界

**event-processor vs event-report-generator**：
- `event-processor`：负责分析（验证、时间轴、预测），**不负责生成文件**
- `event-report-generator`：负责生成 md 文件和下载图片，**不负责分析**

**synthesizer 的定位**：
- **不是**生成整体报告（这是 `event-report-generator` 的事）
- **是**生成类别级的索引文件（index.md）

---

## 6. 修改文件清单

### 6.1 需要修改的文件

#### 1. prompts/news-coordinator.txt

**修改内容**：
- 添加 `report_timestamp` 的生成（与 `session_id` 一起）
- 在调用 `@category-processor` 时传递 `report_timestamp`
- 添加生成总索引的步骤
- 移除 `@report-organizer` 的调用（不再需要）

**关键位置**：
- 第 44-50 行：会话管理部分
- 第 110-135 行：阶段2：并行启动任务
- 第 136-165 行：阶段4：生成总索引

#### 2. prompts/category-processor.txt

**修改内容**：
- 添加接收 `report_timestamp` 的说明
- 在调用 `@event-processor` 时传递 `report_timestamp`
- 在调用 `@synthesizer` 时传递 `report_timestamp`
- 明确输出格式中不包含顶层目录（使用传递的 `report_timestamp`）

**关键位置**：
- 第 78-92 行：会话管理部分
- 第 130-210 行：工作流程
- 第 275-294 行：输出格式

#### 3. prompts/event-processor.txt

**修改内容**：
- 添加接收 `report_timestamp` 的说明
- 在调用 `@event-report-generator` 时传递 `report_timestamp`、`category`、`date`
- 在返回结果中添加 `report_path`

**关键位置**：
- 第 59-74 行：数据库工具部分
- 第 84-210 行：工作流程

#### 4. prompts/event-report-generator.txt

**修改内容**：
- **关键修改**：使用传递的 `report_timestamp`，不要自己生成
- 修复目录创建逻辑
- 修复图片引用路径为相对路径
- 明确目录结构：md 文件和图片文件夹在同一级

**关键位置**：
- 第 84-118 行：工作流程
- 第 93-103 行：阶段2：创建报告目录（核心修改）
- 第 104-116 行：阶段3：下载图片
- 第 130-155 行：阶段5：生成报告文件

#### 5. prompts/synthesizer.txt

**修改内容**：
- 明确定位为类别索引生成器
- 使用传递的 `report_timestamp`
- 生成 `资讯汇总与摘要/index.md`
- 清晰描述索引内容（事件列表、链接等）

**关键位置**：
- 第 10-15 行：核心任务
- 第 36-72 行：工作流程

### 6.2 可以删除的文件

- `prompts/report-organizer.txt`：不再需要（所有内容直接生成到统一目录下）

---

## 7. 验证清单

### 7.1 目录结构验证

- [ ] 所有文件都在 `report_{timestamp}/` 目录下
- [ ] 时间戳格式为 `report_YYYYMMDD_HHMMSS`
- [ ] 类别目录结构正确
- [ ] 日期目录结构正确
- [ ] 事件 md 文件和图片文件夹在同一级

### 7.2 文件完整性验证

- [ ] 每个类别都有 `index.md`（类别索引）
- [ ] 根目录有 `index.md`（总索引）
- [ ] 每个事件都有 `.md` 文件
- [ ] 事件图片文件夹存在
- [ ] 图片文件已下载

### 7.3 图片引用验证

- [ ] md 文件中的图片引用使用相对路径
- [ ] 相对路径格式正确：`./{event_name}/{image_file}`
- [ ] 图片文件实际存在
- [ ] 图片可以正常显示

### 7.4 索引文件验证

- [ ] 类别索引包含所有事件链接
- [ ] 总索引包含所有类别链接
- [ ] 链接路径正确（相对路径）
- [ ] 可以正常跳转

---

## 8. 附录

### 8.1 术语表

| 术语 | 定义 |
|------|------|
| **session_id** | 会话ID，用于数据库隔离，格式：`YYYYMMDD-xxxxxxxx` |
| **report_timestamp** | 报告时间戳，用于目录组织，格式：`report_YYYYMMDD_HHMMSS` |
| **category** | 新闻类别（如：体育新闻、科技新闻） |
| **event** | 新闻事件（如：极氪9X产能提升） |
| **date** | 日期（如：2026-01-30） |

### 8.2 示例

**完整的目录结构示例**：
```
output/
└── report_20260130_153000/
    ├── index.md                                    ← 总索引
    ├── 体育新闻/
    │   └── 2026-01-30/
    │       └── 资讯汇总与摘要/
    │           ├── index.md                        ← 体育类别索引
    │           ├── 樊振东宣布退出世界排名.md
    │           ├── 樊振东宣布退出世界排名/
    │           │   ├── 图片1.png
    │           │   └── 图片2.png
    │           └── 赵心童夺得斯诺克世锦赛冠军.md
    ├── 科技新闻/
    │   └── 2026-01-30/
    │       └── 资讯汇总与摘要/
    │           ├── index.md                        ← 科技类别索引
    │           └── 量子计算与AI大模型技术突破.md
    └── 政治新闻/
        └── 2026-01-30/
            └── 资讯汇总与摘要/
                └── index.md                        ← 政治类别索引
```

**图片引用示例**（在 `樊振东宣布退出世界排名.md` 中）：
```markdown
## 相关图片

![樊振东宣布退出](./樊振东宣布退出世界排名/图片1.png)
![比赛瞬间](./樊振东宣布退出世界排名/图片2.png)
```

**索引文件示例**（`体育新闻/2026-01-30/资讯汇总与摘要/index.md`）：
```markdown
# 体育新闻 - 2026年1月30日

## 事件列表

- [樊振东宣布退出世界排名](./樊振东宣布退出世界排名.md)
- [赵心童夺得斯诺克世锦赛冠军](./赵心童夺得斯诺克世锦赛冠军.md)
```

**总索引示例**（`report_20260130_153000/index.md`）：
```markdown
# 新闻资讯汇总报告

生成时间：2026年1月30日 15:30

## 目录

### 体育新闻
- [查看详情](./体育新闻/2026-01-30/资讯汇总与摘要/index.md)

### 科技新闻
- [查看详情](./科技新闻/2026-01-30/资讯汇总与摘要/index.md)

### 政治新闻
- [查看详情](./政治新闻/2026-01-30/资讯汇总与摘要/index.md)
```
