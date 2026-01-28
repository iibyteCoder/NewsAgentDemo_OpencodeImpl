"""辅助函数"""

import re
from typing import Optional

from bs4 import BeautifulSoup

from ..core.config import get_settings


def extract_image_urls(html_content: str, base_url: Optional[str] = None) -> list[str]:
    """从HTML内容中提取图片URL

    Args:
        html_content: HTML内容
        base_url: 基础URL（用于处理相对路径）

    Returns:
        图片URL列表
    """
    settings = get_settings()
    soup = BeautifulSoup(html_content, "lxml")
    urls = []

    # 查找所有img标签
    for img in soup.find_all("img", src=True):
        url = img["src"]
        # 处理相对路径
        if base_url and not url.startswith(("http://", "https://", "//")):
            from urllib.parse import urljoin

            url = urljoin(base_url, url)

        # 过滤有效的图片扩展名
        if any(url.lower().endswith(ext) for ext in settings.image_extensions):
            urls.append(url)

    # 查找picture标签中的source
    for picture in soup.find_all("picture"):
        for source in picture.find_all("source", srcset=True):
            srcset = source["srcset"]
            # 解析srcset（可能有多个URL）
            for part in srcset.split(","):
                url = part.strip().split()[0]
                if base_url and not url.startswith(("http://", "https://", "//")):
                    from urllib.parse import urljoin

                    url = urljoin(base_url, url)

                if any(url.lower().endswith(ext) for ext in settings.image_extensions):
                    urls.append(url)

    # 查找背景图片（CSS中的url()）
    pattern = r'url\(["\']?([^"\'()]+\.(?:jpg|jpeg|png|gif|webp|svg|bmp))["\']?\)'
    for match in re.finditer(pattern, html_content, re.IGNORECASE):
        url = match.group(1)
        if base_url and not url.startswith(("http://", "https://", "//")):
            from urllib.parse import urljoin

            url = urljoin(base_url, url)
        urls.append(url)

    # 去重并返回
    return list(dict.fromkeys(urls))


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    # 替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # 移除控制字符
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)
    # 限制长度
    if len(filename) > 200:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[: 200 - len(ext) - 1] + ("." + ext if ext else "")
    return filename


def generate_unique_filename(
    base_name: str, existing_files: set[str], max_suffix: int = 1000
) -> str:
    """生成唯一的文件名

    Args:
        base_name: 基础文件名
        existing_files: 已存在的文件名集合
        max_suffix: 最大后缀数

    Returns:
        唯一的文件名
    """
    if base_name not in existing_files:
        return base_name

    name, ext = base_name.rsplit(".", 1) if "." in base_name else (base_name, "")

    for i in range(1, max_suffix + 1):
        new_name = f"{name}_{i}.{ext}" if ext else f"{name}_{i}"
        if new_name not in existing_files:
            return new_name

    # 如果都存在，添加时间戳
    import time

    timestamp = int(time.time())
    new_name = f"{name}_{timestamp}.{ext}" if ext else f"{name}_{timestamp}"
    return new_name
