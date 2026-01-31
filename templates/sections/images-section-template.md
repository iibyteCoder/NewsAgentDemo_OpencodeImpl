# 相关图片模板

## 模板格式

## 图片总览

- **图片总数**: {total_count}张
- **成功下载**: {downloaded_count}张
- **下载失败**: {failed_count}张
- **图片存储路径**: `./{event_folder}/`

---

## 按新闻来源分类

{images_by_source}

---

_图片最后更新时间：{update_time}_

## 说明

### 单个来源图片格式

```markdown
### {sequence}. [{title}]({url})

| 缩略图 | 图片信息 |
|--------|----------|
| ![图片](./{event_folder}/{filename}) | **文件名**: {filename}<br>**文件大小**: {size}<br>**来源新闻**: [{title}]({url})<br>**说明**: {description} |
```

### 占位符说明

- `{total_count}` - 图片总数
- `{downloaded_count}` - 成功下载的图片数量
- `{failed_count}` - 下载失败的图片数量
- `{event_folder}` - 事件文件夹名称
- `{images_by_source}` - 按来源新闻分组的图片内容
- `{update_time}` - 最后更新时间

### 单个图片字段

- `{sequence}` - 序号
- `{title}` - 新闻标题
- `{url}` - 新闻链接
- `{filename}` - 图片文件名
- `{size}` - 文件大小
- `{description}` - 图片说明
