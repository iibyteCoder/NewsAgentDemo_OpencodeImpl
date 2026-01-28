"""
手动验证辅助脚本

1. 启动浏览器访问百度
2. 等待用户在浏览器窗口中手动完成验证
3. 验证成功后自动保存 Cookies
4. 后续请求将使用已验证的 Cookies
"""

import asyncio
import time
from mcp_server.baidu_search.browser_pool import get_browser_pool

async def manual_verify():
    """手动验证流程"""
    print("\n" + "="*60)
    print("手动验证流程")
    print("="*60)
    print("\n步骤:")
    print("1. 浏览器将自动打开并访问百度")
    print("2. 请在浏览器窗口中完成百度安全验证")
    print("3. 验证成功后，脚本将自动保存 Cookies")
    print("4. 按回车键继续...\n")

    input("按回车键开始...")

    # 获取浏览器池
    browser_pool = get_browser_pool()

    # 确保浏览器启动
    await browser_pool._ensure_browser()

    # 获取第一个 Context
    context = await browser_pool._get_or_create_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    # 创建页面并访问百度首页
    page = await context.new_page()

    print("\n🌐 正在打开百度首页...")
    print("📋 请在浏览器窗口中完成安全验证")
    print("⏳ 验证完成后，脚本将自动检测并保存 Cookies")
    print("="*60 + "\n")

    try:
        # 访问百度首页
        await page.goto("https://www.baidu.com", timeout=60000)

        # 等待用户验证（最多5分钟）
        print("⏳ 等待验证中（最长5分钟）...")

        # 检查是否还在验证页面
        for i in range(60):
            await asyncio.sleep(5)
            title = await page.title()
            print(f"   检测中... ({i*5}秒) 页面标题: {title}")

            if "验证" not in title and "安全" not in title:
                print("\n✅ 验证成功！检测到正常百度页面")

                # 保存 Cookies
                print("💾 正在保存 Cookies...")
                await browser_pool.save_cookies(context)

                print("✅ Cookies 已保存！后续请求将使用这些 Cookies")

                # 测试一次搜索
                print("\n🧪 测试一次搜索...")
                await page.goto("https://www.baidu.com/s?wd=测试", timeout=30000)
                await asyncio.sleep(2)

                title = await page.title()
                if "百度" in title and "验证" not in title:
                    print("✅ 搜索测试成功！")
                else:
                    print(f"⚠️ 搜索测试可能失败，页面标题: {title}")

                break
            elif i >= 55:
                print("\n⏰ 等待超时，请检查是否验证成功")
                break

    finally:
        await page.close()
        print("\n🔒 完成后，浏览器将保持打开状态")
        print("💡 提示: 如果验证成功，后续的自动化请求应该都能正常工作")
        print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(manual_verify())
