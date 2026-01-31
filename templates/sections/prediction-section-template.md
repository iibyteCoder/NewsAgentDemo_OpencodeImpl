# 趋势预测模板

## 情景分析

{scenarios_content}

---

## 关键影响因素

{key_factors_content}

---

## 结论与建议

### 核心结论

{core_conclusion}

### 建议/展望

{recommendations}

---

_预测生成时间：{prediction_time}_
_数据来源：综合分析{sources_count}个来源 | 专家观点{expert_count}条 | 历史案例{case_count}个_

---

## 填充格式说明

### 情景填充

模板中的 `{scenarios_content}` 需填充为：

```markdown
### {scenario_type}情景（概率：{probability}%）

**核心假设**：{core_assumption}

**时间框架**：{timeframe}

**描述**：{description}

**关键因素**：
1. **{factor_name}**（影响：{impact_level}）
   - **来源**：[{source_title}]({source_url}) - {source_media}
   - **相关论述**："{relevant_quote}"

**风险因素**：
- {risk_factor_1}
- {risk_factor_2}
```

**情景排序**：按概率从高到低排列

### 关键影响因素填充

模板中的 `{key_factors_content}` 需填充为：

```markdown
### {factor_number}. {factor_name}（影响：{impact_level}）

**作用机制**：
{mechanism_description}

**关注指标**：
- {indicator_1}
- {indicator_2}

**来源支撑**：
- [{source1_title}]({source1_url}) - {source1_media}
- [{source2_title}]({source2_url}) - {source2_media}
```

### 结论与建议填充

```markdown
### 核心结论

{core_findings}

**支撑来源**：
- {source_1}
- {source_2}

### 建议/展望

**建议**：
- {recommendation_1}
- {recommendation_2}

**风险提示**：
- {risk_1} ([来源]({source_url}))
```
