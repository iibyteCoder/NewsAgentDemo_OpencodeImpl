"""
从HTML文件中移除data:image格式的内联图片

使用示例:
    # 方式1: 处理HTML字符串
    from remove_data_images import remove_data_images_from_html
    cleaned_html, count = remove_data_images_from_html(html_content)

    # 方式2: 处理文件
    from remove_data_images import process_file_simple
    output_file = process_file_simple('input.html')

    # 方式3: 处理目录
    from remove_data_images import process_directory_simple
    output_dir = process_directory_simple('html_files/')
"""
import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Tuple, Optional


def remove_data_images_from_html(html_content):
    """
    从HTML内容中移除所有src="data:image/..."的图片标签

    Args:
        html_content: HTML字符串内容

    Returns:
        处理后的HTML字符串
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # 查找所有img标签
    img_tags = soup.find_all('img')

    removed_count = 0
    for img in img_tags:
        # 检查src属性是否以data:image开头
        if img.get('src', '').startswith('data:image'):
            img.decompose()  # 完全移除这个标签
            removed_count += 1

    return str(soup), removed_count


def remove_data_images_regex(html_content):
    """
    使用正则表达式移除data:image格式的图片标签

    Args:
        html_content: HTML字符串内容

    Returns:
        处理后的HTML字符串
    """
    # 匹配 <img src="data:image/..." ... >
    pattern = r'<img[^>]*\ssrc=["\']data:image/[^"\']*["\'][^>]*>'

    matches = re.findall(pattern, html_content)
    removed_count = len(matches)

    # 移除匹配的标签
    result = re.sub(pattern, '', html_content)

    return result, removed_count


def process_file(input_file, output_file=None, use_regex=False):
    """
    处理单个HTML文件

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选，默认添加_cleaned后缀）
        use_regex: 是否使用正则表达式方法（默认使用BeautifulSoup）
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"错误: 文件不存在 - {input_file}")
        return

    # 读取文件
    print(f"正在处理: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 处理HTML
    if use_regex:
        result, count = remove_data_images_regex(html_content)
        method = "正则表达式"
    else:
        result, count = remove_data_images_from_html(html_content)
        method = "BeautifulSoup"

    # 确定输出文件（默认添加_cleaned后缀）
    if output_file is None:
        output_path = input_path.with_stem(input_path.stem + '_cleaned')
    else:
        output_path = Path(output_file)

    # 写入结果
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"使用方法: {method}")
    print(f"移除了 {count} 个data:image图片")
    print(f"结果已保存到: {output_path}")
    print()


def process_directory(input_dir, output_dir=None, use_regex=False, pattern="*.html"):
    """
    批量处理目录中的HTML文件

    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径（可选，默认在输入目录中创建cleaned子目录）
        use_regex: 是否使用正则表达式方法
        pattern: 文件匹配模式（默认*.html）
    """
    input_path = Path(input_dir)

    if not input_path.exists() or not input_path.is_dir():
        print(f"错误: 目录不存在 - {input_dir}")
        return

    # 查找所有HTML文件
    html_files = list(input_path.glob(pattern))
    htm_files = list(input_path.glob("*.htm"))
    all_files = html_files + htm_files

    if not all_files:
        print(f"在 {input_dir} 中没有找到HTML文件")
        return

    # 确定输出目录（默认创建cleaned子目录）
    if output_dir is None:
        output_path = input_path / 'cleaned'
    else:
        output_path = Path(output_dir)

    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"找到 {len(all_files)} 个HTML文件")
    print(f"输出目录: {output_path}")
    print()

    # 处理每个文件
    for html_file in all_files:
        output_file = output_path / html_file.name
        process_file(str(html_file), str(output_file), use_regex)


# ========== 简化的API函数，方便在代码中调用 ==========

def process_file_simple(
    input_file: str,
    output_file: Optional[str] = None,
    use_regex: bool = False
) -> str:
    """
    简化版：处理单个HTML文件，返回输出文件路径

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选，默认添加_cleaned后缀）
        use_regex: 是否使用正则表达式方法

    Returns:
        输出文件的完整路径

    示例:
        >>> output_path = process_file_simple('page.html')
        >>> print(f"已保存到: {output_path}")
    """
    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(f"文件不存在: {input_file}")

    # 读取文件
    with open(input_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 处理HTML
    if use_regex:
        result, _ = remove_data_images_regex(html_content)
    else:
        result, _ = remove_data_images_from_html(html_content)

    # 确定输出文件
    if output_file is None:
        output_path = input_path.with_stem(input_path.stem + '_cleaned')
    else:
        output_path = Path(output_file)

    # 写入结果
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    return str(output_path)


def process_directory_simple(
    input_dir: str,
    output_dir: Optional[str] = None,
    use_regex: bool = False,
    pattern: str = "*.html"
) -> dict:
    """
    简化版：批量处理目录，返回处理统计信息

    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径（可选，默认创建cleaned子目录）
        use_regex: 是否使用正则表达式方法
        pattern: 文件匹配模式

    Returns:
        包含统计信息的字典: {
            'total_files': 总文件数,
            'total_removed': 总移除图片数,
            'output_dir': 输出目录路径,
            'files': [{file: 文件路径, removed: 移除数量, output: 输出路径}, ...]
        }

    示例:
        >>> stats = process_directory_simple('html_files/')
        >>> print(f"处理了 {stats['total_files']} 个文件")
        >>> print(f"移除了 {stats['total_removed']} 个图片")
    """
    input_path = Path(input_dir)

    if not input_path.exists() or not input_path.is_dir():
        raise NotADirectoryError(f"目录不存在: {input_dir}")

    # 查找所有HTML文件
    html_files = list(input_path.glob(pattern))
    htm_files = list(input_path.glob("*.htm"))
    all_files = html_files + htm_files

    if not all_files:
        return {
            'total_files': 0,
            'total_removed': 0,
            'output_dir': '',
            'files': []
        }

    # 确定输出目录
    if output_dir is None:
        output_path = input_path / 'cleaned'
    else:
        output_path = Path(output_dir)

    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)

    # 处理每个文件
    files_info = []
    total_removed = 0

    for html_file in all_files:
        output_file = output_path / html_file.name

        # 读取文件
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 处理HTML
        if use_regex:
            result, count = remove_data_images_regex(html_content)
        else:
            result, count = remove_data_images_from_html(html_content)

        # 写入结果
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)

        total_removed += count
        files_info.append({
            'file': str(html_file),
            'removed': count,
            'output': str(output_file)
        })

    return {
        'total_files': len(all_files),
        'total_removed': total_removed,
        'output_dir': str(output_path),
        'files': files_info
    }


def clean_html_string(html_content: str, use_regex: bool = False) -> Tuple[str, int]:
    """
    清理HTML字符串中的data:image图片

    Args:
        html_content: HTML字符串内容
        use_regex: 是否使用正则表达式方法

    Returns:
        (清理后的HTML字符串, 移除的图片数量)

    示例:
        >>> html = '<img src="data:image/png;base64,...">测试'
        >>> cleaned, count = clean_html_string(html)
        >>> print(f"移除了 {count} 个图片")
    """
    if use_regex:
        return remove_data_images_regex(html_content)
    else:
        return remove_data_images_from_html(html_content)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='从HTML文件中移除data:image格式的内联图片'
    )
    parser.add_argument(
        'input',
        help='输入文件或目录路径'
    )
    parser.add_argument(
        '-o', '--output',
        help='输出文件或目录路径（可选，默认自动添加_cleaned后缀或cleaned目录）'
    )
    parser.add_argument(
        '-r', '--regex',
        action='store_true',
        help='使用正则表达式方法（默认使用BeautifulSoup）'
    )
    parser.add_argument(
        '-d', '--directory',
        action='store_true',
        help='将输入作为目录处理，批量处理所有HTML文件'
    )

    args = parser.parse_args()

    if args.directory:
        process_directory(args.input, args.output, args.regex)
    else:
        process_file(args.input, args.output, args.regex)
