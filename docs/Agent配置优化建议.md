# OpenCode Agent 配置优化建议

## 优化日期
2026-01-29

---

## 关键发现

### 1. MCP 工具名称不匹配 ⚠️

**问题描述**：
- MCP 服务器名称：`web_browser`（下划线）
- 工具通配符：`web-browser*`（连字符）
- 实际工具名：`web-browser_*_tool`（连字符）

**影响**：
- 通配符 `web-browser*` 可能无法匹配到实际工具
- Agent 可能无法使用 MCP 工具

**解决方案**：
```json
"tools": {
  "web-browser_*": true  // 使用下划线匹配服务器名
}

// 或者明确列出所有工具
"tools": {
  "web-browser_baidu_search_tool": true,
  "web-browser_baidu_news_search_tool": true,
  // ...
}
```

### 2. Model 配置优化

**当前配置**：
- 所有 agent 都没有指定 model
- Subagent 会继承 primary agent 的模型

**优化建议**：
为不同的 agent 配置不同的模型，平衡速度和质量：

```json
{
  "agent": {
    "news-collector": {
      "model": "anthropic/claude-sonnet-4-20250514"  // 主模型
    },
    "event-aggregator": {
      "model": "anthropic/claude-haiku-4-20250514"  // 快速模型（简单任务）
    },
    "validator": {
      "model": "anthropic/claude-sonnet-4-20250514"  // 主模型（复杂任务）
    },
    "timeline-builder": {
      "model": "anthropic/claude-sonnet-4-20250514"  // 主模型
    },
    "predictor": {
      "model": "anthropic/claude-sonnet-4-20250514"  // 主模型
    },
    "synthesizer": {
      "model": "anthropic/claude-haiku-4-20250514"  // 快速模型（只是格式化）
    }
  }
}
```

**成本优化**：
- Haiku 价格更低（约为 Sonnet 的 1/10）
- 简单任务使用 Haiku，复杂任务使用 Sonnet
- 预计可以节省 30-50% 的 API 成本

### 3. MaxSteps 配置一致性

**问题**：
- JSON 中配置了 `maxSteps`
- Markdown 文件头中也配置了 `maxSteps`
- 可能导致不一致

**优化建议**：
只在 JSON 中配置 `maxSteps`，从 Markdown 文件头中移除：

```markdown
---
description: 验证事件真实性
mode: subagent
temperature: 0.2
# maxSteps: 15  ← 移除这行，只在 JSON 中配置
hidden: true
---
```

### 4. Task Permission 更精确控制

**当前配置**：
```json
"permission": {
  "task": {
    "*": "allow"  // 允许所有 subagent
  }
}
```

**优化建议**：
使用更精确的控制，提高安全性：

```json
"news-collector": {
  "permission": {
    "task": {
      "event-aggregator": "allow",
      "validator": "allow",
      "timeline-builder": "allow",
      "predictor": "allow",
      "synthesizer": "allow",
      "*": "deny"  // 默认拒绝其他 subagent
    }
  }
}
```

### 5. Temperature 优化

**当前配置**：
- event-aggregator: 0.1
- validator: 0.2
- timeline-builder: 0.2
- predictor: 0.3
- synthesizer: 0.1

**文档建议**：
- **0.0-0.2**: 非常专注和确定性，适合代码分析和规划
- **0.3-0.5**: 平衡的响应，适合一般开发任务
- **0.6-1.0**: 更有创意和变化，适合头脑风暴和探索

**优化建议**：
当前配置基本合理，但可以考虑：
- `event-aggregator`: 0.1 → 0.2（稍微提高，避免过于固化）
- `validator`: 0.2（保持，需要确定性）
- `timeline-builder`: 0.2（保持，需要确定性）
- `predictor`: 0.3 → 0.4（稍微提高，增强创造性）
- `synthesizer`: 0.1（保持，只需要格式化）

### 6. 工具访问权限优化

**当前配置问题**：
- `event-aggregator` 没有配置工具权限
- 其他 subagent 都有 `web-browser_*: true`

**优化建议**：
```json
"event-aggregator": {
  "tools": {
    "write": false,
    "edit": false,
    "bash": false,
    "read": true  // 允许读取文件
    // 不需要 MCP 工具
  }
}
```

### 7. Description 字段

**文档说明**：
> This is a **required** config option.

**当前配置**：
所有 agent 都有 description ✅

**优化建议**：
确保描述清晰简洁，说明：
1. Agent 的主要功能
2. 何时使用
3. 与其他 agent 的区别

```json
{
  "news-collector": {
    "description": "协调新闻收集、验证、分析并生成报告的主agent（S级功能）"
  },
  "validator": {
    "description": "验证事件真实性 - 通过多轮搜索交叉验证（主动探索型，S级核心）"
  }
}
```

---

## 优化后的完整配置

### opencode.json（优化版）

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "web_browser": {
      "type": "local",
      "command": [".venv/Scripts/python.exe", "-m", "mcp_server.web_browser.main"],
      "enabled": true
    }
  },
  "agent": {
    "news-collector": {
      "mode": "primary",
      "description": "协调新闻收集、验证、分析并生成报告的主agent（S级功能）",
      "model": "anthropic/claude-sonnet-4-20250514",
      "temperature": 0.3,
      "prompt": "{file:./prompts/news-collector.txt}",
      "tools": {
        "write": true,
        "edit": true,
        "bash": true,
        "webfetch": false,
        "read": true,
        "grep": true,
        "web-browser_*": true
      },
      "permission": {
        "bash": {
          "python *": "allow",
          "cd *": "allow",
          "ls": "allow",
          "mkdir *": "allow"
        },
        "task": {
          "event-aggregator": "allow",
          "validator": "allow",
          "timeline-builder": "allow",
          "predictor": "allow",
          "synthesizer": "allow",
          "*": "deny"
        }
      }
    },
    "event-aggregator": {
      "mode": "subagent",
      "description": "将多条新闻聚合为事件（识别相似度、生成统一标题和摘要）",
      "model": "anthropic/claude-haiku-4-20250514",
      "prompt": "{file:.opencode/agents/event-aggregator.md}",
      "hidden": true,
      "temperature": 0.2,
      "maxSteps": 5,
      "tools": {
        "write": false,
        "edit": false,
        "bash": false,
        "read": true
      }
    },
    "validator": {
      "mode": "subagent",
      "description": "验证事件真实性 - 通过多轮搜索交叉验证（主动探索型，S级核心）",
      "model": "anthropic/claude-sonnet-4-20250514",
      "prompt": "{file:.opencode/agents/validator.md}",
      "hidden": true,
      "temperature": 0.2,
      "maxSteps": 8,
      "tools": {
        "write": false,
        "edit": false,
        "bash": false,
        "web-browser_*": true
      }
    },
    "timeline-builder": {
      "mode": "subagent",
      "description": "构建事件时间轴 - 主动搜索填补缺口（主动探索型，S级核心）",
      "model": "anthropic/claude-sonnet-4-20250514",
      "prompt": "{file:.opencode/agents/timeline-builder.md}",
      "hidden": true,
      "temperature": 0.2,
      "maxSteps": 10,
      "tools": {
        "write": false,
        "edit": false,
        "bash": false,
        "web-browser_*": true
      }
    },
    "predictor": {
      "mode": "subagent",
      "description": "预测事件发展趋势 - 多情景预测（主动探索型，S级核心）",
      "model": "anthropic/claude-sonnet-4-20250514",
      "prompt": "{file:.opencode/agents/predictor.md}",
      "hidden": true,
      "temperature": 0.4,
      "maxSteps": 8,
      "tools": {
        "write": false,
        "edit": false,
        "bash": false,
        "web-browser_*": true
      }
    },
    "synthesizer": {
      "mode": "subagent",
      "description": "生成最终结构化报告（按分类组织、生成索引）",
      "model": "anthropic/claude-haiku-4-20250514",
      "prompt": "{file:.opencode/agents/synthesizer.md}",
      "hidden": true,
      "temperature": 0.1,
      "tools": {
        "write": true,
        "edit": true,
        "bash": true,
        "read": true
      },
      "permission": {
        "bash": {
          "mkdir *": "allow"
        }
      }
    }
  }
}
```

---

## 关键优化点总结

| 优化项 | 当前配置 | 优化配置 | 预期效果 |
|-------|---------|---------|---------|
| **MCP 工具通配符** | `web-browser*` | `web-browser_*` | 确保工具可访问 |
| **Model 配置** | 未配置 | 为每个 agent 明确配置 | 节省 30-50% 成本 |
| **Task Permission** | `*: allow` | 精确列出允许的 agent | 提高安全性 |
| **Temperature** | 部分偏低 | 微调至最优值 | 平衡确定性和创造性 |
| **MaxSteps** | JSON 和 Markdown 重复 | 只在 JSON 中配置 | 避免混淆 |
| **Description** | 已配置 | 优化描述内容 | 更清晰的理解 |

---

## 下一步行动

### 立即修复（高优先级）
1. ✅ 修改 MCP 工具通配符为 `web-browser_*`
2. ✅ 为 agent 配置 model（使用 Haiku 节省成本）
3. ✅ 优化 task permission（精确控制）

### 可选优化（中优先级）
4. 微调 temperature 值
5. 优化 description 内容
6. 从 Markdown 文件中移除 maxSteps

### 验证步骤
1. 运行 `python verify_config.py` 确保配置正确
2. 测试 agent 是否能正确调用 MCP 工具
3. 对比优化前后的 API 成本

---

**文档版本**: v1.0
**最后更新**: 2026-01-29
**状态**: 已完成分析，待应用优化
