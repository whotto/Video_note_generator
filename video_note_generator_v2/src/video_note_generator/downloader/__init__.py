"""
视频下载器模块
"""
from .base import (
    BaseDownloader,
    VideoInfo,
    DownloadError,
    DownloaderRegistry
)
from .ytdlp_downloader import YtDlpDownloader
from .bilibili_downloader import BilibiliDownloader
from .res_downloader import ResDownloader

__all__ = [
    'BaseDownloader',
    'VideoInfo',
    'DownloadError',
    'DownloaderRegistry',
    'YtDlpDownloader',
    'BilibiliDownloader',
    'ResDownloader',
]
