import datetime
import logging
import os
from logging.handlers import TimedRotatingFileHandler


class Logger:
    def __init__(self, name, log_level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        # 创建日志目录
        log_dir = os.getenv('LOG_DIR', 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.log_dir = log_dir

        # 文件处理器
        now_date = datetime.datetime.now().strftime('%Y-%m-%d')
        file_handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, f'{name}-{now_date}.log'),
            when='midnight',
            backupCount=7
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
