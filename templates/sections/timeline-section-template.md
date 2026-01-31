# 事件时间轴模板

## 发展脉络

{development_path}

---

## 关键时间节点

{timeline_items}

---

## 影响与后果

{impacts_and_consequences}

---

_时间轴构建时间：{timeline_build_time}_

---

## 填充格式说明

### 时间节点填充

模板中的 `{timeline_items}` 需填充为：

```markdown
### {date} - {importance_emoji}

**{event_title}**

{description}

**来源**：{source_media} - [{source_title}]({source_url})

**影响**：{impact}

**因果关系**：{causal_relationship}

---
```

**重要性标注**：

- ⭐⭐⭐⭐ 极其重要
- ⭐⭐⭐ 高度重要
- ⭐⭐ 重要
- ⭐ 一般

### 影响与后果填充

模板中的 `{impacts_and_consequences}` 需填充为：

```markdown
## 影响与后果

**整体影响**：

{overall_impact}

**关键变化**：
- {key_change_1}
- {key_change_2}

**连锁反应**：
- {chain_reaction_1}
- {chain_reaction_2}
```

### 重要性映射

```text
importance_level = 4 → ⭐⭐⭐⭐ 极其重要
importance_level = 3 → ⭐⭐⭐ 高度重要
importance_level = 2 → ⭐⭐ 重要
importance_level = 1 → ⭐ 一般
```
