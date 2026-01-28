"""
分析各搜索引擎的稳定HTML结构
"""

import sys
import io
from bs4 import BeautifulSoup

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def analyze_structure(html_file, engine_name):
    """分析引擎的稳定结构"""
    print(f"\n{'='*60}")
    print(f"{engine_name} 稳定结构分析")
    print('='*60)

    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # 查找包含链接的结构
    print("\n🔗 链接结构:")

    if engine_name == "必应":
        # 查找所有包含 href 的 a 标签
        links = soup.find_all('a', href=True)
        news_links = [l for l in links if '/news/' in l.get('href', '') or l.get('data-title')]

        print(f"找到 {len(news_links)} 个新闻链接")

        for i, link in enumerate(news_links[:3]):
            print(f"\n链接 {i+1}:")
            print(f"  href: {link.get('href', '')[:80]}")

            # 查找父级div的属性
            parent = link.find_parent('div')
            if parent:
                print(f"  父级div属性:")
                for attr in ['class', 'data-title', 'data-url', 'data-author', 'role']:
                    val = parent.get(attr)
                    if val:
                        print(f"    {attr}: {str(val)[:100]}")

            # 查找标题
            title = link.find(['h2', 'h3', 'h4'])
            if title:
                print(f"  标题标签: {title.name}, class: {title.get('class')}")
                print(f"  标题文本: {title.get_text(strip=True)[:60]}")

    elif engine_name == "谷歌":
        # 查找所有 /url= 开头的链接
        links = soup.find_all('a', href=True)
        url_links = [l for l in links if l.get('href', '').startswith('/url?')]

        print(f"找到 {len(url_links)} 个新闻链接")

        for i, link in enumerate(url_links[:3]):
            print(f"\n链接 {i+1}:")
            href = link.get('href', '')
            print(f"  href: {href[:80]}...")

            # 查找标题结构
            parent = link.find_parent('div')
            if parent:
                # 查找h3
                h3 = parent.find('h3')
                if h3:
                    print(f"  h3 class: {h3.get('class')}")
                    print(f"  标题: {h3.get_text(strip=True)[:60]}")

                # 查找内容div
                content_divs = parent.find_all('div')
                for div in content_divs[:3]:
                    classes = div.get('class', [])
                    if any(cls for cls in classes if len(cls) > 5 and cls[0].isupper()):
                        print(f"  内容div class: {classes}")
                        text = div.get_text(strip=True)[:60]
                        if text:
                            print(f"  文本: {text}")

    elif engine_name == "搜狗":
        # 查找所有结果
        all_divs = soup.find_all('div')
        result_divs = [d for d in all_divs if d.find('a') and d.find('h3')]

        print(f"找到 {len(result_divs)} 个可能的结果div")

        for i, div in enumerate(result_divs[:3]):
            print(f"\n结果 {i+1}:")

            link = div.find('a', href=True)
            if link:
                href = link.get('href', '')
                print(f"  href: {href[:80]}...")

            h3 = div.find('h3')
            if h3:
                print(f"  h3 class: {h3.get('class')}")
                print(f"  标题: {h3.get_text(strip=True)[:60]}")

            # 查找父级div的class
            parent = div.find_parent('div')
            if parent and parent.get('class'):
                print(f"  父级class: {parent.get('class')}")


def main():
    """主函数"""
    engines = {
        "必应": "search_engine_demos/必应_news_cleaned.html",
        "谷歌": "search_engine_demos/谷歌_news_cleaned.html",
        "搜狗": "search_engine_demos/搜狗_news_cleaned.html",
    }

    for engine_name, html_file in engines.items():
        try:
            analyze_structure(html_file, engine_name)
        except Exception as e:
            print(f"\n❌ {engine_name} 分析失败: {e}")


if __name__ == "__main__":
    main()
