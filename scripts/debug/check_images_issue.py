#!/usr/bin/env python3
"""检查图片提取和保存流程"""

import asyncio
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

async def check_fetch_images():
    """测试 fetch_article_content_tool 是否返回图片"""
    from mcp_server.web_browser.tools.search_tools import fetch_article_content

    # 使用一个典型的新闻URL
    test_url = "https://baijiahao.baidu.com/s?id=1855021253209913694"

    print("\n" + "="*60)
    print(f"测试提取图片: {test_url}")
    print("="*60 + "\n")

    result_str = await fetch_article_content(test_url, include_images=True)
    result = json.loads(result_str)

    print(f"标题: {result.get('title', '')[:100]}...")
    print(f"内容长度: {result.get('content_length', 0)} 字符")
    print(f"图片数量: {result.get('image_count', 0)}")
    print(f"图片列表: {json.dumps(result.get('images', []), indent=2, ensure_ascii=False)}")

    return result


async def check_database_save():
    """测试保存到数据库时是否包含图片"""
    from mcp_server.news_storage.tools.storage_tools import save_news_tool

    print("\n" + "="*60)
    print("测试保存新闻（带图片）")
    print("="*60 + "\n")

    # 准备测试数据
    test_image_urls = json.dumps([
        "https://example.com/image1.jpg",
        "https://example.com/image2.png"
    ])

    print("准备保存的新闻数据:")
    print("  - 标题: 测试新闻标题")
    print("  - URL: https://test.example.com/test-image-002")
    print(f"  - 网络图片URL参数: {test_image_urls}")

    result_str = await save_news_tool(
        title="测试新闻标题",
        url="https://test.example.com/test-image-002",
        summary="测试摘要",
        source="测试来源",
        content="测试内容",
        image_urls=test_image_urls
    )

    result = json.loads(result_str)
    print(f"\n保存结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

    # 验证保存后的数据
    from mcp_server.news_storage.tools.storage_tools import get_news_by_url_tool
    saved_news_str = await get_news_by_url_tool("https://test.example.com/test-image-002")
    saved_news = json.loads(saved_news_str)

    if saved_news.get("found"):
        news_data = saved_news["data"]
        print("\n验证数据库中的数据:")
        print(f"  - 标题: {news_data.get('title')}")
        print(f"  - 网络图片URL字段: {news_data.get('image_urls')}")
        print(f"  - 本地图片路径字段: {news_data.get('local_image_paths')}")
        print(f"  - 图片是否保存: {'✅ 成功' if news_data.get('image_urls') != '[]' else '❌ 失败'}")
    else:
        print("\n❌ 未找到保存的新闻")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("图片保存流程诊断")
    print("="*60)

    # 1. 测试图片提取
    await check_fetch_images()

    # 2. 测试数据库保存
    await check_database_save()

    print("\n" + "="*60)
    print("诊断完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
