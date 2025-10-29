"""
Video Note Generator V2

A modular video note generation tool with multi-platform support
"""

__version__ = "2.0.0"
__author__ = "Your Name"
__email__ = "grow8org@gmail.com"

from .config import get_settings, Settings
from .processor import VideoNoteProcessor
from .downloader import VideoInfo, DownloadError
from .transcriber import WhisperTranscriber
from .ai_processor import AIProcessor
from .utils.logger import setup_logger

__all__ = [
    "get_settings",
    "Settings",
    "VideoNoteProcessor",
    "VideoInfo",
    "DownloadError",
    "WhisperTranscriber",
    "AIProcessor",
    "setup_logger",
]
