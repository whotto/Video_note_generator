"""
基于 yt-dlp 的通用视频下载器
"""
import os
import time
from pathlib import Path
from typing import Optional
import yt_dlp

from .base import BaseDownloader, VideoInfo, DownloadError


class YtDlpDownloader(BaseDownloader):
    """基于 yt-dlp 的下载器，支持多个平台"""

    SUPPORTED_PLATFORMS = [
        'youtube.com', 'youtu.be',
        'bilibili.com',
        'douyin.com',
        'tiktok.com',
    ]

    MAX_RETRIES = 3
    RETRY_DELAY = 5  # 秒

    def __init__(self, logger=None, proxies: Optional[dict] = None, cookie_file: Optional[str] = None):
        """
        初始化下载器

        Args:
            logger: 日志记录器
            proxies: 代理配置
            cookie_file: Cookies文件路径（可选）
        """
        super().__init__(logger)
        self.proxies = proxies
        self.cookie_file = cookie_file

    def supports(self, url: str) -> bool:
        """检查是否支持该URL"""
        return any(platform in url for platform in self.SUPPORTED_PLATFORMS)

    def _get_platform_name(self, url: str) -> str:
        """获取平台名称"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'bilibili.com' in url:
            return 'bilibili'
        elif 'douyin.com' in url:
            return 'douyin'
        elif 'tiktok.com' in url:
            return 'tiktok'
        return 'unknown'

    def _build_options(
        self,
        output_dir: Path,
        audio_only: bool = True
    ) -> dict:
        """
        构建 yt-dlp 选项

        Args:
            output_dir: 输出目录
            audio_only: 是否只下载音频

        Returns:
            选项字典
        """
        options = {
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            # 明确禁用代理（如果没有配置代理）
            'proxy': '',
        }

        if audio_only:
            options.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
            })
        else:
            options['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

        # 如果配置了代理则使用
        if self.proxies and self.proxies.get('http://'):
            options['proxy'] = self.proxies['http://']

        # 如果配置了cookies文件，则使用（避免从浏览器读取时弹窗）
        # 用户可以使用浏览器插件导出cookies，然后配置路径
        # 推荐插件: Get cookies.txt LOCALLY (Chrome/Firefox)
        if self.cookie_file and Path(self.cookie_file).exists():
            options['cookiefile'] = str(self.cookie_file)
            self.logger.debug(f"使用cookies文件: {self.cookie_file}")

        return options

    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """
        获取视频信息（不下载）

        Args:
            url: 视频URL

        Returns:
            视频信息
        """
        try:
            options = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'proxy': '',  # 禁用代理
            }

            # 如果配置了代理则使用
            if self.proxies and self.proxies.get('http://'):
                options['proxy'] = self.proxies['http://']

            # 尝试从浏览器导入cookie
            try:
                options['cookiesfrombrowser'] = ('chrome',)
            except Exception:
                try:
                    options['cookiesfrombrowser'] = ('firefox',)
                except Exception:
                    pass

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None

                return VideoInfo(
                    title=info.get('title', '未知标题'),
                    uploader=info.get('uploader', '未知作者'),
                    description=info.get('description', ''),
                    duration=info.get('duration', 0),
                    platform=self._get_platform_name(url),
                    url=url,
                    thumbnail_url=info.get('thumbnail')
                )

        except Exception as e:
            self.logger.error(f"获取视频信息失败: {str(e)}")
            return None

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
        platform = self._get_platform_name(url)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 构建选项
        options = self._build_options(output_dir, audio_only)

        # 重试逻辑
        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.info(
                    f"正在尝试下载（第{attempt + 1}/{self.MAX_RETRIES}次）: {url}"
                )

                with yt_dlp.YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if not info:
                        raise DownloadError(
                            "无法获取视频信息",
                            platform,
                            "info_error"
                        )

                    # 查找下载的文件
                    expected_ext = 'mp3' if audio_only else 'mp4'
                    downloaded_files = list(output_dir.glob(f"*.{expected_ext}"))

                    if not downloaded_files:
                        raise DownloadError(
                            f"未找到下载的{expected_ext}文件",
                            platform,
                            "file_not_found"
                        )

                    # 获取最新的文件
                    audio_path = max(downloaded_files, key=os.path.getmtime)

                    if not audio_path.exists():
                        raise DownloadError(
                            "下载的文件不存在",
                            platform,
                            "file_not_found"
                        )

                    video_info = VideoInfo(
                        title=info.get('title', '未知标题'),
                        uploader=info.get('uploader', '未知作者'),
                        description=info.get('description', ''),
                        duration=info.get('duration', 0),
                        platform=platform,
                        url=url,
                        thumbnail_url=info.get('thumbnail')
                    )

                    self.logger.info(f"下载成功: {video_info.title}")
                    return str(audio_path), video_info

            except Exception as e:
                error_msg = self._handle_error(e, url)
                self.logger.warning(
                    f"下载失败（第{attempt + 1}次）: {error_msg}"
                )

                if attempt < self.MAX_RETRIES - 1:
                    self.logger.info(f"等待{self.RETRY_DELAY}秒后重试...")
                    time.sleep(self.RETRY_DELAY)
                else:
                    # 最后一次尝试失败
                    raise DownloadError(
                        error_msg,
                        platform,
                        "download_failed",
                        str(e)
                    )

        return None, None
