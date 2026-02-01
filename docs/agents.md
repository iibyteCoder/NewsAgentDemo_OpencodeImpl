# Agents 开发规范

本文档记录项目中涉及 AI 辅助开发时的规范、要求和最佳实践。

## 目录

- [测试文件编写规范](#测试文件编写规范)
- [代码风格规范](#代码风格规范)
- [AI 辅助开发指南](#ai-辅助开发指南)

---

## 测试文件编写规范

### 文件位置

测试文件应放置在 `scripts/` 目录下，命名格式：`test_<功能描述>.py`

### 文件结构要求

#### 1. 入口点 (`if __name__ == "__main__"` 部分)

入口点应保持**简洁**，仅负责：
- 配置参数（通过顶部常量定义）
- 调用主函数
- 异常处理和资源清理

```python
if __name__ == "__main__":
    async def main():
        """主函数 - 仅负责配置和调用"""
        try:
            # 运行测试套件
            await run_test_suite(TEST_URLS, save_result=True)
        except Exception as e:
            # 处理异常
            pass
        finally:
            # 清理资源
            await cleanup()

    asyncio.run(main())
```

#### 2. 具体实现（外部函数）

所有业务逻辑、测试逻辑应放在入口点**外部**的函数中：

```python
# ==================== 配置项 ====================
TEST_URLS = [...]  # 配置参数

# ==================== 实现函数 ====================
async def test_single_url(url: str, title: str) -> Dict:
    """测试单个URL"""

async def run_test_suite(test_urls: List[Tuple[str, str]], save_result: bool):
    """运行完整的测试套件"""

def print_test_summary(results: List[Dict]):
    """打印测试汇总报告"""

async def cleanup():
    """清理资源"""
```

### 代码组织

#### 配置项区域

在文件顶部使用清晰的分隔符标记配置项：

```python
# ==================== 配置项 ====================

# 测试URL列表（从output目录的实际报告中提取）
TEST_URLS: List[Tuple[str, str]] = [
    ("https://example.com/news1", "新闻标题1"),
    ("https://example.com/news2", "新闻标题2"),
]

# 保存结果的文件路径
OUTPUT_FILE = Path("./test_data/test_results.json")

# 控制台显示的URL最大长度
MAX_URL_DISPLAY_LENGTH = 70
```

#### 实现函数区域

使用分隔符标记不同类型的函数：

```python
# ==================== 测试函数 ====================
async def test_single_url(...) -> Dict:
    """测试单个URL的图片提取功能"""

# ==================== 工具函数 ====================
def _is_valid_content_image(img: Dict) -> bool:
    """判断图片是否可能是正文图片"""

# ==================== 入口点 ====================
if __name__ == "__main__":
    ...
```

### 测试用例提取

测试用例应从 `output/` 目录的实际报告中提取，确保测试的真实性和有效性。

提取步骤：
1. 查看 `output/**/事件报告.md` 文件
2. 从"新闻来源"部分提取真实 URL
3. 整理成 `(url, title)` 元组格式
4. 分类组织（科技、体育、财经等）

### 输出格式

#### 控制台输出

- 使用清晰的分隔线和图标标识不同部分
- 显示测试进度：`[1/6]`
- 使用状态图标：`✅` 成功、`❌` 失败、`⚠️` 警告
- 截断过长的 URL 以保持可读性

#### 文件输出

- 测试结果保存为 JSON 格式
- 路径：`scripts/test_data/<测试名称>_results.json`
- 包含完整的图片信息和元数据

### 资源管理

必须在 `finally` 块中清理资源：

```python
async def cleanup():
    """清理资源"""
    try:
        from mcp_server.web_browser.core.browser_pool import get_browser_pool
        browser_pool = get_browser_pool()
        await browser_pool.close()
    except Exception as e:
        logger.error(f"清理浏览器资源时出错: {e}")
```

### 类型注解

所有函数必须添加类型注解：

```python
async def test_single_url(url: str, title: str) -> Dict:
    """测试单个URL

    Args:
        url: 新闻URL
        title: 新闻标题

    Returns:
        测试结果字典
    """
```

### 文档字符串

- 所有公开函数必须有文档字符串
- 使用 Google 风格的文档字符串
- 包含：功能描述、参数说明、返回值说明

---

## 代码风格规范

### 常量定义

使用全大写命名常量：

```python
DATA_IMAGE_PREFIX = "data:image"
MIN_IMAGE_URL_LENGTH = 20
UNWANTED_IMAGE_KEYWORDS = [...]
```

### 辅助函数

将重复逻辑提取为独立的辅助函数：

```python
def _is_valid_image_url(url: str) -> bool:
    """检查图片URL是否有效"""
    ...

def _normalize_image_url(url: str, base_url: str) -> str:
    """规范化图片URL（处理相对路径）"""
    ...

def _create_image_dict(index: int, url: str, ...) -> dict:
    """创建图片信息字典"""
    ...
```

### 错误处理

- 使用具体的异常捕获
- 提供有意义的错误信息
- 记录错误日志

```python
try:
    result = await fetch_article_content(url)
except Exception as e:
    logger.error(f"获取文章内容失败: {e}")
    return {...}
```

---

## AI 辅助开发指南

### 与 AI 协作的最佳实践

#### 1. 明确需求

在向 AI 提出需求时，应包含：
- **目标**：要实现什么功能
- **背景**：为什么需要这个功能
- **约束**：有什么限制条件
- **示例**：提供期望的输入输出示例

#### 2. 代码审查

AI 生成的代码需要人工审查：
- 检查安全性（SQL 注入、XSS 等）
- 验证逻辑正确性
- 确保符合项目规范
- 添加必要的注释和文档

#### 3. 增量开发

- 优先实现核心功能
- 逐步添加辅助功能
- 及时测试和验证

#### 4. 测试驱动

- 先编写测试用例
- 确保测试覆盖关键路径
- 验证边界条件

---

## 示例：完整的测试文件模板

```python
"""
测试功能描述

测试目标：
1. 目标一
2. 目标二

用法：
- 在 VS Code 中右键 -> "在终端中运行 Python 文件" 或按 F5 直接调试
- 点击右上角的运行按钮
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from module import function_to_test


# ==================== 配置项 ====================

TEST_URLS: List[Tuple[str, str]] = [
    ("https://example.com/test1", "测试用例1"),
    ("https://example.com/test2", "测试用例2"),
]

OUTPUT_FILE = Path("./test_data/test_results.json")


# ==================== 测试函数 ====================

async def test_single_case(url: str, title: str) -> Dict:
    """测试单个用例

    Args:
        url: 测试URL
        title: 测试标题

    Returns:
        测试结果字典
    """
    result = await function_to_test(url)
    return {...}


async def run_test_suite(test_cases: List[Tuple[str, str]], save_result: bool = True):
    """运行完整的测试套件

    Args:
        test_cases: 测试用例列表
        save_result: 是否保存结果
    """
    all_results = []
    for url, title in test_cases:
        result = await test_single_case(url, title)
        all_results.append(result)

    if save_result:
        save_results(all_results)

    return all_results


# ==================== 工具函数 ====================

def print_summary(results: List[Dict]):
    """打印测试汇总"""
    ...


def save_results(results: List[Dict]):
    """保存测试结果到文件"""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


async def cleanup():
    """清理资源"""
    ...


# ==================== 入口点 ====================

if __name__ == "__main__":
    async def main():
        """主函数 - 仅负责配置和调用"""
        try:
            await run_test_suite(TEST_URLS, save_result=True)
        except Exception as e:
            print(f"测试失败: {e}")
        finally:
            await cleanup()

    asyncio.run(main())
```

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-02-01 | 1.0 | 初始版本，记录测试文件编写规范 |
