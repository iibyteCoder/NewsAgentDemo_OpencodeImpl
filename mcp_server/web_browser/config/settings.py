"""集中配置管理 - 使用 Pydantic 进行配置验证"""

from functools import lru_cache
from typing import Optional, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MCP Server 配置"""

    model_config = SettingsConfigDict(
        env_prefix="MCP_SERVER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ========== 浏览器配置 ==========
    max_concurrent_browsers: int = Field(
        default=2,
        description="最大并发浏览器数量",
        ge=1,
        le=10,
    )
    max_contexts_per_browser: int = Field(
        default=5,
        description="每个浏览器最大上下文数",
        ge=1,
        le=20,
    )
    max_context_pool_size: int = Field(
        default=10,
        description="最大上下文池大小",
        ge=1,
        le=50,
    )
    context_max_idle_time: int = Field(
        default=300,
        description="上下文最大空闲时间（秒）",
        ge=60,
    )
    headless: bool = Field(
        default=True,
        description="是否使用无头模式",
    )

    # ========== 速率限制配置 ==========
    rate_limit_time_window: float = Field(
        default=1.0,
        description="速率限制时间窗口（秒）",
        ge=0.1,
    )
    max_domain_requests_per_second: int = Field(
        default=2,
        description="同一域名每秒最大请求数",
        ge=1,
    )
    max_engine_requests_per_second: int = Field(
        default=2,
        description="同一引擎每秒最大请求数",
        ge=1,
    )

    # ========== 代理配置 ==========
    proxy_server: Optional[str] = Field(
        default=None,
        description="代理服务器地址（如 localhost:7897）",
    )
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None

    @property
    def proxy_config(self) -> Optional[dict]:
        """获取代理配置字典"""
        if not self.proxy_server:
            return None
        config = {"server": self.proxy_server}
        if self.proxy_username and self.proxy_password:
            config["username"] = self.proxy_username
            config["password"] = self.proxy_password
        return config

    # ========== User-Agent 配置 ==========
    user_agents: List[str] = Field(
        default=[
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ],
        description="User-Agent 列表",
    )

    # ========== 搜索引擎配置 ==========
    enabled_engines: List[str] = Field(
        default=[
            "baidu",
            "bing",
            "sogou",
            "google",
            "360",
            "toutiao",
            "tencent",
            "wangyi",
            "sina",
            "sohu",
        ],
        description="启用的搜索引擎列表",
    )

    default_num_results: int = Field(
        default=30,
        description="默认返回结果数量",
        ge=1,
        le=100,
    )

    # ========== Cookie 存储配置 ==========
    cookie_file: str = Field(
        default=".baidu_cookies.json",
        description="Cookie 存储文件路径",
    )


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
