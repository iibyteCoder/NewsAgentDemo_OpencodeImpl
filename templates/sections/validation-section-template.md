# 真实性验证模板

---

<!-- TEMPLATE_DOC_START -->

## 填充说明

### 核心要求

1. **证据链步骤**（`{evidence_chain_items}`）：
   - 每步包含：步骤标题、验证焦点、核心结论、支撑来源、交叉验证结果
   - 支撑来源格式：`[{title}]({url}) - {source} - {time}`
   - 必须包含引用的具体论述或数据
   - 使用 ✅、⚠️、❌ 标注可靠性

2. **综合分析维度**（5个 `{xxx_content}` 字段）：
   - 事实一致性、时间序列、多维度验证、逻辑合理性、信息完整性
   - 包含具体分析和来源链接
   - 使用对比表格（如适用）

3. **禁止事项**：
   - 禁止使用"多个媒体报道"等抽象表述
   - 必须提供具体的标题和链接

<!-- TEMPLATE_DOC_END -->

---

## 模板格式

### 可信度评分

**综合评分**：{credibility_score}/100 | **置信等级**：{confidence_level}

### 证据链验证

{evidence_chain_items}

### 综合分析

#### 1. 事实一致性 {fact_consistency_indicator}

{fact_consistency_content}

#### 2. 时间序列完整 {time_sequence_indicator}

{time_sequence_content}

#### 3. 多维度交叉验证 {multi_dimension_indicator}

{multi_dimension_content}

#### 4. 逻辑合理性 {logic_consistency_indicator}

{logic_consistency_content}

#### 5. 信息完整性 {information_completeness_indicator}

{information_completeness_content}

### 结论

**综合判断**：{overall_conclusion}

{detailed_conclusion}

_验证时间：{validation_time}_
_验证方法：多源交叉验证 | 数据点数量：{data_points_count} | 来源媒体数：{media_sources_count}_
