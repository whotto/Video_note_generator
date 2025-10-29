"""
日志系统模块

提供结构化的日志功能，支持文件和控制台输出
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'

    def format(self, record):
        # 为日志级别添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


class Logger:
    """日志管理器"""

    _instance: Optional['Logger'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._loggers = {}

    def setup(
        self,
        name: str = "video_note_generator",
        log_dir: Path = Path("logs"),
        log_level: str = "INFO",
        console_output: bool = True,
        file_output: bool = True,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """
        设置日志记录器

        Args:
            name: 日志记录器名称
            log_dir: 日志文件目录
            log_level: 日志级别
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            max_bytes: 单个日志文件最大字节数
            backup_count: 日志文件备份数量

        Returns:
            配置好的日志记录器
        """
        # 如果已经设置过，直接返回
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.propagate = False

        # 清除已有的处理器
        logger.handlers.clear()

        # 日志格式
        detailed_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        simple_format = '%(asctime)s - %(levelname)s - %(message)s'

        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level.upper()))
            console_formatter = ColoredFormatter(
                simple_format,
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        # 文件处理器
        if file_output:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)

            # 详细日志文件（所有级别）
            timestamp = datetime.now().strftime('%Y%m%d')
            log_file = log_dir / f"{name}_{timestamp}.log"

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                detailed_format,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            # 错误日志文件（仅ERROR及以上）
            error_log_file = log_dir / f"{name}_error_{timestamp}.log"
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            logger.addHandler(error_handler)

        self._loggers[name] = logger
        return logger

    def get_logger(self, name: str = "video_note_generator") -> logging.Logger:
        """
        获取日志记录器

        Args:
            name: 日志记录器名称

        Returns:
            日志记录器
        """
        if name not in self._loggers:
            # 如果还没有设置，使用默认配置
            return self.setup(name)
        return self._loggers[name]


# 全局日志管理器实例
_logger_manager = Logger()


def setup_logger(
    name: str = "video_note_generator",
    log_dir: Path = Path("logs"),
    log_level: str = "INFO",
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    设置日志记录器（便捷函数）

    Args:
        name: 日志记录器名称
        log_dir: 日志文件目录
        log_level: 日志级别
        console_output: 是否输出到控制台
        file_output: 是否输出到文件

    Returns:
        配置好的日志记录器
    """
    return _logger_manager.setup(
        name=name,
        log_dir=log_dir,
        log_level=log_level,
        console_output=console_output,
        file_output=file_output
    )


def get_logger(name: str = "video_note_generator") -> logging.Logger:
    """
    获取日志记录器（便捷函数）

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return _logger_manager.get_logger(name)
