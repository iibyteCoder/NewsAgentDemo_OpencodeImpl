# 全局智能体规则

本文件定义了所有智能体必须遵守的全局规则，确保系统一致性和数据完整性。

---

## ⭐⭐⭐ session_id 管理规则（最重要）

### 基本原则

- ⭐ **单一生成源**：只有 `coordinator` 智能体允许生成 session_id
- ⭐ **严格禁止自生成**：其他所有智能体**严禁**自己生成或编造 session_id
- ⭐ **必须传递**：session_id 必须在智能体调用链中正确传递

### 各智能体的职责

#### session_id 生成者（唯一）
- **coordinator**：使用系统命令生成 session_id，传递给所有子任务

#### session_id 接收者 → 传递者
以下智能体从 prompt 接收 session_id，并传递给下游智能体：
- **category-handler** → @news-processor, @event-aggregator
- **event-analyzer** → @validator, @timeline-builder, @predictor
- **report-assembler** → 各个报告生成器
- **report-generator** → @report-assembler

#### session_id 接收者 → 数据库使用者
以下智能体从 prompt 接收 session_id，用于数据库操作：
- **news-processor**：保存数据到数据库
- **news-aggregator**：读取和更新数据库

#### session_id 接收者 → 传递者（调用 news-processor）
以下智能体从 prompt 接收 session_id，传递给 @news-processor：
- **event-validator** → @news-processor
- **event-timeline** → @news-processor
- **event-predictor** → @news-processor

### 统一规则格式

每个智能体应遵循以下格式描述 session_id 管理：

```markdown
## 关键原则

1. ⭐⭐⭐ **session_id 管理**：
   - ⭐ **从 prompt 接收**：从调用方传递的 prompt 中获取 session_id
   - ⭐ **禁止自己生成**：绝对不要自己生成或编造 session_id
   - ⭐ **[必须传递/用于数据库操作]**：[具体说明]
```

---

## ⭐⭐⭐ 工具权限规则

### fetch_article_content 工具

**唯一拥有者**：`news-processor`

**规则**：
- ⭐ 只有 news-processor 可以直接获取文章正文内容
- ⭐ 其他智能体（category-processor、validator、timeline-builder、predictor 等）都没有此权限
- ⭐ 需要文章内容时，必须通过 @news-processor 获取

---

## ⭐⭐⭐ 并行处理规则

### 调用 @news-processor 时

**规则**：
- ⭐⭐⭐ **并行调用**：搜索到的所有链接必须同时并行调用 @news-processor
- ❌ 不要串行逐个处理链接
- ❌ 不要批量处理多个链接
- ❌ 不要尝试自己获取文章内容
- ✅ 一次性并行调用所有链接

**调用格式**：
```text
@news-processor 处理这个链接：{url} session_id={session_id} category={category}
```

---

## ⭐⭐ 数据库存储规则

### 新版架构（数据库存储）

**目的**：避免上下文过长导致信息丢失

**规则**：
- ⭐⭐⭐ **保存到数据库**：分析结果必须保存到数据库，不要在返回中包含完整数据
- ⭐⭐⭐ **按需读取**：报告生成器从数据库按需读取数据
- ⭐⭐ **状态管理**：使用 `news-storage_mark_section_failed` 标记失败

**适用智能体**：
- event-validator
- event-timeline
- event-predictor
- report-assembler
- report-generator

---

## ⭐ 统一时间戳规则

**规则**：
- ⭐ 使用传递的 `report_timestamp`，不要自己生成
- ⭐ 所有智能体使用相同的时间戳格式：`report_YYYYMMDD_HHMMSS`

---

## 使用说明

### 如何在智能体 prompt 中引用

**方式1：直接在"关键原则"部分添加**

```markdown
## 关键原则

1. ⭐⭐⭐ **session_id 管理**：
   - ⭐ **从 prompt 接收**：从调用方传递的 prompt 中获取 session_id
   - ⭐ **禁止自己生成**：绝对不要自己生成或编造 session_id
   - ⭐ **必须传递**：调用 [下游智能体] 时必须传递 session_id
2. [其他关键原则...]
```

**方式2：简化引用**

```markdown
## 关键原则

遵守 `global-agent-rules.md` 中定义的 session_id 管理规则：

- ⭐⭐⭐ **从 prompt 接收 session_id**
- ⭐⭐⭐ **禁止自己生成 session_id**
- ⭐⭐⭐ **[必须传递给下游 / 用于数据库操作]**

[其他关键原则...]
```

---

## 规则优先级

1. ⭐⭐⭐ **核心规则**：必须遵守，违反将导致系统故障
   - session_id 管理
   - 工具权限
   - 并行处理

2. ⭐⭐ **重要规则**：强烈建议遵守，影响数据质量
   - 数据库存储
   - 数据验证

3. ⭐ **建议规则**：最佳实践，提升系统性能
   - 统一时间戳
   - 错误处理

---

## 维护说明

- 修改本文件时，确保所有智能体的 prompt 文件保持一致
- 添加新智能体时，参考本文件定义其 session_id 管理职责
- 定期审查各智能体是否符合全局规则
