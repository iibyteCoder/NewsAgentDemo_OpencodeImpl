"""
测试 Downloader MCP Server

这个脚本测试下载器的各个功能：
1. 单个文件下载
2. 批量下载
3. 从HTML中提取并下载图片
4. 从网页URL中提取并下载图片
"""

import asyncio
import json
from pathlib import Path

from mcp_server.downloader.core.downloader import get_downloader
from mcp_server.downloader.tools import (
    download_file,
    download_files,
    download_images_from_html,
    download_images_from_url,
)


async def test_single_download():
    """测试单个文件下载"""
    print("\n" + "=" * 60)
    print("测试1: 单个文件下载")
    print("=" * 60)

    # 使用一个公开的测试图片
    test_url = "https://httpbin.org/image/png"

    result = await download_file(test_url, save_path="./test_downloads")

    result_dict = json.loads(result)
    print(f"\n结果: {json.dumps(result_dict, indent=2, ensure_ascii=False)}")

    if result_dict.get("success"):
        print(f"✅ 下载成功: {result_dict['filepath']}")
    else:
        print(f"❌ 下载失败: {result_dict.get('message')}")


async def test_batch_download():
    """测试批量下载"""
    print("\n" + "=" * 60)
    print("测试2: 批量下载")
    print("=" * 60)

    # 测试多个URL
    test_urls = [
        "https://httpbin.org/image/png",
        "https://httpbin.org/image/jpeg",
        "https://httpbin.org/image/svg",
    ]

    result = await download_files(test_urls, save_path="./test_downloads")

    result_dict = json.loads(result)
    print(f"\n结果: {json.dumps(result_dict, indent=2, ensure_ascii=False)}")

    print(f"\n总计: {result_dict['total']}")
    print(f"成功: {result_dict['success']}")
    print(f"失败: {result_dict['failed']}")


async def test_extract_from_html():
    """测试从HTML中提取并下载图片"""
    print("\n" + "=" * 60)
    print("测试3: 从HTML中提取并下载图片")
    print("=" * 60)

    # 测试HTML内容
    test_html = """
    <html>
    <body>
        <h1>测试页面</h1>
        <img src="https://httpbin.org/image/png" alt="测试图片1">
        <img src="https://httpbin.org/image/jpeg" alt="测试图片2">
        <div style="background-image: url('https://httpbin.org/image/svg')"></div>
    </body>
    </html>
    """

    result = await download_images_from_html(
        test_html, save_path="./test_downloads/images"
    )

    result_dict = json.loads(result)
    print(f"\n结果: {json.dumps(result_dict, indent=2, ensure_ascii=False)}")

    print(f"\n找到图片: {result_dict['total']}")
    print(f"成功下载: {result_dict['success']}")
    print(f"下载失败: {result_dict['failed']}")


async def test_extract_from_url():
    """测试从网页URL中提取并下载图片"""
    print("\n" + "=" * 60)
    print("测试4: 从网页URL中提取并下载图片")
    print("=" * 60)

    # 使用一个简单的测试网页
    test_url = "https://httpbin.org/html"

    result = await download_images_from_url(
        test_url, save_path="./test_downloads/from_url"
    )

    result_dict = json.loads(result)
    print(f"\n结果: {json.dumps(result_dict, indent=2, ensure_ascii=False)}")

    print(f"\n找到图片: {result_dict.get('total', 0)}")
    print(f"成功下载: {result_dict.get('success', 0)}")
    print(f"下载失败: {result_dict.get('failed', 0)}")


async def main():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("开始测试 Downloader MCP Server")
    print("🚀" * 30)

    # 创建测试目录
    test_dir = Path("./test_downloads")
    test_dir.mkdir(exist_ok=True)

    try:
        # 运行测试
        await test_single_download()
        await test_batch_download()
        await test_extract_from_html()
        await test_extract_from_url()

        print("\n" + "✅" * 30)
        print("所有测试完成！")
        print("✅" * 30)

    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # 清理资源
        downloader = get_downloader()
        await downloader.close()


if __name__ == "__main__":
    asyncio.run(main())
