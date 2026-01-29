"""Simple async downloader test"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.downloader.core.downloader import Downloader


async def main():
    """Test async download functionality"""
    print("Testing async downloader (without singleton)...")

    test_url = "https://httpbin.org/image/png"
    save_dir = Path("test_downloads")

    try:
        # Use context manager to create downloader instance
        async with Downloader() as downloader:
            print("1. Downloader instance created successfully")

            # Download single file
            print(f"2. Downloading: {test_url}")
            result = await downloader.download(test_url, save_dir)

            if result["success"]:
                print(f"3. Download successful: {result['filepath']}")
                print(f"   File size: {result['size']} bytes")

                # Cleanup
                filepath = Path(result['filepath'])
                if filepath.exists():
                    filepath.unlink()
                if save_dir.exists():
                    save_dir.rmdir()
                print("4. Test files cleaned up")
            else:
                print(f"3. Download failed: {result['message']}")
                return False

        print("\nAll async features working correctly!")
        print("Design improvements:")
        print("  - No singleton pattern (direct instance creation)")
        print("  - Context manager for automatic resource cleanup")
        print("  - Fully async with aiofiles")
        return True

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
