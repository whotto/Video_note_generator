"""
字幕提取器

支持从各平台提取官方字幕，避免不必要的下载和转录
"""
import re
import requests
from typing import Optional, Dict, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SubtitleExtractor:
    """字幕提取器基类"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

    def extract(self, url: str) -> Optional[str]:
        """
        从URL提取字幕

        Args:
            url: 视频URL

        Returns:
            字幕文本，如果没有字幕返回None
        """
        # 判断平台并调用对应方法
        if 'youtube.com' in url or 'youtu.be' in url:
            return self._extract_youtube(url)
        elif 'bilibili.com' in url:
            return self._extract_bilibili(url)
        elif 'tiktok.com' in url:
            return self._extract_tiktok(url)
        else:
            return None

    def _extract_youtube(self, url: str) -> Optional[str]:
        """
        提取YouTube字幕

        使用yt-dlp提取字幕，不下载视频
        """
        try:
            import yt_dlp

            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['zh-Hans', 'zh-Hant', 'zh', 'en'],
                'subtitlesformat': 'json3',
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("尝试提取YouTube字幕...")
                info = ydl.extract_info(url, download=False)

                # 优先使用官方字幕
                subtitles = info.get('subtitles', {})
                if not subtitles:
                    # 使用自动生成字幕
                    subtitles = info.get('automatic_captions', {})

                if subtitles:
                    # 按优先级选择语言
                    for lang in ['zh-Hans', 'zh-Hant', 'zh', 'en']:
                        if lang in subtitles:
                            subtitle_data = subtitles[lang]
                            # 选择json3格式
                            for fmt in subtitle_data:
                                if fmt.get('ext') == 'json3':
                                    subtitle_url = fmt['url']
                                    return self._download_and_parse_json3(subtitle_url)

                    # 如果没有json3，尝试其他格式
                    first_lang = list(subtitles.keys())[0]
                    if subtitles[first_lang]:
                        subtitle_url = subtitles[first_lang][0]['url']
                        return self._download_and_parse_subtitle(subtitle_url)

                logger.info("该YouTube视频没有字幕")
                return None

        except Exception as e:
            logger.warning(f"YouTube字幕提取失败: {e}")
            return None

    def _extract_bilibili(self, url: str) -> Optional[str]:
        """
        提取Bilibili字幕

        使用B站API直接获取字幕
        """
        try:
            # 提取BV号
            bv_match = re.search(r'BV[\w]+', url)
            if not bv_match:
                return None

            bvid = bv_match.group(0)
            logger.info(f"提取Bilibili字幕: {bvid}")

            # 1. 获取cid
            api = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            response = requests.get(api, headers=self.headers, timeout=10)
            data = response.json()

            if data['code'] != 0:
                return None

            cid = data['data']['cid']

            # 2. 获取字幕列表
            subtitle_api = f"https://api.bilibili.com/x/player/wbi/v2?cid={cid}&bvid={bvid}"
            response = requests.get(subtitle_api, headers=self.headers, timeout=10)
            data = response.json()

            if data['code'] != 0:
                return None

            subtitle_info = data['data'].get('subtitle', {})
            subtitles = subtitle_info.get('subtitles', [])

            if not subtitles:
                logger.info("该B站视频没有字幕")
                return None

            # 3. 下载第一个字幕
            subtitle_url = subtitles[0]['subtitle_url']
            if not subtitle_url.startswith('http'):
                subtitle_url = 'https:' + subtitle_url

            response = requests.get(subtitle_url, timeout=10)
            subtitle_data = response.json()

            # 4. 解析字幕
            body = subtitle_data.get('body', [])
            if body:
                text_parts = [item.get('content', '') for item in body]
                subtitle_text = ' '.join(text_parts)
                logger.info(f"✅ 成功提取B站字幕（{len(body)}条）")
                return subtitle_text

            return None

        except Exception as e:
            logger.warning(f"Bilibili字幕提取失败: {e}")
            return None

    def _extract_tiktok(self, url: str) -> Optional[str]:
        """
        提取TikTok字幕

        TikTok通常没有官方字幕，返回None
        """
        logger.info("TikTok视频通常没有字幕")
        return None

    def _download_and_parse_json3(self, url: str) -> str:
        """下载并解析json3格式字幕"""
        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            # json3格式: {"events": [{"segs": [{"utf8": "text"}]}]}
            text_parts = []
            for event in data.get('events', []):
                for seg in event.get('segs', []):
                    text = seg.get('utf8', '')
                    if text and text != '\n':
                        text_parts.append(text)

            subtitle_text = ' '.join(text_parts)
            logger.info(f"✅ 成功提取YouTube字幕（{len(text_parts)}段）")
            return subtitle_text

        except Exception as e:
            logger.error(f"解析json3字幕失败: {e}")
            return ""

    def _download_and_parse_subtitle(self, url: str) -> str:
        """下载并解析通用字幕格式"""
        try:
            response = requests.get(url, timeout=10)
            content = response.text

            # 简单解析：移除时间戳等标记
            # 支持SRT、VTT等格式
            lines = content.split('\n')
            text_parts = []

            for line in lines:
                line = line.strip()
                # 跳过空行、数字行、时间戳行
                if not line or line.isdigit() or '-->' in line or line.startswith('WEBVTT'):
                    continue
                text_parts.append(line)

            return ' '.join(text_parts)

        except Exception as e:
            logger.error(f"解析字幕失败: {e}")
            return ""
