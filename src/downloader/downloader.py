import os
import subprocess
import time
from typing import Optional, Tuple, Dict

import httpx
import yt_dlp

from src.downloader.error import DownloadError
from src.logger import app_logger


def download_video(platform_type: str, url: str, temp_dir: str) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """Download video and get file path & info"""
    try:
        if not platform_type:
            raise DownloadError("不支持的视频平台", "unknown", "platform_error")
        # Basic download options
        options = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'quiet': True,
            'no_warnings': True,
        }

        # Download Video
        for attempt in range(3):  # 最多重试3次
            try:
                with yt_dlp.YoutubeDL(options) as ydl:
                    app_logger.info(f"正在尝试下载（第{attempt + 1}次）...")
                    info = ydl.extract_info(url, download=True)
                    if not info:
                        raise DownloadError("无法获取视频信息", platform_type, "info_error")

                    # 找到下载的音频文件
                    downloaded_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp3')]
                    if not downloaded_files:
                        raise DownloadError("未找到下载的音频文件", platform_type, "file_error")

                    audio_path = os.path.join(temp_dir, downloaded_files[0])
                    if not os.path.exists(audio_path):
                        raise DownloadError("音频文件不存在", platform_type, "file_error")

                    video_info = {
                        'title': info.get('title', '未知标题'),
                        'uploader': info.get('uploader', '未知作者'),
                        'description': info.get('description', ''),
                        'duration': info.get('duration', 0),
                        'platform': platform_type
                    }

                    app_logger.info(f"✅ {platform_type}视频下载成功")
                    return audio_path, video_info

            except Exception as e:
                app_logger.warning(f"⚠️ 下载失败（第{attempt + 1}次）: {str(e)}")
                if attempt < 2:  # 如果不是最后一次尝试
                    app_logger.warning("等待5秒后重试...")
                    time.sleep(5)
                else:
                    raise  # 最后一次失败，抛出异常
    except Exception as e:
        error_msg = _handle_download_error(e, platform_type, url)
        app_logger.error(f"⚠️ {error_msg}")
        return None, None


def _get_alternative_download_method(platform: str, url: str) -> Optional[str]:
    """Get alternative download type"""
    if platform == 'youtube':
        return 'pytube'
    elif platform == 'douyin':
        return 'requests'
    elif platform == 'bilibili':
        return 'you-get'
    return None

def download_with_alternative_method(url: str, temp_dir: str, method: str) -> Optional[str]:
    """Use alternative method download"""
    try:
        if method == 'you-get':
            cmd = ['you-get', '--no-proxy', '--no-check-certificate', '-o', temp_dir, url]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # 查找下载的文件
                files = [f for f in os.listdir(temp_dir) if f.endswith(('.mp4', '.flv', '.webm'))]
                if files:
                    return os.path.join(temp_dir, files[0])
            raise Exception(result.stderr)

        elif method == 'requests':
            # 使用requests直接下载
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            # 首先获取页面内容
            response = httpx.get(url, headers=headers, verify=False)

            if response.status_code == 200:
                # 尝试从页面中提取视频URL
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                video_url = None
                # 查找video标签
                video_tags = soup.find_all('video')
                for video in video_tags:
                    src = video.get('src') or video.get('data-src')
                    if src:
                        video_url = src
                        break

                if not video_url:
                    # 尝试查找其他可能包含视频URL的元素
                    import re
                    video_patterns = [
                        r'https?://[^"\'\s]+\.(?:mp4|m3u8)[^"\'\s]*',
                        r'playAddr":"([^"]+)"',
                        r'play_url":"([^"]+)"'
                    ]
                    for pattern in video_patterns:
                        matches = re.findall(pattern, response.text)
                        if matches:
                            video_url = matches[0]
                            break

                if video_url:
                    if not video_url.startswith('http'):
                        video_url = 'https:' + video_url if video_url.startswith('//') else video_url

                    # 下载视频
                    video_response = httpx.get(video_url, headers=headers, stream=True, verify=False)
                    if video_response.status_code == 200:
                        file_path = os.path.join(temp_dir, 'video.mp4')
                        with open(file_path, 'wb') as f:
                            for chunk in video_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        return file_path

                raise Exception(f"无法下载视频: HTTP {video_response.status_code}")
            raise Exception(f"无法访问页面: HTTP {response.status_code}")

        elif method == 'pytube':
            # 禁用SSL验证
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context

            from pytube import YouTube
            yt = YouTube(url)
            # 获取最高质量的MP4格式视频
            video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            if video:
                return video.download(output_path=temp_dir)
            raise Exception("未找到合适的视频流")

    except Exception as e:
        print(f"备用下载方法 {method} 失败: {str(e)}")
        return None

def download_image(url: str, output_file_path: str) -> str:
    """
    下载图片
    """
    try:
        response = httpx.get(url, verify=False)
        if response.status_code == 200:
            with open(output_file_path, 'wb') as f:
                f.write(response.content)
            return output_file_path
    except Exception as e:
        print(f"下载图片失败: {str(e)}")
        return None


def _handle_download_error(error: Exception, platform: str, url: str) -> str:
    """
    处理下载错误并返回用户友好的错误消息

    Args:
        error: 异常对象
        platform: 平台名称
        url: 视频URL

    Returns:
        str: 用户友好的错误消息
    """
    error_msg = str(error)

    if "SSL" in error_msg:
        return "⚠️ SSL证书验证失败，请检查网络连接"
    elif "cookies" in error_msg.lower():
        return f"⚠️ {platform}访问被拒绝，可能需要更新cookie或更换IP地址"
    elif "404" in error_msg:
        return "⚠️ 视频不存在或已被删除"
    elif "403" in error_msg:
        return "⚠️ 访问被拒绝，可能需要登录或更换IP地址"
    elif "unavailable" in error_msg.lower():
        return "⚠️ 视频当前不可用，可能是地区限制或版权问题"
    else:
        return f"⚠️ 下载失败: {error_msg}"