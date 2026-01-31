# 真实性验证模板

## 可信度评分

**综合评分**：{credibility_score}/100 | **置信等级**：{confidence_level}

---

## 证据链验证

{evidence_chain_items}

---

## 综合分析

### 1. 事实一致性 {fact_consistency_indicator}

{fact_consistency_content}

### 2. 时间序列完整 {time_sequence_indicator}

{time_sequence_content}

### 3. 多维度交叉验证 {multi_dimension_indicator}

{multi_dimension_content}

### 4. 逻辑合理性 {logic_consistency_indicator}

{logic_consistency_content}

### 5. 信息完整性 {information_completeness_indicator}

{information_completeness_content}

---

## 结论

**综合判断**：{overall_conclusion}

{detailed_conclusion}

---

_验证时间：{validation_time}_
_验证方法：多源交叉验证 | 数据点数量：{data_points_count} | 来源媒体数：{media_sources_count}_

---

## 填充格式说明

### 证据链步骤填充

模板中的 `{evidence_chain_items}` 需填充为：

```markdown
### 第{step_number}步：{step_title}

**验证焦点**：{verification_focus}

**核心结论**：{core_conclusion}

**支撑来源**（{source_count}个）：
1. [{news_title}]({news_url}) - {news_source} - {news_publish_time}
   - **关键数据/论述**："{quoted_text_or_data}"
   - **可靠性**：{reliability_emoji} {reliability_level}

**交叉验证结果**：
- **数据一致性**：{data_consistency_analysis}
- **时间吻合度**：{time_match_analysis}
- **多方印证**：{multi_source_verification}

**可靠性评估**：{reliability_emoji} {reliability_level}
```

### 综合分析填充

模板中的 5 个分析维度（如 `{fact_consistency_content}`）需填充为：

```markdown
{description}

**对比分析**：
| 验证项 | 媒体A数据 | 媒体B数据 | 一致性 |
|--------|-----------|-----------|--------|
| {item_1} | {value_a1} | {value_b1} | {consistency_1} |

**支撑来源**：
- [{source1_title}]({source1_url}) - {source1_source}
- [{source2_title}]({source2_url}) - {source2_source}
```

### 格式要求

- 每个证据链步骤必须包含至少一个来源链接（标题、URL、媒体、时间）
- 使用 ✅、⚠️、❌ 标注可靠性等级
- 禁止使用"多个媒体报道"等抽象表述
- 必须包含引用的具体论述或数据（quoted_text）
