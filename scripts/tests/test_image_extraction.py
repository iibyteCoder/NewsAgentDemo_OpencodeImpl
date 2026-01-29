"""
测试文章内容获取与图片链接提取功能

测试 fetch_article_content 函数：
- 访问新闻网页
- 提取文章内容
- 提取图片链接

用法：
1. 在 VS Code 中右键 -> "在终端中运行 Python 文件" 或按 F5 直接调试
2. 或者点击右上角的运行按钮

来源：2025年国内国际十大体育新闻评选事件
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_server.web_browser.tools.search_tools import fetch_article_content


# ==================== 测试函数 ====================

async def test_fetch_article_with_images(urls, save_result=True):
    """测试从新闻URL获取文章内容和图片链接

    Args:
        urls: URL列表，格式为 [(url, title), ...]
        save_result: 是否保存结果到文件
    """
    print("\n" + "=" * 60)
    print("测试 fetch_article_content - 获取文章内容和图片链接")
    print("=" * 60)
    print(f"\n将测试 {len(urls)} 个新闻URL")

    all_results = []

    for idx, (url, title) in enumerate(urls, 1):
        print(f"\n[{idx}/{len(urls)}] {title}")
        print(f"URL: {url}")
        print("-" * 60)

        try:
            # 调用 fetch_article_content 获取文章内容和图片链接
            print("  正在获取文章内容...")
            result_json = await fetch_article_content(url, include_images=True)

            # 解析结果
            result = json.loads(result_json)

            # 提取信息
            article_title = result.get('title', '无标题')
            content_length = result.get('content_length', 0)
            images = result.get('images', [])
            image_count = result.get('image_count', len(images))
            status = result.get('status', {})

            print(f"  标题: {article_title}")
            print(f"  正文长度: {content_length} 字符")
            print(f"  页面状态: {status.get('status', 'unknown')}")
            print(f"  图片数量: {image_count}")

            if images:
                print(f"\n  图片链接列表:")
                for i, img in enumerate(images, 1):
                    img_url = img.get('url', 'N/A')
                    alt = img.get('alt', '')
                    # 显示URL，如果太长就截断
                    display_url = img_url if len(img_url) <= 70 else img_url[:67] + "..."
                    alt_text = f" - {alt}" if alt else ""
                    print(f"    {i}. {display_url}{alt_text}")
            else:
                print("  未找到图片")

            all_results.append({
                'title': title,
                'url': url,
                'article_title': article_title,
                'content_length': content_length,
                'image_count': image_count,
                'images': images,
                'status': status,
                'success': True
            })

        except Exception as e:
            print(f"  ✗ 错误: {e}")
            import traceback
            traceback.print_exc()

            all_results.append({
                'title': title,
                'url': url,
                'error': str(e),
                'image_count': 0,
                'images': [],
                'success': False
            })

    # 汇总统计
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    total_pages = len(urls)
    total_images = sum(r.get('image_count', 0) for r in all_results)
    successful_pages = sum(1 for r in all_results if r.get('success'))

    print(f"\n统计信息:")
    print(f"  测试页面数: {total_pages}")
    print(f"  成功获取: {successful_pages}")
    print(f"  总共找到图片链接: {total_images}")

    print(f"\n详细结果:")
    for r in all_results:
        if r.get('success'):
            status = "✓"
            detail = f"找到 {r['image_count']} 个图片链接，正文 {r['content_length']} 字符"
        else:
            status = "✗"
            detail = f"错误 - {r.get('error', '未知错误')}"

        print(f"  {status} {r['title']}")
        print(f"      {detail}")

    # 保存结果到文件
    if save_result:
        save_results_to_file(all_results)

    return all_results


def save_results_to_file(results):
    """保存测试结果到文件"""
    output_file = Path("./test_data/article_fetch_result.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存到: {output_file.absolute()}")


async def main(test_urls):
    """主运行函数"""
    print("\n" + "🚀" * 30)
    print("开始测试 fetch_article_content 功能")
    print("🚀" * 30)

    try:
        # 运行测试
        await test_fetch_article_with_images(test_urls, save_result=True)

        print("\n" + "✅" * 30)
        print("测试完成！")
        print("✅" * 30)

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理资源
        from mcp_server.web_browser.core.browser_pool import get_browser_pool
        browser_pool = get_browser_pool()
        await browser_pool.close()


if __name__ == "__main__":
    # ==================== 配置项 ====================
    # 真实新闻URL（来自体育新闻汇总报告）
    test_urls = [
        ("https://www.sohu.com/a/971359832_122219432", "搜狐-樊振东陈梦退出世排"),
        # ("https://news.qq.com/rain/a/20260109A03DFT00", "腾讯-赵心童斯诺克夺冠"),
        # ("https://news.qq.com/rain/a/20250626A09B5B00", "腾讯-杨瀚森NBA选秀"),
        # ("https://www.sohu.com/a/969024685_122014422", "搜狐-2025国内十大体育新闻"),
        # ("https://www.sohu.com/a/971226352_121106854", "搜狐-2025国际十大体育新闻"),
        # ("https://www.sport.gov.cn/n20001280/n20067662/n20067613/c29329796/content.html", "国家体育总局-十大体育新闻"),
    ]

    asyncio.run(main(test_urls))
