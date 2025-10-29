"""
多策略视频下载器

支持多种下载方式的组合：
1. 本地工具（yt-dlp, you-get, gallery-dl）
2. 可配置的API服务
3. 用户自定义脚本
"""
import subprocess
import os
from pathlib import Path
from typing import Optional, List, Dict, Callable
import logging

from .base import BaseDownloader, VideoInfo, DownloadError


class DownloadStrategy:
    """下载策略基类"""

    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority

    def can_handle(self, url: str) -> bool:
        """检查是否可以处理该URL"""
        raise NotImplementedError

    def download(self, url: str, output_dir: Path) -> Optional[str]:
        """下载视频，返回文件路径"""
        raise NotImplementedError


class YtDlpStrategy(DownloadStrategy):
    """yt-dlp 策略"""

    def __init__(self, priority: int = 10):
        super().__init__("yt-dlp", priority)

    def can_handle(self, url: str) -> bool:
        """yt-dlp 支持大部分平台"""
        return True

    def download(self, url: str, output_dir: Path) -> Optional[str]:
        try:
            import yt_dlp

            options = {
                'format': 'bestaudio/best',
                'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])

            # 查找下载的文件
            files = list(output_dir.glob('*.mp3'))
            if files:
                return str(max(files, key=os.path.getmtime))
            return None

        except Exception:
            return None


class YouGetStrategy(DownloadStrategy):
    """you-get 策略（适合B站等）"""

    def __init__(self, priority: int = 20):
        super().__init__("you-get", priority)

    def can_handle(self, url: str) -> bool:
        """you-get 对某些平台支持更好"""
        platforms = ['bilibili.com', 'youku.com', 'iqiyi.com']
        return any(p in url for p in platforms)

    def download(self, url: str, output_dir: Path) -> Optional[str]:
        try:
            cmd = ['you-get', '-o', str(output_dir), url]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                # 查找下载的文件
                for ext in ['.mp4', '.flv', '.mp3']:
                    files = list(output_dir.glob(f'*{ext}'))
                    if files:
                        return str(max(files, key=os.path.getmtime))
            return None

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None


class GalleryDlStrategy(DownloadStrategy):
    """gallery-dl 策略（适合图片网站和社交媒体）"""

    def __init__(self, priority: int = 15):
        super().__init__("gallery-dl", priority)

    def can_handle(self, url: str) -> bool:
        """gallery-dl 适合图片和视频网站"""
        platforms = ['twitter.com', 'x.com', 'instagram.com', 'reddit.com']
        return any(p in url for p in platforms)

    def download(self, url: str, output_dir: Path) -> Optional[str]:
        try:
            cmd = ['gallery-dl', '-d', str(output_dir), url]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                # 查找下载的文件
                for ext in ['.mp4', '.mp3', '.webm']:
                    files = list(output_dir.glob(f'**/*{ext}'), recursive=True)
                    if files:
                        return str(max(files, key=os.path.getmtime))
            return None

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None


class CustomScriptStrategy(DownloadStrategy):
    """自定义脚本策略"""

    def __init__(self, script_path: str, priority: int = 5):
        super().__init__("custom-script", priority)
        self.script_path = script_path

    def can_handle(self, url: str) -> bool:
        """检查脚本是否存在"""
        return os.path.exists(self.script_path)

    def download(self, url: str, output_dir: Path) -> Optional[str]:
        """
        执行自定义脚本
        脚本应该：
        - 接受两个参数：URL 和输出目录
        - 下载文件到输出目录
        - 成功时返回 0
        """
        try:
            cmd = [self.script_path, url, str(output_dir)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                # 查找最新下载的文件
                files = list(output_dir.glob('*'))
                if files:
                    return str(max(files, key=os.path.getmtime))
            return None

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None


class MultiStrategyDownloader(BaseDownloader):
    """多策略下载器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        self.strategies: List[DownloadStrategy] = []
        self._setup_default_strategies()

    def _setup_default_strategies(self):
        """设置默认策略（按优先级排序）"""
        # 优先级：you-get > gallery-dl > yt-dlp
        self.add_strategy(YouGetStrategy(priority=20))
        self.add_strategy(GalleryDlStrategy(priority=15))
        self.add_strategy(YtDlpStrategy(priority=10))

    def add_strategy(self, strategy: DownloadStrategy):
        """添加下载策略"""
        self.strategies.append(strategy)
        # 按优先级降序排序
        self.strategies.sort(key=lambda s: s.priority, reverse=True)

    def supports(self, url: str) -> bool:
        """检查是否支持该URL（任一策略支持即可）"""
        return any(s.can_handle(url) for s in self.strategies)

    def download(
        self,
        url: str,
        output_dir: Path,
        audio_only: bool = True
    ) -> tuple[Optional[str], Optional[VideoInfo]]:
        """
        使用多个策略尝试下载

        Args:
            url: 视频URL
            output_dir: 输出目录
            audio_only: 是否只下载音频

        Returns:
            (下载文件路径, 视频信息) 元组
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 尝试每个可用的策略
        for strategy in self.strategies:
            if not strategy.can_handle(url):
                continue

            self.logger.info(f"尝试使用 {strategy.name} 下载...")

            try:
                file_path = strategy.download(url, output_dir)

                if file_path and os.path.exists(file_path):
                    self.logger.info(f"✅ 使用 {strategy.name} 下载成功")

                    # 创建简单的视频信息
                    video_info = VideoInfo(
                        title=Path(file_path).stem,
                        uploader="Unknown",
                        description="",
                        duration=0,
                        platform=self._extract_platform(url),
                        url=url
                    )

                    return file_path, video_info
                else:
                    self.logger.warning(f"⚠️ {strategy.name} 下载失败")

            except Exception as e:
                self.logger.warning(f"⚠️ {strategy.name} 出错: {e}")
                continue

        # 所有策略都失败
        self.logger.error("所有下载策略都失败")
        raise DownloadError(
            "所有下载方法都失败",
            self._extract_platform(url),
            "all_strategies_failed"
        )

    def _extract_platform(self, url: str) -> str:
        """从URL提取平台名称"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'bilibili.com' in url:
            return 'bilibili'
        elif 'douyin.com' in url or 'tiktok.com' in url:
            return 'tiktok'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'twitter'
        elif 'instagram.com' in url:
            return 'instagram'
        else:
            return 'unknown'

    def get_available_strategies(self) -> List[str]:
        """获取可用的策略列表"""
        available = []
        for strategy in self.strategies:
            # 简单测试策略是否可用
            if isinstance(strategy, CustomScriptStrategy):
                if os.path.exists(strategy.script_path):
                    available.append(strategy.name)
            else:
                # 对于工具类策略，尝试调用命令检查是否安装
                tool_name = strategy.name
                try:
                    subprocess.run(
                        [tool_name, '--version'],
                        capture_output=True,
                        timeout=5
                    )
                    available.append(strategy.name)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
        return available


def create_multi_strategy_downloader(
    logger: Optional[logging.Logger] = None,
    custom_scripts: Optional[List[str]] = None
) -> MultiStrategyDownloader:
    """
    创建多策略下载器（便捷函数）

    Args:
        logger: 日志记录器
        custom_scripts: 自定义脚本路径列表

    Returns:
        多策略下载器实例
    """
    downloader = MultiStrategyDownloader(logger)

    # 添加自定义脚本策略
    if custom_scripts:
        for i, script in enumerate(custom_scripts):
            strategy = CustomScriptStrategy(script, priority=30 + i)
            downloader.add_strategy(strategy)

    return downloader
