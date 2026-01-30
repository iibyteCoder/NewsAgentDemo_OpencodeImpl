"""配置管理"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """下载器配置"""

    model_config = SettingsConfigDict(
        env_prefix="DOWNLOADER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 默认下载目录
    default_download_dir: Path = Path("./downloads")

    # 并发下载数量
    max_concurrent_downloads: int = 15

    # 请求超时时间（秒）
    request_timeout: int = 30

    # 重试次数
    max_retries: int = 3

    # 重试延迟（秒）
    retry_delay: float = 1.0

    # User-Agent
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # 支持的图片格式
    image_extensions: set[str] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".svg",
        ".ico",
    }

    # 支持的文档格式
    document_extensions: set[str] = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
    }


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
        # 确保下载目录存在
        _settings.default_download_dir.mkdir(parents=True, exist_ok=True)
    return _settings
