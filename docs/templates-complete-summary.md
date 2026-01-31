# 模板系统完成总结

## 完成情况

所有6个报告部分现在都有对应的模板文件。

## 模板文件列表

### 1. 事件摘要模板 ✅

**文件**：`templates/sections/summary-section-template.md`

**对应的报告生成器**：`prompts/summary-report-generator.md`

**模板定义**：
- 长度要求：150-200字
- 结构：事件概述 → 核心信息 → 重要意义
- 要素：What、When、Who、Where、Why、How

**占位符**：
- `{event_summary}` - 完整的事件摘要内容

---

### 2. 新闻来源模板 ✅

**文件**：`templates/sections/news-section-template.md`

**对应的报告生成器**：`prompts/news-report-generator.md`

**模板定义**：
- 分类：最新报道、当日热点、权威分析、其他媒体、历史参考
- 格式：标题、链接、来源、时间、摘要
- 排序：按发布时间倒序

**占位符**：
- `{latest_news}` - 最新报道内容列表
- `{hot_news}` - 当日热点报道内容列表
- `{authoritative_news}` - 权威分析报道内容列表
- `{other_media_news}` - 其他媒体报道内容列表
- `{historical_news}` - 历史参考报道内容列表
- `{total_news_count}` - 新闻总数
- `{main_sources}` - 主要来源列表
- `{time_range}` - 时间范围描述
- `{content_types}` - 涵盖内容类型描述

---

### 3. 真实性验证模板 ✅

**文件**：`templates/sections/validation-section-template.md`

**对应的报告生成器**：`prompts/validation-report-generator.md`

**模板定义**：
- 可信度评分
- 证据链验证（每个步骤包含具体来源）
- 综合分析（事实一致性、时间序列、多维度验证等）

**占位符**：
- `{credibility_score}` - 可信度评分（0-100）
- `{confidence_level}` - 置信度（高/中/低）
- `{evidence_chain_items}` - 证据链内容
- `{fact_consistency_indicator}` - 事实一致性指示器
- `{fact_consistency_content}` - 事实一致性内容
- `{time_sequence_indicator}` - 时间序列指示器
- `{time_sequence_content}` - 时间序列内容
- `{multi_dimension_indicator}` - 多维度指示器
- `{multi_dimension_content}` - 多维度内容
- `{logic_consistency_indicator}` - 逻辑一致性指示器
- `{logic_consistency_content}` - 逻辑一致性内容
- `{information_completeness_indicator}` - 信息完整性指示器
- `{information_completeness_content}` - 信息完整性内容
- `{overall_conclusion}` - 综合判断
- `{detailed_conclusion}` - 详细结论
- `{validation_time}` - 验证时间
- `{data_points_count}` - 数据点数量
- `{media_sources_count}` - 来源媒体数量

---

### 4. 事件时间轴模板 ✅

**文件**：`templates/sections/timeline-section-template.md`

**对应的报告生成器**：`prompts/timeline-report-generator.md`

**模板定义**：
- 发展脉络
- 关键时间节点（每个节点包含来源）
- 影响与后果

**占位符**：
- `{development_path}` - 事件发展脉络的完整叙述
- `{timeline_items}` - 时间轴项目列表
- `{impacts_and_consequences}` - 影响与后果
- `{timeline_build_time}` - 时间轴构建时间

---

### 5. 趋势预测模板 ✅

**文件**：`templates/sections/prediction-section-template.md`

**对应的报告生成器**：`prompts/prediction-report-generator.md`

**模板定义**：
- 情景分析（乐观、基准、悲观）
- 关键影响因素
- 结论与建议

**占位符**：
- `{scenarios_content}` - 情景内容
- `{key_factors_content}` - 关键因素内容
- `{core_conclusion}` - 核心结论
- `{recommendations}` - 建议/展望
- `{prediction_time}` - 预测生成时间
- `{sources_count}` - 来源数量
- `{expert_count}` - 专家观点数量
- `{case_count}` - 历史案例数量

---

### 6. 相关图片模板 ✅

**文件**：`templates/sections/images-section-template.md`

**对应的报告生成器**：`prompts/images-report-generator.md`

**模板定义**：
- 图片总览
- 按新闻来源分类
- 下载情况说明

**占位符**：
- `{total_images_count}` - 原始图片总数
- `{downloaded_count}` - 成功下载数量
- `{failed_count}` - 下载失败数量
- `{event_folder}` - 事件文件夹名称
- `{images_by_source}` - 按来源分组的图片
- `{download_status_description}` - 下载状态描述
- `{photo_count}` - 纪实类图片数量
- `{chart_count}` - 数据图表类图片数量
- `{person_count}` - 人物照片数量
- `{update_time}` - 最后更新时间

---

## 模板系统特点

### 1. 统一的占位符格式

所有占位符都使用 `{placeholder_name}` 格式，便于识别和替换。

### 2. 完整的文档说明

每个模板文件都包含：
- 模板格式定义
- 占位符说明
- 使用示例
- 注意事项

### 3. 强制性引用

所有报告生成器都明确要求：
```markdown
**⚠️ 必须遵循模板**：

参考模板文件：`templates/sections/xxx-section-template.md`
```

### 4. 通用性设计

模板设计考虑了各种类型的新闻：
- 金融类新闻
- 科技类新闻
- 体育类新闻
- 政治类新闻
- 社会类新闻

---

## 文件结构总览

```
templates/
└── sections/
    ├── summary-section-template.md       ✅ 事件摘要
    ├── news-section-template.md          ✅ 新闻来源
    ├── validation-section-template.md    ✅ 真实性验证
    ├── timeline-section-template.md      ✅ 事件时间轴
    ├── prediction-section-template.md    ✅ 趋势预测
    └── images-section-template.md        ✅ 相关图片
```

---

## 报告生成器与模板对应关系

| 报告生成器 | 对应模板 | 模板文件 |
|-----------|---------|---------|
| summary-report-generator | ⭐ 事件摘要 | summary-section-template.md |
| news-report-generator | ⭐ 新闻来源 | news-section-template.md |
| validation-report-generator | ⭐ 真实性验证 | validation-section-template.md |
| timeline-report-generator | ⭐ 事件时间轴 | timeline-section-template.md |
| prediction-report-generator | ⭐ 趋势预测 | prediction-section-template.md |
| images-report-generator | ⭐ 相关图片 | images-section-template.md |

---

## 使用方式

### 报告生成器使用模板的步骤

1. **读取模板文件** - 了解模板格式要求
2. **从数据库读取数据** - 获取该部分的数据
3. **填充占位符** - 使用实际数据替换占位符
4. **生成Markdown内容** - 按照模板格式生成
5. **写入文件** - 保存到.parts文件夹

### 示例代码（伪代码）

```python
# 1. 读取模板
template = read_file("templates/sections/validation-section-template.md")

# 2. 读取数据
data = news_storage_get_report_section(event_name, session_id, "validation")

# 3. 填充占位符
content = template.replace("{credibility_score}", data["credibility_score"])
content = content.replace("{confidence_level}", data["confidence_level"])
content = content.replace("{evidence_chain_items}", format_evidence_chain(data["evidence_chain"]))
# ... 其他占位符

# 4. 写入文件
write_file(output_file, content)
```

---

## 模板系统的优势

1. **统一性** - 所有报告部分使用统一的格式
2. **可维护性** - 修改模板即可改变所有报告的格式
3. **强制性** - 报告生成器必须遵循模板格式
4. **通用性** - 模板设计考虑了各种类型的新闻
5. **完整性** - 每个模板都包含完整的文档说明

---

*模板系统完成时间：2026-01-30*
