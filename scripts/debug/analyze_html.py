"""
通用HTML清洗工具 - 移除script/css/header等标签，保留body内容
"""

import sys
import io
from bs4 import BeautifulSoup
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def clean_html(html_file: str, engine_name: str):
    """清洗HTML文件 - 移除script/css/header等标签，保留body内容"""
    print(f"\n{'='*60}")
    print(f"清洗 {engine_name} HTML文件")
    print(f"{'='*60}")

    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # 只移除真正的噪音标签（不影响内容的关键信息）
    # script/style: JavaScript和CSS样式
    # noscript: 无脚本时的替代内容
    # iframe/svg/canvas/video/audio: 多媒体和嵌入内容
    tags_to_remove = ['script', 'style', 'noscript', 'iframe',
                      'svg', 'canvas', 'video', 'audio']

    removed_count = 0
    for tag_name in tags_to_remove:
        for tag in soup.find_all(tag_name):
            tag.decompose()
            removed_count += 1

    # 保存清洗后的HTML（只保留body内容）
    if soup.body:
        cleaned_html = str(soup.body)
    else:
        cleaned_html = str(soup)

    # 保存清洗后的文件
    output_file = Path("search_engine_demos") / f"{engine_name}_cleaned.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_html)

    # 统计信息
    original_size = len(html)
    cleaned_size = len(cleaned_html)
    reduction_rate = (1 - cleaned_size / original_size) * 100

    print(f"✅ 清洗完成")
    print(f"   移除了 {removed_count} 个标签")
    print(f"   原始大小: {original_size:,} 字符")
    print(f"   清洗后大小: {cleaned_size:,} 字符")
    print(f"   清理率: {reduction_rate:.1f}%")
    print(f"   已保存到: {output_file}")

    # 分析清洗后的基本结构
    soup_cleaned = BeautifulSoup(cleaned_html, 'html.parser')
    print("\n📊 清洗后基本统计:")
    print(f"   链接数量: {len(soup_cleaned.find_all('a', href=True))}")
    print(f"   标题数量(h1-h4): {len(soup_cleaned.find_all(['h1', 'h2', 'h3', 'h4']))}")
    print(f"   图片数量: {len(soup_cleaned.find_all('img'))}")
    print(f"   div数量: {len(soup_cleaned.find_all('div'))}")
    print(f"   p数量: {len(soup_cleaned.find_all('p'))}")


def main():
    """主函数"""
    demo_dir = Path("search_engine_demos")

    engines = {
        "百度": "百度_news.html",
        "必应": "必应_news.html",
        "谷歌": "谷歌_news.html",
        "搜狗": "搜狗_news.html",
    }

    for engine_name, filename in engines.items():
        html_file = demo_dir / filename

        if not html_file.exists():
            print(f"⚠️ 文件不存在: {html_file}")
            continue

        try:
            clean_html(str(html_file), engine_name)
        except Exception as e:
            print(f"❌ 清洗失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
