import re
from typing import List

from src.logger import app_logger


def extract_urls_from_text(text: str) -> list:
    """
    从文本中提取所有有效的URL
    支持的URL格式：
    - 视频平台URL (YouTube, Bilibili, 抖音等)
    - 包含http://或https://的标准URL
    - 短链接URL (如t.co等)

    Args:
        text: 输入文本

    Returns:
        list: 提取到的有效URL列表
    """
    # URL正则模式
    url_patterns = [
        # 标准URL
        r'https?://[^\s<>\[\]"\']+[^\s<>\[\]"\'.,]',
        # 短链接
        r'https?://[a-zA-Z0-9]+\.[a-zA-Z]{2,3}/[^\s<>\[\]"\']+',
        # Bilibili
        r'BV[a-zA-Z0-9]{10}',
        # 抖音分享链接
        r'v\.douyin\.com/[a-zA-Z0-9]+',
    ]

    urls = []
    for pattern in url_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            url = match.group()
            # 对于不完整的BV号，添加完整的bilibili前缀
            if url.startswith('BV'):
                url = f'https://www.bilibili.com/video/{url}'
            urls.append(url)

    # 去重并保持顺序
    seen = set()
    return [url for url in urls if not (url in seen or seen.add(url))]

def process_markdown_file(self, input_file: str) -> List[str]:
    """处理markdown文件，生成优化后的笔记

    Args:
        input_file (str): 输入的markdown文件路径
    """
    try:
        # 读取markdown文件
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取视频链接
        video_links = re.findall(
            r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|bilibili\.com/video/|douyin\.com/video/)[^\s\)]+',
            content)

        if not video_links:
            app_logger.error("未在markdown文件中找到视频链接")
            return []

        app_logger.info(f"找到 {len(video_links)} 个视频链接，开始处理...\n")

        # 处理每个视频链接
        urls = []
        for i, url in enumerate(video_links, 1):
            print(f"处理第 {i}/{len(video_links)} 个视频: {url}\n")
            # append to urls
            urls.append(url)

        seen = set()
        return [url for url in urls if not (url in seen or seen.add(url))]

    except Exception as e:
        app_logger.error(f"处理markdown文件时出错: {str(e)}")
        return []