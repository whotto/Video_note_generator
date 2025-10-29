"""
视频下载器基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict
from pathlib import Path
import logging


@dataclass
class VideoInfo:
    """视频信息"""
    title: str
    uploader: str
    description: str
    duration: int
    platform: str
    url: str
    thumbnail_url: Optional[str] = None


class DownloadError(Exception):
    """下载错误"""

    def __init__(
        self,
        message: str,
        platform: str,
        error_type: str,
        details: Optional[str] = None
    ):
        self.message = message
        self.platform = platform
        self.error_type = error_type
        self.details = details
        super().__init__(self.message)


class BaseDownloader(ABC):
    """视频下载器基类"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化下载器

        Args:
            logger: 日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)

    @abstractmethod
    def supports(self, url: str) -> bool:
        """
        检查是否支持该URL

        Args:
            url: 视频URL

        Returns:
            是否支持
        """
        pass

    @abstractmethod
    def download(
        self,
        url: str,
        output_dir: Path,
        audio_only: bool = True
    ) -> tuple[Optional[str], Optional[VideoInfo]]:
        """
        下载视频

        Args:
            url: 视频URL
            output_dir: 输出目录
            audio_only: 是否只下载音频

        Returns:
            (下载文件路径, 视频信息) 元组
        """
        pass

    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """
        获取视频信息（不下载）

        Args:
            url: 视频URL

        Returns:
            视频信息
        """
        raise NotImplementedError("子类需要实现此方法")

    def _handle_error(self, error: Exception, url: str) -> str:
        """
        处理错误并返回用户友好的错误消息

        Args:
            error: 异常对象
            url: 视频URL

        Returns:
            错误消息
        """
        error_msg = str(error)

        if "SSL" in error_msg:
            return "SSL证书验证失败，请检查网络连接"
        elif "cookies" in error_msg.lower():
            return f"访问被拒绝，可能需要更新cookie或更换IP地址"
        elif "404" in error_msg:
            return "视频不存在或已被删除"
        elif "403" in error_msg:
            return "访问被拒绝，可能需要登录或更换IP地址"
        elif "unavailable" in error_msg.lower():
            return "视频当前不可用，可能是地区限制或版权问题"
        else:
            return f"下载失败: {error_msg}"


class DownloaderRegistry:
    """下载器注册表"""

    def __init__(self):
        self._downloaders: list[BaseDownloader] = []

    def register(self, downloader: BaseDownloader):
        """
        注册下载器

        Args:
            downloader: 下载器实例
        """
        self._downloaders.append(downloader)

    def get_downloader(self, url: str) -> Optional[BaseDownloader]:
        """
        根据URL获取合适的下载器

        Args:
            url: 视频URL

        Returns:
            下载器实例，如果没有合适的返回None
        """
        for downloader in self._downloaders:
            if downloader.supports(url):
                return downloader
        return None

    def download(
        self,
        url: str,
        output_dir: Path,
        audio_only: bool = True
    ) -> tuple[Optional[str], Optional[VideoInfo]]:
        """
        使用合适的下载器下载视频

        Args:
            url: 视频URL
            output_dir: 输出目录
            audio_only: 是否只下载音频

        Returns:
            (下载文件路径, 视频信息) 元组

        Raises:
            DownloadError: 如果没有合适的下载器或下载失败
        """
        downloader = self.get_downloader(url)
        if not downloader:
            raise DownloadError(
                "不支持的视频平台",
                "unknown",
                "platform_not_supported"
            )

        return downloader.download(url, output_dir, audio_only)
