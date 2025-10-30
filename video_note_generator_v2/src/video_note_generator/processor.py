"""
视频笔记生成处理器
"""
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging

from .config import Settings
from .downloader import (
    DownloaderRegistry,
    YtDlpDownloader,
    BilibiliDownloader,
    ResDownloader,
    VideoInfo,
)
from .transcriber import WhisperTranscriber
from .ai_processor import AIProcessor
from .generators.xiaohongshu import XiaohongshuGenerator
from .generators.blog import BlogGenerator
from .image_service import UnsplashImageService
from .subtitle_extractor import SubtitleExtractor


class VideoNoteProcessor:
    """视频笔记处理器"""

    def __init__(self, settings: Settings, logger: logging.Logger):
        """
        初始化处理器

        Args:
            settings: 配置对象
            logger: 日志记录器
        """
        self.settings = settings
        self.logger = logger

        # 初始化下载器注册表
        self.downloader_registry = DownloaderRegistry()

        # 注册 Bilibili 专用下载器（优先级高，先注册）
        bilibili_downloader = BilibiliDownloader(
            logger=logger,
            cookie_file=settings.cookie_file
        )
        self.downloader_registry.register(bilibili_downloader)

        # 注册基于 res-downloader 思路的通用下载器（抖音/小红书等）
        res_downloader = ResDownloader(
            logger=logger,
            proxies=settings.get_proxies(),
            cookie_file=settings.cookie_file
        )
        self.downloader_registry.register(res_downloader)

        # 注册通用下载器（作为最终兜底）
        ytdlp_downloader = YtDlpDownloader(
            logger=logger,
            proxies=settings.get_proxies(),
            cookie_file=settings.cookie_file
        )
        self.downloader_registry.register(ytdlp_downloader)

        # 初始化转录器
        self.transcriber = WhisperTranscriber(
            logger=logger,
            cache_dir=settings.cache_dir / "transcriptions"
        )

        # 初始化字幕提取器
        self.subtitle_extractor = SubtitleExtractor()

        # 初始化 AI 处理器
        self.ai_processor = AIProcessor(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_api_url,
            model=settings.ai_model,
            app_name=settings.openrouter_app_name,
            http_referer=settings.openrouter_http_referer,
            logger=logger
        )

        # 初始化生成器
        self.xiaohongshu_generator = XiaohongshuGenerator(
            ai_processor=self.ai_processor,
            logger=logger
        )

        self.blog_generator = BlogGenerator(
            ai_processor=self.ai_processor,
            logger=logger
        )

        # 初始化图片服务
        self.image_service = None
        if settings.unsplash_access_key:
            self.image_service = UnsplashImageService(
                access_key=settings.unsplash_access_key,
                logger=logger
            )

    def process_video(
        self,
        url: str,
        generate_xiaohongshu: bool = True,
        generate_blog: bool = True
    ) -> List[Path]:
        """
        处理视频

        Args:
            url: 视频URL
            generate_xiaohongshu: 是否生成小红书版本

        Returns:
            生成的文件路径列表
        """
        self.logger.info(f"开始处理视频: {url}")
        generated_files = []

        # 创建临时目录
        temp_dir = self.settings.output_dir / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Tier 1: 尝试提取官方字幕（最快，免费，1-5秒）
            self.logger.info("🎯 策略1: 尝试提取官方字幕...")
            transcript = self.subtitle_extractor.extract(url)
            audio_path = None

            if transcript:
                self.logger.info(f"✅ 使用官方字幕（{len(transcript)}字符，耗时<5秒）")

                # 获取视频基本信息（不下载）
                video_info = self._get_video_info_without_download(url)
                if not video_info:
                    self.logger.warning("无法获取视频信息，使用默认信息")
                    video_info = VideoInfo(
                        title="视频标题",
                        duration=0,
                        uploader="未知",
                        description=""
                    )
            else:
                # Tier 2/3: 无字幕，下载并使用Whisper转录
                self.logger.info("❌ 未找到官方字幕")
                self.logger.info("🎤 策略2/3: 下载并使用Whisper转录...")

                # 1. 下载视频
                self.logger.info("正在下载视频...")
                audio_path, video_info = self.downloader_registry.download(
                    url=url,
                    output_dir=temp_dir,
                    audio_only=True
                )

                if not audio_path or not video_info:
                    self.logger.error("视频下载失败")
                    return generated_files

                self.logger.info(f"视频下载成功: {video_info.title}")

                # 2. 转录音频
                self.logger.info("正在转录音频...")
                transcript = self.transcriber.transcribe(
                    audio_path=audio_path,
                    model_name=self.settings.whisper_model,
                    language="zh"
                )

                if not transcript:
                    self.logger.error("音频转录失败")
                    return generated_files

                self.logger.info(f"转录完成，文本长度: {len(transcript)} 字符")

            # 3. 保存原始转录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_file = self._save_original_note(
                video_info=video_info,
                transcript=transcript,
                timestamp=timestamp
            )
            generated_files.append(original_file)

            # 4. 整理内容
            self.logger.info("正在整理内容...")
            organized_content = self.ai_processor.organize_long_content(
                content=transcript,
                chunk_size=self.settings.content_chunk_size
            )

            organized_file = self._save_organized_note(
                video_info=video_info,
                content=organized_content,
                timestamp=timestamp
            )
            generated_files.append(organized_file)

            # 5. 生成小红书版本
            if generate_xiaohongshu:
                self.logger.info("正在生成小红书版本...")
                xiaohongshu_file = self._generate_xiaohongshu_note(
                    content=organized_content,
                    timestamp=timestamp
                )
                if xiaohongshu_file:
                    generated_files.append(xiaohongshu_file)

            # 6. 生成博客文章
            if generate_blog:
                self.logger.info("正在生成博客文章...")
                blog_file = self._generate_blog_note(
                    content=organized_content,
                    video_info=video_info,
                    timestamp=timestamp
                )
                if blog_file:
                    generated_files.append(blog_file)

            self.logger.info(f"处理完成，共生成 {len(generated_files)} 个文件")
            return generated_files

        except Exception as e:
            self.logger.error(f"处理视频时出错: {e}", exc_info=True)
            return generated_files

        finally:
            # 清理临时文件
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _save_original_note(
        self,
        video_info: VideoInfo,
        transcript: str,
        timestamp: str
    ) -> Path:
        """保存原始笔记"""
        file_path = self.settings.output_dir / f"{timestamp}_original.md"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {video_info.title}\n\n")
            f.write(f"## 视频信息\n")
            f.write(f"- 作者：{video_info.uploader}\n")
            f.write(f"- 时长：{video_info.duration}秒\n")
            f.write(f"- 平台：{video_info.platform}\n")
            f.write(f"- 链接：{video_info.url}\n\n")
            f.write(f"## 原始转录内容\n\n")
            f.write(transcript)

        self.logger.info(f"原始笔记已保存: {file_path}")
        return file_path

    def _save_organized_note(
        self,
        video_info: VideoInfo,
        content: str,
        timestamp: str
    ) -> Path:
        """保存整理版笔记"""
        file_path = self.settings.output_dir / f"{timestamp}_organized.md"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {video_info.title} - 整理版\n\n")
            f.write(f"## 视频信息\n")
            f.write(f"- 作者：{video_info.uploader}\n")
            f.write(f"- 时长：{video_info.duration}秒\n")
            f.write(f"- 平台：{video_info.platform}\n")
            f.write(f"- 链接：{video_info.url}\n\n")
            f.write(f"## 内容整理\n\n")
            f.write(content)

        self.logger.info(f"整理版笔记已保存: {file_path}")
        return file_path

    def _generate_xiaohongshu_note(
        self,
        content: str,
        timestamp: str
    ) -> Optional[Path]:
        """生成小红书笔记"""
        try:
            # 生成小红书内容
            xiaohongshu_content, titles, tags = self.xiaohongshu_generator.generate(
                content=content,
                max_tokens=self.settings.max_tokens
            )

            # 获取图片（使用视频原始内容提取关键词）
            images = []
            if self.image_service:
                images = self.image_service.get_photos_for_xiaohongshu(
                    titles=titles,
                    tags=tags,
                    count=3,
                    ai_processor=self.ai_processor,
                    content=content  # 传入原始内容，用于提取图片关键词
                )

            # 格式化并保存
            if titles:
                formatted_content = self.xiaohongshu_generator.format_note(
                    content=xiaohongshu_content,
                    title=titles[0],
                    tags=tags,
                    images=images
                )

                file_path = self.settings.output_dir / f"{timestamp}_xiaohongshu.md"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(formatted_content)

                self.logger.info(f"小红书笔记已保存: {file_path}")
                return file_path

            return None

        except Exception as e:
            self.logger.error(f"生成小红书笔记失败: {e}", exc_info=True)
            return None

    def _generate_blog_note(
        self,
        content: str,
        video_info: VideoInfo,
        timestamp: str
    ) -> Optional[Path]:
        """生成博客文章"""
        try:
            # 准备视频信息
            video_info_dict = {
                'title': video_info.title,
                'uploader': video_info.uploader,
                'url': video_info.url,
                'platform': video_info.platform,
                'timestamp': timestamp
            }

            # 生成博客内容
            blog_content = self.blog_generator.generate(
                content=content,
                video_info=video_info_dict,
                max_tokens=16000  # 博客要完整呈现所有内容，不受长度限制
            )

            if blog_content:
                # 格式化博客（添加元信息）
                formatted_blog = self.blog_generator.format_blog(
                    content=blog_content,
                    video_info=video_info_dict
                )

                # 保存博客文件
                file_path = self.settings.output_dir / f"{timestamp}_blog.md"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(formatted_blog)

                self.logger.info(f"博客文章已保存: {file_path}")
                return file_path

            return None

        except Exception as e:
            self.logger.error(f"生成博客文章失败: {e}", exc_info=True)
            return None

    def _get_video_info_without_download(self, url: str) -> Optional[VideoInfo]:
        """
        获取视频信息（不下载视频）

        使用yt-dlp的extract_info(download=False)来获取视频元数据

        Args:
            url: 视频URL

        Returns:
            VideoInfo对象，如果获取失败返回None
        """
        try:
            import yt_dlp

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info:
                    # 判断平台
                    platform = "未知"
                    if 'youtube.com' in url or 'youtu.be' in url:
                        platform = "YouTube"
                    elif 'bilibili.com' in url:
                        platform = "Bilibili"
                    elif 'tiktok.com' in url:
                        platform = "TikTok"

                    return VideoInfo(
                        title=info.get('title', '未知标题'),
                        duration=info.get('duration', 0),
                        uploader=info.get('uploader', '未知'),
                        description=info.get('description', ''),
                        platform=platform,
                        url=url
                    )
        except Exception as e:
            self.logger.warning(f"获取视频信息失败: {e}")
            return None

    def process_multiple_videos(
        self,
        urls: List[str],
        generate_xiaohongshu: bool = True
    ) -> dict:
        """
        批量处理视频

        Args:
            urls: 视频URL列表
            generate_xiaohongshu: 是否生成小红书版本

        Returns:
            处理结果字典 {url: [生成的文件列表]}
        """
        results = {}
        total = len(urls)

        for i, url in enumerate(urls, 1):
            self.logger.info(f"处理第 {i}/{total} 个视频")
            try:
                files = self.process_video(url, generate_xiaohongshu)
                results[url] = files
            except Exception as e:
                self.logger.error(f"处理视频失败: {url}, 错误: {e}")
                results[url] = []

        return results
