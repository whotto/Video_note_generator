import os
from typing import Optional


class Platform:
    def __init__(self):
        self._init_cookie()
        self.type = None

    def detect(self, url: str):
        """
        确定视频平台

        Args:
            url: 视频URL

        Returns:
            str: 平台名称 ('youtube', 'douyin', 'bilibili') 或 None
        """
        if 'youtube.com' in url or 'youtu.be' in url:
            self.type = 'youtube'
        elif 'douyin.com' in url:
            self.type = 'douyin'
        elif 'bilibili.com' in url:
            self.type = 'bilibili'

    def _init_cookie(self):
        """Init cookie parameter"""
        self.cookie_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies')
        self.platform_cookies = {
            'douyin': os.path.join(self.cookie_dir, 'douyin_cookies.txt'),
            'bilibili': os.path.join(self.cookie_dir, 'bilibili_cookies.txt'),
            'youtube': os.path.join(self.cookie_dir, 'youtube_cookies.txt')
        }

    def _validate_cookies(self, platform: str) -> bool:
        if platform not in self.platform_cookies:
            return False
        cookie_file = self.platform_cookies[platform]
        return os.path.exists(cookie_file)

