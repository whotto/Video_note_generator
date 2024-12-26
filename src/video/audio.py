import os
from moviepy.editor import VideoFileClip

from src.logger import app_logger

video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
audio_extensions = ['.mp3', '.wav', '.aac']

# Check file type
def _check_file_type(file_path):
    _, ext = os.path.splitext(file_path)
    if ext.lower() in video_extensions:
        return 'video'
    elif ext.lower() in audio_extensions:
        return 'audio'
    else:
        return 'unknown'

# Extract audio from video
def extract_audio_to_mp3(file_path, output_path) -> str:
    file_type = _check_file_type(file_path)
    if file_type == 'audio':
        return file_path
    app_logger.info(f"🎙 提取视频 {file_path} 到 \n语音 {output_path}")
    # 使用 moviepy 提取音频
    video_clip = VideoFileClip(file_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(output_path, codec='libmp3lame')
    audio_clip.close()
    video_clip.close()