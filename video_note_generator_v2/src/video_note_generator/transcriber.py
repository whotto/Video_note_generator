"""
音频转录服务模块

使用 Whisper 进行语音识别
"""
import hashlib
import pickle
from pathlib import Path
from typing import Optional
import logging
import whisper


class TranscriptionCache:
    """转录缓存管理器"""

    def __init__(self, cache_dir: Path):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, audio_path: str, model_name: str) -> str:
        """
        生成缓存键

        Args:
            audio_path: 音频文件路径
            model_name: 模型名称

        Returns:
            缓存键
        """
        content = f"{audio_path}:{model_name}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, audio_path: str, model_name: str) -> Optional[str]:
        """
        从缓存获取转录结果

        Args:
            audio_path: 音频文件路径
            model_name: 模型名称

        Returns:
            转录文本，如果不存在返回None
        """
        cache_key = self._get_cache_key(audio_path, model_name)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                return None
        return None

    def set(self, audio_path: str, model_name: str, text: str):
        """
        保存转录结果到缓存

        Args:
            audio_path: 音频文件路径
            model_name: 模型名称
            text: 转录文本
        """
        cache_key = self._get_cache_key(audio_path, model_name)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(text, f)
        except Exception as e:
            logging.warning(f"保存缓存失败: {e}")


class WhisperTranscriber:
    """Whisper 转录服务（单例模式）"""

    _instance: Optional['WhisperTranscriber'] = None
    _model: Optional[whisper.Whisper] = None
    _model_name: Optional[str] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        cache_dir: Optional[Path] = None
    ):
        """
        初始化转录器

        Args:
            logger: 日志记录器
            cache_dir: 缓存目录
        """
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.logger = logger or logging.getLogger(__name__)
            self.cache = TranscriptionCache(
                cache_dir or Path(".cache/transcriptions")
            )

    def _load_model(self, model_name: str = "medium") -> whisper.Whisper:
        """
        加载 Whisper 模型

        Args:
            model_name: 模型名称 (tiny/base/small/medium/large)

        Returns:
            Whisper 模型实例
        """
        if self._model is None or self._model_name != model_name:
            self.logger.info(f"正在加载 Whisper 模型: {model_name}")
            try:
                self._model = whisper.load_model(model_name)
                self._model_name = model_name
                self.logger.info(f"Whisper 模型加载成功: {model_name}")
            except Exception as e:
                self.logger.error(f"Whisper 模型加载失败: {e}")
                raise

        return self._model

    def transcribe(
        self,
        audio_path: str,
        model_name: str = "medium",
        language: str = "zh",
        use_cache: bool = True,
        **kwargs
    ) -> str:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            model_name: 模型名称
            language: 语言代码
            use_cache: 是否使用缓存
            **kwargs: 其他 Whisper 参数

        Returns:
            转录文本

        Raises:
            Exception: 转录失败时抛出异常
        """
        # 检查缓存
        if use_cache:
            cached_text = self.cache.get(audio_path, model_name)
            if cached_text:
                self.logger.info("使用缓存的转录结果")
                return cached_text

        # 加载模型
        model = self._load_model(model_name)

        # 转录
        self.logger.info(f"正在转录音频: {audio_path}")
        self.logger.info("这可能需要几分钟，请耐心等待...")

        try:
            # 默认参数
            transcribe_options = {
                'language': language,
                'task': 'transcribe',
                'best_of': 5,
                'initial_prompt': "以下是一段视频的转录内容。请用流畅的中文输出。"
            }

            # 合并用户提供的参数
            transcribe_options.update(kwargs)

            result = model.transcribe(audio_path, **transcribe_options)
            text = result["text"].strip()

            # 保存到缓存
            if use_cache and text:
                self.cache.set(audio_path, model_name, text)

            self.logger.info(f"转录完成，文本长度: {len(text)} 字符")
            return text

        except Exception as e:
            self.logger.error(f"音频转录失败: {e}")
            raise

    def get_available_models(self) -> list[str]:
        """
        获取可用的模型列表

        Returns:
            模型名称列表
        """
        return ["tiny", "base", "small", "medium", "large", "large-v2"]


def create_transcriber(
    logger: Optional[logging.Logger] = None,
    cache_dir: Optional[Path] = None
) -> WhisperTranscriber:
    """
    创建转录器实例（便捷函数）

    Args:
        logger: 日志记录器
        cache_dir: 缓存目录

    Returns:
        转录器实例
    """
    return WhisperTranscriber(logger=logger, cache_dir=cache_dir)
