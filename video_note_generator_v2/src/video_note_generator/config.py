"""
配置管理模块

使用 pydantic 进行类型安全的配置管理
"""
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """应用配置"""

    # API 配置
    openrouter_api_key: str = Field(..., description="OpenRouter API密钥")
    openrouter_api_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API地址"
    )
    openrouter_app_name: str = Field(
        default="video_note_generator_v2",
        description="应用名称"
    )
    openrouter_http_referer: str = Field(
        default="https://github.com",
        description="HTTP Referer"
    )

    unsplash_access_key: Optional[str] = Field(
        default=None,
        description="Unsplash访问密钥"
    )
    unsplash_secret_key: Optional[str] = Field(
        default=None,
        description="Unsplash密钥"
    )

    # 模型配置
    ai_model: str = Field(
        default="google/gemini-pro",
        description="AI模型名称"
    )
    whisper_model: str = Field(
        default="medium",
        description="Whisper模型大小 (tiny/base/small/medium/large)"
    )

    # 内容生成配置
    max_tokens: int = Field(
        default=2000,
        ge=100,
        le=8000,
        description="生成内容的最大token数"
    )
    content_chunk_size: int = Field(
        default=2000,
        ge=500,
        le=5000,
        description="长文本分块大小（字符数）"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="AI创造性程度"
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="采样阈值"
    )

    # 笔记样式配置
    use_emoji: bool = Field(default=True, description="是否使用表情符号")
    tag_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="生成的标签数量"
    )
    min_paragraphs: int = Field(default=3, ge=1, description="最少段落数")
    max_paragraphs: int = Field(default=6, ge=1, description="最多段落数")

    # 目录配置
    output_dir: Path = Field(
        default=Path("generated_notes"),
        description="输出目录"
    )
    cache_dir: Path = Field(
        default=Path(".cache"),
        description="缓存目录"
    )
    log_dir: Path = Field(
        default=Path("logs"),
        description="日志目录"
    )

    # 代理配置
    http_proxy: Optional[str] = Field(default=None, description="HTTP代理")
    https_proxy: Optional[str] = Field(default=None, description="HTTPS代理")

    # Cookies 配置（用于访问需要登录的视频）
    cookie_file: Optional[str] = Field(
        default=None,
        description="浏览器cookies文件路径（Netscape格式）"
    )

    # 调试配置
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(
        default="INFO",
        description="日志级别 (DEBUG/INFO/WARNING/ERROR)"
    )

    # FFmpeg配置
    ffmpeg_path: Optional[str] = Field(
        default=None,
        description="FFmpeg可执行文件路径"
    )

    @validator("max_paragraphs")
    def validate_paragraph_range(cls, v, values):
        """验证段落范围"""
        if "min_paragraphs" in values and v < values["min_paragraphs"]:
            raise ValueError("max_paragraphs 必须大于等于 min_paragraphs")
        return v

    @validator("output_dir", "cache_dir", "log_dir")
    def ensure_dir_exists(cls, v):
        """确保目录存在"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @validator("log_level")
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"log_level 必须是以下之一: {', '.join(valid_levels)}")
        return v

    def get_proxies(self) -> Optional[dict]:
        """获取代理配置"""
        if self.http_proxy or self.https_proxy:
            return {
                "http://": self.http_proxy,
                "https://": self.https_proxy,
            }
        return None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        # 允许从环境变量读取（自动转换大小写）
        env_prefix = ""


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = Settings()
    return _settings
