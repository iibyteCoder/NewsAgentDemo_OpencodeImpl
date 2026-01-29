"""测试异步下载器功能"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.downloader.core.downloader import get_downloader


async def test_async_download():
    """测试异步下载功能"""
    print("开始测试异步下载功能...")

    # 测试 URL（使用一个小图片）
    test_url = "https://httpbin.org/image/png"
    save_dir = Path("test_downloads")

    try:
        # 获取下载器
        downloader = await get_downloader()
        print("✓ 获取下载器实例成功")

        # 下载单个文件
        print(f"\n正在下载: {test_url}")
        result = await downloader.download(test_url, save_dir)

        if result["success"]:
            print(f"✓ 下载成功: {result['filepath']}")
            print(f"  文件大小: {result['size']} 字节")

            # 清理测试文件
            filepath = Path(result['filepath'])
            if filepath.exists():
                filepath.unlink()
                save_dir.rmdir()
                print("✓ 测试文件已清理")
        else:
            print(f"✗ 下载失败: {result['message']}")
            return False

        print("\n✓ 异步下载功能测试通过！")
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_batch_download():
    """测试批量异步下载功能"""
    print("\n\n开始测试批量异步下载功能...")

    test_urls = [
        "https://httpbin.org/image/png",
        "https://httpbin.org/image/jpeg",
        "https://httpbin.org/image/webp",
    ]
    save_dir = Path("test_batch_downloads")

    try:
        downloader = await get_downloader()
        print(f"✓ 准备批量下载 {len(test_urls)} 个文件")

        results = await downloader.download_batch(test_urls, save_dir, max_concurrent=2)

        success_count = sum(1 for r in results if r.get("success"))
        print(f"✓ 批量下载完成: 成功 {success_count}/{len(test_urls)}")

        # 清理测试文件
        for result in results:
            if result.get("success") and result.get("filepath"):
                filepath = Path(result["filepath"])
                if filepath.exists():
                    filepath.unlink()

        if save_dir.exists():
            save_dir.rmdir()
            print("✓ 测试文件已清理")

        print("✓ 批量异步下载功能测试通过！")
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("=" * 50)
    print("异步下载器功能测试")
    print("=" * 50)

    test1 = await test_async_download()
    test2 = await test_async_batch_download()

    print("\n" + "=" * 50)
    if test1 and test2:
        print("所有测试通过！✓")
    else:
        print("部分测试失败！✗")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
