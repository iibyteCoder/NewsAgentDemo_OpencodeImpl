"""
测试 trafilatura 文章内容提取 - 多场景测试

测试多个不同来源的新闻文章，验证提取效果

用法:
    python test_trafilatura_extractor.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_server.web_browser.tools.search_tools import fetch_article_content


# ========== 测试用例 ==========

TEST_CASES = [
    {
        "name": "搜狐-体育新闻",
        "url": "https://www.sohu.com/a/971359832_122219432",
        "category": "体育",
        "expected_images": True,
    },
    {
        "name": "腾讯-科技新闻",
        "url": "https://new.qq.com/rain/a/20250109A03DFT00",
        "category": "科技",
        "expected_images": True,
    },
    {
        "name": "网易-财经新闻",
        "url": "https://www.163.com/dy/article/JM2KE5CN0537B9K9.html",
        "category": "财经",
        "expected_images": True,
    },
    {
        "name": "新浪-娱乐新闻",
        "url": "https://ent.sina.com.cn/s/m/2025-01-14/doc-incimrvz0566031.d.html",
        "category": "娱乐",
        "expected_images": True,
    },
    {
        "name": "今日头条-综合",
        "url": "https://www.toutiao.com/article/7323456789012345678/",
        "category": "综合",
        "expected_images": False,  # 可能无图片
    },
]


# ========== 测试函数 ==========


async def test_single_article(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """测试单篇文章提取

    Args:
        test_case: 测试用例字典

    Returns:
        测试结果字典
    """
    name = test_case["name"]
    url = test_case["url"]
    category = test_case["category"]

    print(f"\n{'=' * 70}")
    print(f"测试: {name} ({category})")
    print(f"{'=' * 70}")
    print(f"URL: {url}")
    print("-" * 70)

    result = {
        "name": name,
        "url": url,
        "category": category,
        "success": False,
        "title": "",
        "content_length": 0,
        "image_count": 0,
        "images": [],
        "status": "",
        "error": "",
    }

    try:
        # 提取文章内容
        result_json = await fetch_article_content(url, include_images=True)
        data = json.loads(result_json)

        # 提取信息
        title = data.get("title", "")
        content = data.get("content", "")
        content_length = data.get("content_length", 0)
        status = data.get("status", {})
        images = data.get("images", [])
        image_count = data.get("image_count", 0)

        # 更新结果
        result["success"] = True
        result["title"] = title
        result["content_length"] = content_length
        result["image_count"] = image_count
        result["images"] = images
        result["status"] = status.get("status", "unknown")

        # 显示结果
        print(f"\n[成功] 提取完成!")
        print(f"  标题: {title[:60]}...")
        print(f"  内容长度: {content_length} 字符")
        print(f"  图片数量: {image_count}")
        print(f"  页面状态: {status.get('status', 'unknown')}")

        # 显示图片
        if images:
            print(f"\n  图片列表 (前5张):")
            for img in images[:5]:
                img_url = img.get("url", "")
                # 简短显示URL
                short_url = img_url[:70] + "..." if len(img_url) > 70 else img_url
                print(f"    {img.get('index')}. {short_url}")
            if len(images) > 5:
                print(f"    ... 还有 {len(images) - 5} 张图片")

        # 内容预览
        if content:
            preview = content[:300].replace("\n", " ")
            print(f"\n  内容预览: {preview}...")

    except Exception as e:
        result["error"] = str(e)
        print(f"\n[失败] 提取失败: {e}")

    return result


async def test_multiple_articles(test_cases: List[Dict[str, Any]], save_results: bool = True):
    """批量测试多篇文章

    Args:
        test_cases: 测试用例列表
        save_results: 是否保存结果到文件
    """
    print("\n" + "=" * 70)
    print("批量测试 - trafilatura 文章内容提取")
    print("=" * 70)
    print(f"\n将测试 {len(test_cases)} 个新闻URL\n")

    all_results = []

    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n[{idx}/{len(test_cases)}] ", end="")
        result = await test_single_article(test_case)
        all_results.append(result)

        # 短暂延迟，避免请求过快
        if idx < len(test_cases):
            print("\n  等待 2 秒...")
            await asyncio.sleep(2)

    # 汇总统计
    print_results_summary(all_results)

    # 保存结果
    if save_results:
        save_test_results(all_results)


def print_results_summary(results: List[Dict[str, Any]]):
    """打印测试结果汇总

    Args:
        results: 测试结果列表
    """
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    # 统计
    total = len(results)
    success_count = sum(1 for r in results if r["success"])
    failed_count = total - success_count

    total_content = sum(r["content_length"] for r in results if r["success"])
    total_images = sum(r["image_count"] for r in results if r["success"])

    avg_content = total_content / success_count if success_count > 0 else 0
    avg_images = total_images / success_count if success_count > 0 else 0

    print(f"\n统计信息:")
    print(f"  总测试数: {total}")
    print(f"  成功: {success_count} | 失败: {failed_count}")
    print(f"  成功率: {success_count / total * 100:.1f}%")
    print(f"\n内容提取:")
    print(f"  总内容长度: {total_content:,} 字符")
    print(f"  平均长度: {avg_content:.0f} 字符/篇")
    print(f"\n图片提取:")
    print(f"  总图片数: {total_images}")
    print(f"  平均图片: {avg_images:.1f} 张/篇")

    # 详细结果
    print(f"\n详细结果:")
    print("-" * 70)
    for r in results:
        status_symbol = "[OK]" if r["success"] else "[FAIL]"
        print(f"{status_symbol} {r['name']} ({r['category']})")
        if r["success"]:
            print(
                f"      内容: {r['content_length']} 字符 | 图片: {r['image_count']} 张 | 状态: {r['status']}"
            )
        else:
            print(f"      错误: {r['error']}")
        print("-" * 70)


def save_test_results(results: List[Dict[str, Any]]):
    """保存测试结果到文件

    Args:
        results: 测试结果列表
    """
    output_dir = Path("./test_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存JSON格式
    json_file = output_dir / "trafilatura_test_results.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 保存Markdown格式
    md_file = output_dir / "trafilatura_test_results.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# trafilatura 文章提取测试结果\n\n")
        f.write(f"测试时间: {Path(__file__).stat().st_mtime}\n\n")
        f.write("## 测试统计\n\n")
        f.write(f"- 总测试数: {len(results)}\n")
        f.write(f"- 成功: {sum(1 for r in results if r['success'])}\n")
        f.write(f"- 失败: {sum(1 for r in results if not r['success'])}\n\n")

        f.write("## 详细结果\n\n")
        for r in results:
            f.write(f"### {r['name']}\n\n")
            f.write(f"- **分类**: {r['category']}\n")
            f.write(f"- **URL**: {r['url']}\n")
            f.write(f"- **状态**: {'成功' if r['success'] else '失败'}\n")
            if r['success']:
                f.write(f"- **标题**: {r['title']}\n")
                f.write(f"- **内容长度**: {r['content_length']} 字符\n")
                f.write(f"- **图片数量**: {r['image_count']}\n")
                f.write(f"- **页面状态**: {r['status']}\n")
            else:
                f.write(f"- **错误**: {r['error']}\n")
            f.write("\n")

    print(f"\n[保存] 结果已保存到:")
    print(f"  JSON: {json_file.absolute()}")
    print(f"  Markdown: {md_file.absolute()}")


async def main():
    """主运行函数"""
    print("\n[开始] trafilatura 文章提取多场景测试")

    try:
        await test_multiple_articles(TEST_CASES, save_results=True)
        print("\n[完成] 所有测试完成!")

    except KeyboardInterrupt:
        print("\n\n[中断] 用户取消测试")
    except Exception as e:
        print(f"\n[错误] 测试出错: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # 清理资源
        from mcp_server.web_browser.core.browser_pool import get_browser_pool

        browser_pool = get_browser_pool()
        await browser_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
