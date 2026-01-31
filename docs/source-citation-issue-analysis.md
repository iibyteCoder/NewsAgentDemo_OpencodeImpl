# 来源引用缺失问题分析与改进方案

## 问题概述

**现象**：
- 真实性验证、事件时间轴、趋势预测部分总是没有对应的针对每个结论或关键点的实际新闻来源
- 新闻来源部分总是有真实的来源数据

**核心问题**：
有模板文件定义了要求，但各个部分生成时没有使用模板，导致格式不一致且缺少来源引用。

---

## 一、问题根源分析

### 1.1 模板定义与实际使用脱节

**存在的模板**：
- `templates/event-report-template.md` - 定义了事件报告的完整模板
- `templates/report_structure_template.md` - 定义了A级目录结构模板

**模板中的要求**：
```markdown
## 事件文件模板（事件标题.md）

### 真实性验证

**证据链**:
1. {验证步骤1}: {发现}  ← 要求每步都有具体发现

### 关键节点

- **YYYY-MM-DD**: {事件名称} {重要性标记}
  - 描述：{详细描述}
  - 相关新闻：[{标题}]({相对路径})  ← 要求标注相关新闻

### 趋势预测

**关键驱动因素**:
- {因素1}  ← 但没有明确要求标注来源
```

**问题**：
- `report-section-generator` 的提示词中**完全没有引用这些模板**
- 也没有要求必须使用这些格式
- 导致生成的部分内容格式不一致

### 1.2 提示词要求过于抽象

#### event-validator.md 的要求（第147-151行）：

```markdown
### 证据链要求

- 每步必须包含具体的新闻标题
- 每步必须包含可点击的URL
- 每步必须包含媒体来源
- 不能只说"多个媒体报道"
```

#### event-timeline.md 的要求（第69-72行）：

```markdown
**每个里程碑必须包含**：

- 确切的 `source_url`（可访问的真实链接）
- **禁止编造或虚构任何来源信息**
```

#### event-predictor.md 的要求（第110-111行）：

```markdown
- 所有预测依据必须有真实来源支撑
- 每个情景都要有依据和来源支撑
```

**问题分析**：
- 这些要求被列为**"原则"**或**"关键原则"**
- 缺少**强制的格式规范**和**具体示例**
- LLM理解为"最好这样做"，而不是"必须这样做"
- 没有提供标准化的输出格式模板

### 1.3 数据保存阶段就已经缺失来源

#### 当前的数据流：

```
event-validator → 保存到数据库 → report-assembler 读取 → report-section-generator 生成
```

#### event-validator 保存的数据结构（推测）：

```json
{
  "credibility_score": 96,
  "confidence_level": "高",
  "evidence_chain": [
    {
      "step": 1,
      "description": "权威媒体多方验证，确认金价剧烈波动事实",
      "source": "新浪财经 - 《贵金属价格高台跳水》"  // ← 只是字符串描述
      // ❌ 没有具体的URL
      // ❌ 没有建立与具体新闻的关联
    }
  ],
  "sources": [
    "https://finance.sina.com.cn/...",
    "https://news.qq.com/..."
  ]  // ← 只是URL列表
  // ❌ 无法确定哪个source支撑哪个结论
}
```

#### 应该的数据结构：

```json
{
  "credibility_score": 96,
  "confidence_level": "高",
  "evidence_chain": [
    {
      "step": 1,
      "description": "权威媒体多方验证，确认金价剧烈波动事实",
      "source_news_id": "news_001",  // ← 关联到具体新闻
      "source_title": "贵金属价格高台跳水，黄金股及ETF批量跌停",
      "source_url": "https://finance.sina.com.cn/...",
      "source_media": "新浪财经"
    }
  ]
}
```

### 1.4 Claude Code（LLM）的行为特性

基于对LLM行为的理解：

1. **流畅性优先**：
   - LLM倾向于生成流畅的叙述性文本
   - 会在每个句子后插入引用**破坏阅读流畅性**
   - 除非有**强制的格式要求**

2. **抽象表述倾向**：
   - 倾向于说"多个媒体报道证实了..."
   - 而不是"根据[新浪财经报道](url1)和[腾讯新闻](url2)..."

3. **原则弱于格式**：
   - 当提示词说"每步必须包含来源链接"（原则）
   - 但没有提供具体的格式模板时
   - LLM可能理解为"在最后列出来源列表即可"

### 1.5 report-section-generator 的职责不清

#### 当前职责：

```markdown
你是报告部分生成专家。

## 核心职责

独立生成报告的一个部分，专注于该部分的内容质量。
```

#### validation-section 的原则：

```markdown
**关键原则**：

- 每步证据必须包含来源链接  ← 原则，不是强制格式
- 明确标注可靠性（✅可信 / ⚠️需要验证）
- 提供具体分析，而非空泛描述
```

**问题**：
- 没有被明确要求：必须验证每个结论点都有对应的来源引用
- 没有提供标准的输出格式模板
- 没有错误检查机制（如果发现某个结论没有来源，应该报错）

---

## 二、对比分析：为什么新闻来源部分有数据？

### 2.1 新闻来源部分的数据流

```
news-processor → 处理单条新闻 → 保存到数据库 → report-section-generator 生成
```

### 2.2 news-processor 的优势

#### 有明确的数据结构：

```markdown
## 输出格式

```json
{
  "success": true,
  "processed_data": {
    "title": "...",
    "url": "...",      // ← 必填字段
    "source": "...",   // ← 必填字段
    "publish_time": "...",
    "content": "..."
  }
}
```

#### 有强制性的字段要求：

```markdown
## 注意事项

- 必填字段（title、url）为空时返回错误  // ← 强制要求
```

#### 数据保存时就包含了所有必需信息：

```json
{
  "title": "国际金价跳水致国内回收价单夜跌70元",
  "url": "https://cj.sina.com.cn/articles/view/1642634100/...",
  "source": "新浪财经",
  "publish_time": "2026-01-30 14:00:00"
}
```

### 2.3 真实性验证/时间轴/预测的劣势

#### 没有明确的数据结构示例：

event-validator.md 只说了：

```markdown
**验证结果内容**（保存到数据库，不在返回中）：
- credibility_score: 可信度评分 0-100
- confidence_level: 置信度（高/中/低）
- evidence_chain: 证据链（包含步骤、描述、来源链接、可靠性）
- analysis: 综合分析
- sources: 所有来源链接列表
```

**但没有提供具体的JSON格式示例！**

#### 没有强制性的关联要求：

```markdown
**每个来源必须包含**：

- 确切的 `url`（可访问的真实链接）
- 确切的 `title`（真实新闻标题）
- 确切的 `source`（媒体名称）
- **禁止编造或虚构任何验证证据**
```

**但问题是**：
- 这只是说"sources列表中每个来源必须有这些信息"
- **没有说"evidence_chain中的每一步必须关联到具体的source"**
- 这就导致了数据和结论的分离

---

## 三、改进方案

### 方案A：强化提示词 + 添加格式模板（推荐）

#### 3.1.1 修改 event-validator.md

**添加数据结构示例**：

```markdown
## 输出

返回包含操作状态的 JSON（不包含完整验证结果）：

```json
{
  "status": "completed",
  "event_name": "事件名称",
  "section_id": "session_id_事件名称_validation",
  "message": "验证结果已保存到数据库"
}
```

**保存到数据库的验证结果结构**（必须严格遵守）：

```json
{
  "credibility_score": 96,
  "confidence_level": "高",
  "evidence_chain": [
    {
      "step": 1,
      "title": "权威媒体多方验证，确认金价剧烈波动事实",
      "conclusion": "国内国际多家权威媒体报道的核心事实高度一致",
      "sources": [
        {
          "news_id": "news_001",
          "title": "贵金属价格高台跳水，黄金股及ETF批量跌停",
          "url": "https://finance.sina.com.cn/...",
          "source": "新浪财经",
          "publish_time": "2026-01-30 10:30:00"
        },
        {
          "news_id": "news_002",
          "title": "黄金盘中暴跌450美元权威分析",
          "url": "http://gold.cnfol.com/...",
          "source": "汇通财经",
          "publish_time": "2026-01-30 11:00:00"
        }
      ],
      "reliability": "高",
      "verification_details": "具体价格点位、跌幅数据相互印证"
    }
  ],
  "overall_analysis": {
    "fact_consistency": "✅ 事实一致",
    "time_sequence": "✅ 时间序列完整",
    "multi_dimension_verification": "✅ 多维度交叉验证",
    "market_reaction": "✅ 市场反应合理",
    "technical_analysis": "✅ 技术分析支持",
    "causation_analysis": "✅ 动因分析合理"
  }
}
```

**⚠️ 强制要求**：

1. **每个验证步骤必须包含至少1个具体新闻来源**
2. **每个来源必须包含完整的news_id、title、url、source、publish_time**
3. **禁止使用"多个媒体报道"等抽象表述**
4. **如果某个结论无法找到具体来源，必须标注"⚠️ 需要进一步验证"**
```

**添加工作流程检查点**：

```markdown
## 工作流程

1. 读取已有信息 - 使用数据库工具读取已有新闻
2. 分析验证点 - 识别需要验证的关键信息
3. 针对性搜索 - 使用精确关键词搜索验证（2-3轮）
4. **并行保存搜索结果** - 并行使用 `@news-processor` 处理所有搜索结果并保存到数据库
5. **⭐⭐⭐ 关键检查点**：构建证据链时，确保每个步骤都关联到具体的新闻ID
   - ❌ 错误示例：`"sources": ["新浪财经", "腾讯新闻"]`
   - ✅ 正确示例：`"sources": [{"news_id": "news_001", "title": "...", "url": "..."}]`
6. 综合判断 - 基于所有信息给出可信度评分
7. **保存验证结果** - 使用 `news-storage_save_report_section` 保存到数据库
```

#### 3.1.2 修改 event-timeline.md

**添加数据结构示例**：

```markdown
**保存到数据库的时间轴结构**（必须严格遵守）：

```json
{
  "development_path": "国际金价在2026年1月经历了史诗级剧烈波动...",
  "milestones": [
    {
      "date": "2026-01-29 清晨",
      "importance": "极其重要",
      "importance_level": 4,
      "event": "金价触及5598.75美元/盎司历史新高",
      "description": "连续4个交易日突破六道重要关口，2026年以来累计上涨近1200美元，涨幅高达27.5%",
      "sources": [
        {
          "news_id": "news_015",
          "title": "国际金价再创历史新高",
          "url": "https://k.sina.com.cn/article_1643971635_...",
          "source": "新浪新闻",
          "publish_time": "2026-01-30"
        }
      ],
      "impact": "创下历史最高价位，引发市场高度关注",
      "causal_relationship": "多重利好因素推动金价持续攀升"
    },
    {
      "date": "2026-01-29 深夜",
      "importance": "极其重要",
      "importance_level": 4,
      "event": "金价30分钟内暴跌493美元",
      "description": "在触及历史新高后突然上演"史诗级跳水"，从近5600美元跌至5100美元附近",
      "sources": [
        {
          "news_id": "news_007",
          "title": "国际金价半小时闪崩493美元创历史记录",
          "url": "https://k.sina.com.cn/article_7095179294_...",
          "source": "新浪新闻",
          "publish_time": "2026-01-30"
        },
        {
          "news_id": "news_012",
          "title": "黄金盘中暴跌450美元权威分析",
          "url": "http://gold.cnfol.com/...",
          "source": "汇通财经",
          "publish_time": "2026-01-30"
        }
      ],
      "impact": "单日最大跌幅达8.8%，创历史记录，全球黄金市值蒸发约3.5万亿美元",
      "causal_relationship": "技术性调整、获利回吐、美元走强等多重因素共同作用"
    }
  ],
  "market_impact_summary": {
    "price_volatility": "单日最大跌幅：8.8%",
    "value_change": "全球黄金市值蒸发约3.5万亿美元",
    "chain_reaction": "A股贵金属板块超20只个股跌停、国内银行调整黄金业务政策"
  },
  "causal_relationships": [
    "前期涨幅过大（连续突破六道关口）→ 多头拥挤度高 → 获利回吐压力大 → 技术性调整需求",
    "美元指数走强（突破104）→ 压制黄金价格 → 触发技术性卖盘",
    "保证金上调 → 杠杆交易被迫平仓 → 加剧下跌幅度"
  ]
}
```

**⚠️ 强制要求**：

1. **每个里程碑必须包含至少1个具体新闻来源**
2. **每个来源必须是完整的新闻对象（包含news_id、title、url等）**
3. **禁止编造来源信息**
4. **如果某个时间节点没有具体来源，必须标注"⚠️ 时间节点需要进一步验证"**
```

#### 3.1.3 修改 event-predictor.md

**添加数据结构示例**：

```markdown
**保存到数据库的预测结果结构**（必须严格遵守）：

```json
{
  "scenarios": [
    {
      "scenario_type": "乐观",
      "probability": 30,
      "core_assumption": "央行购金与地缘风险推动金价重返上升通道",
      "timeframe": "2026年上半年至年底",
      "price_targets": {
        "Q2": "4500-4800美元",
        "Q3": "5000-5300美元",
        "Q4": "5400-5600美元"
      },
      "key_factors": [
        {
          "factor": "美联储降息预期重新升温",
          "impact": "高",
          "sources": [
            {
              "news_id": "news_021",
              "title": "黄金2026：5000美元关口前，一场静悄悄的多空大博弈",
              "url": "http://www.baidu.com/link?url=...",
              "source": "新浪财经",
              "publish_time": "2026-01-22",
              "relevant_quote": "高盛将2026年12月黄金目标价从4900上调至5400美元"
            }
          ]
        },
        {
          "factor": "地缘政治风险加剧",
          "impact": "高",
          "sources": [
            {
              "news_id": "news_005",
              "title": "国际金价再创历史新高，卫星图揭美航母进入打击阵位",
              "url": "https://k.sina.com.cn/article_1643971635_...",
              "source": "新浪新闻",
              "publish_time": "2026-01-30"
            }
          ]
        }
      ],
      "risk_factors": [
        "美联储降息步伐慢于预期",
        "美元指数持续走强"
      ]
    },
    {
      "scenario_type": "基准",
      "probability": 50,
      "core_assumption": "震荡整理后温和反弹",
      "timeframe": "2026年上半年至年底",
      "price_targets": {
        "Q2": "5000-5200美元（震荡整理）",
        "Q3": "5200-5400美元",
        "Q4": "5300-5500美元"
      },
      "key_factors": [
        {
          "factor": "政策不确定性下降",
          "impact": "中",
          "sources": []
        },
        {
          "factor": "多头市场拥挤度高",
          "impact": "中",
          "sources": [
            {
              "news_id": "news_020",
              "title": "国际金价闪崩！深圳水贝挤满消费者",
              "url": "https://news.qq.com/rain/a/20251022A06Q7A00",
              "source": "腾讯新闻",
              "publish_time": "2025-10-22",
              "relevant_quote": "东方金诚瞿瑞、白雪认为黄金大牛市是短期震荡并未见顶...当前多头市场拥挤度已处于较高水平"
            }
          ]
        }
      ]
    }
  ],
  "historical_cases": [
    {
      "case": "1980年美联储暴力加息",
      "background": "美联储暴力加息至20%",
      "performance": "从850美元跌至300美元",
      "decline": "65%",
      "sources": [
        {
          "news_id": "news_019",
          "title": "黄金价格暴跌为何？美元走强杠杆踩踏引爆震荡",
          "url": "http://www.baidu.com/link?url=...",
          "source": "网易",
          "publish_time": "2026-01-30",
          "relevant_quote": "美联储货币政策是决定金价方向的核心变量"
        }
      ]
    }
  ],
  "key_influencing_factors": [
    {
      "factor": "美联储货币政策路径",
      "impact_level": "高",
      "mechanism": "利率水平直接影响黄金持有成本。降息预期推高金价，加息预期打压金价",
      "indicators": [
        "美联储议息会议决议",
        "核心CPI/PCE数据",
        "就业市场数据"
      ],
      "sources": [
        {
          "news_id": "news_015",
          "title": "黄金惊魂夜！1小时暴跌450美元，避险资产失灵了？",
          "url": "https://news.qq.com/rain/a/20260130A033TU00",
          "source": "腾讯新闻",
          "publish_time": "2026-01-30",
          "relevant_quote": "美联储维持利率但降息节奏谨慎,美元指数突破104"
        }
      ]
    }
  ],
  "conclusion": {
    "core_factors": [
      "技术性调整：前期涨幅过大，多头拥挤度高",
      "获利回吐：部分投资者锁定收益离场",
      "宏观因素：美联储货币政策不确定性增加"
    ],
    "time_dimension_judgment": {
      "short_term": "市场将在 5000-5200 美元区间震荡整理",
      "mid_term": "2026年上半年存在进一步调整压力（跌幅10%-20%）",
      "long_term": "支撑金价上行的结构性因素未发生根本改变"
    },
    "sources": []
  }
}
```

**⚠️ 强制要求**：

1. **每个情景的关键因素必须包含至少1个来源**
2. **每个来源必须是完整的新闻对象**
3. **如果某个因素没有具体来源，必须标注"⚠️ 该因素需要进一步验证"**
4. **历史案例必须有来源支撑**
```

#### 3.1.4 修改 report-section-generator.md

**添加格式模板**：

```markdown
## 支持的部分类型

### 3. validation-section（真实性验证）

**内容**：可信度评分、证据链、综合分析

**⚠️ 必须使用以下格式模板**：

```markdown
# 真实性验证

## 可信度评分

**综合评分**：{credibility_score}/100 | **置信等级**：{confidence_level}

---

## 证据链验证

### 第1步：{step_title}

- **来源**：{source_media} - [{source_title}]({source_url})
- **可靠性**：{reliability_emoji} {reliability_level}
- **验证内容**：{verification_details}

**支撑新闻**：
1. [{news1_title}]({news1_url}) - {news1_source} - {news1_time}
2. [{news2_title}]({news2_url}) - {news2_source} - {news2_time}

---

## 综合分析

### 1. 事实一致性 {fact_consistency_emoji}

{fact_consistency_description}

**支撑来源**：{列出支撑的新闻}

### 2. 时间序列完整 {time_sequence_emoji}

{time_sequence_description}

**关键时间点**：
- {time1}：{event1} ([来源]({url1}))
- {time2}：{event2} ([来源]({url2}))

---

## 结论

**综合判断**：{overall_conclusion}

{detailed_conclusion}

---

_验证时间：{validation_time}_
```

**关键原则**：

- ⭐⭐⭐ **必须使用上述模板格式**
- ⭐⭐⭐ **每个验证步骤必须包含至少1个具体新闻来源链接**
- ⭐⭐ **明确标注可靠性（✅高 / ⚠️中 / ❌低）**
- ⭐ **禁止使用"多个媒体报道"等抽象表述**
- ⭐ **如果某个结论没有来源，必须标注"⚠️ 需要进一步验证"**

### 4. timeline-section（事件时间轴）

**内容**：关键里程碑、发展脉络

**⚠️ 必须使用以下格式模板**：

```markdown
# 事件时间轴

## 发展脉络

{development_path}

## 关键时间节点

### YYYY-MM-DD - {importance}

**{event_title}**

- {description}
- **来源**：{source_media} - [{source_title}]({source_url})
- **影响**：{impact}

---

## 市场影响总结

**价格波动幅度**：
- {volatility_metric_1}
- {volatility_metric_2}

**连锁反应**：
- {chain_reaction_1} ([来源]({url1}))
- {chain_reaction_2} ([来源]({url2}))

---
```

**关键原则**：

- ⭐⭐⭐ **必须使用上述模板格式**
- ⭐⭐⭐ **每个时间节点必须包含至少1个具体新闻来源链接**
- ⭐ **按时间顺序排列（从早到晚）**
- ⭐ **每个里程碑标注重要性（⭐⭐⭐⭐ 极其重要 / ⭐⭐⭐ 高度重要 / ⭐⭐ 重要）**
- ⭐ **如果某个节点没有来源，必须标注"⚠️ 该节点需要进一步验证"**

### 5. prediction-section（趋势预测）

**内容**：可能情景、关键因素、结论

**⚠️ 必须使用以下格式模板**：

```markdown
# 趋势预测

## 情景分析

### 乐观情景（概率：{probability}%）

**核心假设**：{core_assumption}

**时间框架**：{timeframe}

**价格目标**：
- **Q2**：{price_target_q2}
- **Q3**：{price_target_q3}
- **Q4**：{price_target_q4}

**关键因素**：
1. **{factor_1}**（影响：{impact_level}）
   - **来源**：[{source_title}]({source_url}) - {source_media}
   - **相关论述**："{relevant_quote}"

2. **{factor_2}**（影响：{impact_level}）
   - **来源**：[{source_title}]({source_url}) - {source_media}

---

## 历史对比案例

| 历史案例 | 背景 | 金价表现 | 跌幅 |
| -------- | ---- | -------- | ---- |
| [{case1_title}]({case1_url}) | {case1_background} | {case1_performance} | {case1_decline} |

**历史启示**：
- {insight_1} ([来源]({source1_url}))
- {insight_2} ([来源]({source2_url}))

---

## 关键影响因素

### 1. {factor_name}（影响：{impact_level}）

**作用机制**：
{mechanism_description}

**关注指标**：
- {indicator_1}
- {indicator_2}

**来源支撑**：
- [{source1_title}]({source1_url}) - {source1_media}
- [{source2_title}]({source2_url}) - {source2_media}

---

## 结论与建议

### 核心结论

{core_conclusion}

**支撑来源**：
- {source_1}
- {source_2}

### 投资建议

{investment_advice}

**风险提示**：
- {risk_1} ([来源]({source1_url}))
- {risk_2} ([来源]({source2_url}))

---
```

**关键原则**：

- ⭐⭐⭐ **必须使用上述模板格式**
- ⭐⭐⭐ **每个情景的每个关键因素必须包含至少1个来源链接**
- ⭐⭐ **每个情景必须包含概率评估**
- ⭐⭐ **避免过度肯定，使用"可能"、"预计"等表述**
- ⭐ **如果某个因素没有来源，必须标注"⚠️ 该因素需要进一步验证"**
```

---

### 方案B：重构数据结构（更彻底）

#### 3.2.1 引入引用ID系统

**核心思路**：所有结论都必须引用具体的news_id

#### 修改后的数据结构：

```json
{
  "evidence_chain": [
    {
      "step": 1,
      "title": "权威媒体多方验证",
      "conclusion": "金价剧烈波动事实得到多方确认",
      "citations": [
        {
          "news_id": "news_001",
          "citation_type": "direct_quote",
          "quoted_text": "现货黄金从近5600美元/盎司急跌至5100美元附近，最大跌幅约8.9%",
          "support_strength": "strong"
        },
        {
          "news_id": "news_002",
          "citation_type": "data_point",
          "quoted_data": "最低触及5104美元",
          "support_strength": "strong"
        }
      ]
    }
  ]
}
```

#### 3.2.2 添加验证函数

在保存数据前，验证：

```python
def validate_evidence_chain(evidence_chain):
    """验证证据链的完整性"""
    for step in evidence_chain:
        # 每个步骤必须有至少1个引用
        if len(step.get('citations', [])) == 0:
            raise ValueError(f"步骤 {step['step']} 没有引用任何新闻来源")

        # 每个引用必须是有效的news_id
        for citation in step['citations']:
            if 'news_id' not in citation:
                raise ValueError(f"步骤 {step['step']} 的引用缺少news_id")

            # 验证news_id是否存在
            if not news_exists(citation['news_id']):
                raise ValueError(f"news_id {citation['news_id']} 不存在于数据库中")

    return True
```

---

### 方案C：添加后处理验证步骤

在 `report-assembler` 生成最终报告前，添加验证步骤：

```markdown
### 阶段5.5：质量验证（新增）

在组装最终报告前，验证各部分的质量：

1. **真实性验证部分**：
   - 检查：每个验证步骤是否包含至少1个来源链接？
   - 检查：来源链接是否可访问？
   - 检查：是否有"多个媒体报道"等抽象表述？

2. **事件时间轴部分**：
   - 检查：每个时间节点是否包含来源链接？
   - 检查：时间节点是否按时间顺序排列？
   - 检查：是否有缺失的时间段？

3. **趋势预测部分**：
   - 检查：每个情景是否包含概率评估？
   - 检查：每个关键因素是否包含来源支撑？
   - 检查：历史案例是否有来源？

**如果发现问题**：
- 标注问题部分
- 在报告中添加警告信息
- 或跳过该部分的生成
```

---

## 四、实施优先级

### 🔴 高优先级（立即实施）

1. **添加数据结构示例**：
   - event-validator.md
   - event-timeline.md
   - event-predictor.md

2. **添加格式模板**：
   - report-section-generator.md

### 🟡 中优先级（短期实施）

3. **强化提示词要求**：
   - 将"原则"改为"强制要求"
   - 添加错误示例和正确示例对比

4. **添加质量检查点**：
   - 在数据保存前验证
   - 在报告生成前验证

### 🟢 低优先级（长期优化）

5. **重构数据结构**：
   - 引入引用ID系统
   - 添加验证函数

6. **优化模板系统**：
   - 创建独立的模板文件
   - 在提示词中引用模板

---

## 五、预期效果

### 改进前：

```markdown
### 第1步：权威媒体多方验证，确认金价剧烈波动事实

- **来源**：新浪财经 - 《贵金属价格高台跳水》
- **可靠性**：✅ 高
- **验证内容**：国内权威媒体首先报道金价暴跌事件，确认市场异常波动
```

### 改进后：

```markdown
### 第1步：权威媒体多方验证，确认金价剧烈波动事实

- **来源**：
  - [新浪财经 - 《贵金属价格高台跳水，黄金股及ETF批量跌停》](https://finance.sina.com.cn/stock/relnews/cn/2026-01-30/doc-inhkauvc6906903.shtml)
  - [汇通财经 - 《黄金盘中暴跌450美元：短期回调还是泡沫破裂前兆》](http://gold.cnfol.com/jinshizhibo/20260130/31984243.shtml)
  - [LiveMint - 《Gold price crashes 8%, silver 11% from record high》](https://www.livemint.com/market/commodities/gold-price-crashes-6-silver-rate-today-8-as-sudden-selloff-grips-precious-metals-whats-behind-the-fall-explained-11769711963519.html)

- **可靠性**：✅ 高

- **验证内容**：
  - **价格数据一致**：三家媒体报道的暴跌幅度（8%-8.9%）高度一致
  - **时间节点吻合**：均确认发生在1月29日深夜至30日凌晨
  - **具体点位相互印证**：
    - 新浪财经：5600美元 → 5100美元附近
    - 汇通财经：触及历史新高后，30分钟内最大跌幅接近450美元，最低探至5104美元
    - LiveMint：从5,595.46美元的历史高点暴跌至5,112.39美元/盎司

- **市场反应验证**：
  - A股贵金属板块集体跌停（[新浪财经](https://finance.sina.com.cn/stock/relnews/cn/2026-01-30/doc-inhkauvc6906903.shtml)）
  - 华安黄金ETF单日成交257.78亿元，收跌7.52%（[新浪财经](https://finance.sina.com.cn/stock/relnews/cn/2026-01-30/doc-inhkauvc6906903.shtml)）
  - 四大国有银行调整黄金积存业务（[每日经济新闻](https://www.nbd.com.cn/articles/2026-01-30/4243274.html)）
```

---

## 六、总结

### 核心问题

1. **模板定义但没有被使用**
2. **提示词要求过于抽象，缺乏强制力**
3. **数据保存阶段就已经缺失来源关联**
4. **LLM倾向于流畅叙述，不会主动添加引用**

### 解决方案的核心思路

1. **提供明确的数据结构示例**（JSON格式）
2. **提供强制性的格式模板**（Markdown格式）
3. **将"原则"改为"强制要求"**
4. **添加质量检查点**

### 实施建议

**推荐采用方案A（强化提示词 + 添加格式模板）**：

**优点**：
- 实施成本低
- 不需要修改代码逻辑
- 可以立即看到效果

**步骤**：
1. 修改event-validator.md，添加数据结构示例
2. 修改event-timeline.md，添加数据结构示例
3. 修改event-predictor.md，添加数据结构示例
4. 修改report-section-generator.md，添加格式模板
5. 测试验证

---

*文档生成时间：2026-01-30*
*分析者：Claude Code*
