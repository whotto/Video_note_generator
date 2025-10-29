"""
Bilibili 专用下载器

使用特定的 API 和策略下载 B站视频
"""
import re
import time
from pathlib import Path
from typing import Optional
import httpx
import subprocess

from .base import BaseDownloader, VideoInfo, DownloadError


class BilibiliDownloader(BaseDownloader):
    """B站专用下载器"""

    def __init__(self, logger=None, cookie_file: Optional[str] = None):
        """
        初始化下载器

        Args:
            logger: 日志记录器
            cookie_file: Cookie 文件路径（Netscape 格式）
        """
        super().__init__(logger)
        self.cookie_file = cookie_file

    def supports(self, url: str) -> bool:
        """检查是否支持该URL"""
        patterns = [
            r'bilibili\.com/video/[Bb][Vv][\w]+',
            r'b23\.tv/[\w]+',  # B站短链接
        ]
        return any(re.search(pattern, url) for pattern in patterns)

    def _extract_bvid(self, url: str) -> Optional[str]:
        """提取 BV 号"""
        # 处理短链接
        if 'b23.tv' in url:
            try:
                # 短链接需要重定向获取真实URL
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                }
                response = httpx.get(url, headers=headers, follow_redirects=True, timeout=10)
                url = str(response.url)
            except Exception as e:
                self.logger.warning(f"解析短链接失败: {e}")
                return None

        # 提取 BV 号
        match = re.search(r'[Bb][Vv]([\w]+)', url)
        if match:
            return f"BV{match.group(1)}"
        return None

    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """
        获取视频信息（不下载）

        Args:
            url: 视频URL

        Returns:
            视频信息
        """
        bvid = self._extract_bvid(url)
        if not bvid:
            return None

        try:
            # 使用 B站 API 获取视频信息
            api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"

            # 添加必要的请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }

            response = httpx.get(api_url, headers=headers, timeout=10)
            data = response.json()

            if data['code'] != 0:
                self.logger.error(f"获取视频信息失败: {data.get('message')}")
                return None

            video_data = data['data']
            return VideoInfo(
                title=video_data['title'],
                uploader=video_data['owner']['name'],
                description=video_data['desc'],
                duration=video_data['duration'],
                platform='bilibili',
                url=url,
                thumbnail_url=video_data.get('pic')
            )

        except Exception as e:
            self.logger.error(f"获取视频信息失败: {e}")
            return None

    def _is_rate_limited(self, error_msg: str) -> bool:
        """检查是否是速率限制错误"""
        rate_limit_indicators = [
            '412',
            'Precondition Failed',
            'rate limit',
            'too many requests',
            '请求过于频繁',
        ]
        error_lower = str(error_msg).lower()
        return any(indicator.lower() in error_lower for indicator in rate_limit_indicators)

    def download(
        self,
        url: str,
        output_dir: Path,
        audio_only: bool = True,
        max_retries: int = 3
    ) -> tuple[Optional[str], Optional[VideoInfo]]:
        """
        下载视频（带重试机制）

        优先使用 you-get，因为它对 B站支持更好

        Args:
            url: 视频URL
            output_dir: 输出目录
            audio_only: 是否只下载音频
            max_retries: 最大重试次数

        Returns:
            (下载文件路径, 视频信息) 元组
        """
        bvid = self._extract_bvid(url)
        if not bvid:
            raise DownloadError(
                "无法解析 BV 号",
                "bilibili",
                "parse_error"
            )

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 获取视频信息
        video_info = self.get_video_info(url)
        if not video_info:
            raise DownloadError(
                "无法获取视频信息",
                "bilibili",
                "info_error"
            )

        last_error = None
        for attempt in range(max_retries):
            try:
                # 方法1: 尝试使用 you-get（对B站支持最好）
                self.logger.info(f"尝试使用 you-get 下载... (尝试 {attempt + 1}/{max_retries})")
                result = self._download_with_youget(url, output_dir)
                if result:
                    return result, video_info

                # 方法2: 回退到 yt-dlp
                self.logger.info(f"you-get 失败，尝试使用 yt-dlp... (尝试 {attempt + 1}/{max_retries})")
                result = self._download_with_ytdlp(url, output_dir, audio_only)
                if result:
                    return result, video_info

                # 如果两种方法都失败，记录错误
                last_error = "所有下载方法都失败"

            except Exception as e:
                last_error = e
                error_msg = str(e)

                # 检查是否是速率限制错误
                if self._is_rate_limited(error_msg):
                    wait_time = 5 * (attempt + 1)  # 递增等待时间：5秒, 10秒, 15秒

                    if attempt < max_retries - 1:
                        self.logger.warning(
                            f"⚠️  检测到 B站 限流 (HTTP 412错误)\n"
                            f"   这是 B站 的反爬虫保护，不是程序问题\n"
                            f"   等待 {wait_time} 秒后重试... (尝试 {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise DownloadError(
                            f"B站下载失败：您的 IP 地址已被 B站 临时限流\n"
                            f"原因：短时间内请求次数过多\n"
                            f"解决方法：\n"
                            f"  1. 等待 10-30 分钟后再试\n"
                            f"  2. 检查是否在浏览器中登录了 B站 账号\n"
                            f"  3. 尝试使用不同的网络连接\n"
                            f"详细信息：{error_msg}",
                            "bilibili",
                            "rate_limited",
                            error_msg
                        )
                else:
                    # 其他错误，直接抛出
                    error_msg = self._handle_error(e, url)
                    raise DownloadError(
                        error_msg,
                        "bilibili",
                        "download_failed",
                        str(e)
                    )

        # 所有重试都失败
        raise DownloadError(
            f"下载失败（已重试 {max_retries} 次）：{last_error}",
            "bilibili",
            "download_failed",
            str(last_error)
        )

    def _download_with_youget(
        self,
        url: str,
        output_dir: Path
    ) -> Optional[str]:
        """
        使用 you-get 下载

        Args:
            url: 视频URL
            output_dir: 输出目录

        Returns:
            下载的文件路径
        """
        try:
            cmd = [
                'you-get',
                '--no-proxy',
                '--format=dash-flv720',  # B站常用格式
                '-o', str(output_dir),
                url
            ]

            # 如果有 cookie 文件
            if self.cookie_file:
                cmd.extend(['-c', self.cookie_file])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode == 0:
                # 查找下载的文件
                files = list(output_dir.glob('*.flv'))
                if not files:
                    files = list(output_dir.glob('*.mp4'))

                if files:
                    return str(max(files, key=lambda p: p.stat().st_mtime))

            self.logger.warning(f"you-get 下载失败: {result.stderr}")
            return None

        except subprocess.TimeoutExpired:
            self.logger.warning("you-get 下载超时")
            return None
        except FileNotFoundError:
            self.logger.warning("you-get 未安装")
            return None
        except Exception as e:
            self.logger.warning(f"you-get 下载失败: {e}")
            return None

    def _download_with_ytdlp(
        self,
        url: str,
        output_dir: Path,
        audio_only: bool
    ) -> Optional[str]:
        """
        使用 yt-dlp 下载

        Args:
            url: 视频URL
            output_dir: 输出目录
            audio_only: 是否只下载音频

        Returns:
            下载的文件路径

        Raises:
            Exception: 如果遇到速率限制错误，向上层抛出
        """
        try:
            import yt_dlp

            options = {
                'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'proxy': '',  # 明确禁用代理
                # 添加B站必需的请求头
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.bilibili.com',
                    'Accept': '*/*',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Origin': 'https://www.bilibili.com',
                },
                # 添加额外的 extractors 选项
                'extractor_args': {
                    'bilibili': {
                        'api_host': 'api.bilibili.com'
                    }
                },
            }

            if audio_only:
                options.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }],
                })

            # 如果配置了cookies文件，则使用（避免从浏览器读取时弹窗）
            if self.cookie_file and Path(self.cookie_file).exists():
                options['cookiefile'] = str(self.cookie_file)
                self.logger.debug(f"B站下载使用cookies文件: {self.cookie_file}")

            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])

                # 查找下载的文件
                ext = 'mp3' if audio_only else 'mp4'
                files = list(output_dir.glob(f'*.{ext}'))
                if files:
                    return str(max(files, key=lambda p: p.stat().st_mtime))

            return None

        except Exception as e:
            error_msg = str(e)

            # 如果是速率限制错误，向上层抛出以便重试
            if self._is_rate_limited(error_msg):
                self.logger.debug(f"yt-dlp 检测到速率限制: {error_msg}")
                raise  # 抛出异常让上层的 download() 方法处理重试
            else:
                # 其他错误只记录日志，返回 None 让程序尝试其他方法
                self.logger.warning(f"yt-dlp 下载失败: {e}")
                return None
