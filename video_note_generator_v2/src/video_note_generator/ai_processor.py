"""
AI 内容处理模块

使用 OpenRouter 进行内容生成和优化
"""
from typing import Optional, List
import logging
from openai import OpenAI

from .utils.text_utils import split_content


class AIProcessor:
    """AI 内容处理器"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "google/gemini-pro",
        app_name: str = "video_note_generator",
        http_referer: str = "https://github.com",
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化 AI 处理器

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model: 使用的模型名称
            app_name: 应用名称
            http_referer: HTTP Referer
            logger: 日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)
        self.model = model

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": http_referer,
                "X-Title": app_name,
            }
        )

        # 测试连接
        self._test_connection()

    def _test_connection(self) -> bool:
        """
        测试 API 连接

        Returns:
            连接是否成功
        """
        try:
            self.logger.info("正在测试 OpenRouter API 连接...")
            self.client.models.list()
            self.logger.info("OpenRouter API 连接成功")
            return True
        except Exception as e:
            self.logger.warning(f"OpenRouter API 连接测试失败: {e}")
            self.logger.warning("将继续尝试使用 API，但可能会遇到问题")
            return False

    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Optional[str]:
        """
        生成内容

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            生成的内容
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            if response.choices:
                return response.choices[0].message.content.strip()

            return None

        except Exception as e:
            self.logger.error(f"AI 生成失败: {e}")
            return None

    def organize_content(self, content: str) -> str:
        """
        整理内容为结构化文章

        Args:
            content: 原始内容

        Returns:
            整理后的内容
        """
        system_prompt = """你是一位著名的科普作家和博客作者，著作等身，屡获殊荣，尤其在内容创作领域有深厚的造诣。

请使用 4C 模型（建立联系 Connection、展示冲突 Conflict、强调改变 Change、即时收获 Catch）为转录的文字内容创建结构。

写作要求：
- 从用户的问题出发，引导读者理解核心概念及其背景
- 使用第二人称与读者对话，语气亲切平实
- 确保所有观点和内容基于用户提供的转录文本
- 如无具体实例，则不编造
- 涉及复杂逻辑时，使用直观类比
- 避免内容重复冗余
- 逻辑递进清晰，从问题开始，逐步深入

Markdown格式要求：
- 大标题突出主题，吸引眼球，最好使用疑问句
- 小标题简洁有力，结构清晰，尽量使用单词或短语
- 直入主题，在第一部分清晰阐述问题和需求
- 正文使用自然段，避免使用列表形式
- 内容翔实，避免过度简略，特别注意保留原文中的数据和示例信息
- 如有来源URL，使用文内链接形式
- 保留原文中的Markdown格式图片链接"""

        user_prompt = f"""请根据以下转录文字内容，创作一篇结构清晰、易于理解的博客文章。

转录文字内容：

{content}"""

        result = self.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=4000
        )

        return result if result else content

    def organize_long_content(
        self,
        content: str,
        chunk_size: int = 2000
    ) -> str:
        """
        整理长内容（分块处理）

        Args:
            content: 原始内容
            chunk_size: 分块大小

        Returns:
            整理后的内容
        """
        if not content or not content.strip():
            return ""

        # 分割内容
        chunks = split_content(content, max_chars=chunk_size)
        organized_chunks = []

        self.logger.info(f"内容将分为 {len(chunks)} 个部分进行处理")

        for i, chunk in enumerate(chunks, 1):
            self.logger.info(f"正在处理第 {i}/{len(chunks)} 部分...")
            organized_chunk = self.organize_content(chunk)
            if organized_chunk:
                organized_chunks.append(organized_chunk)

        return "\n\n".join(organized_chunks)

    def translate_to_english(self, text: str) -> Optional[str]:
        """
        将中文翻译成英文关键词

        Args:
            text: 中文文本

        Returns:
            英文关键词
        """
        system_prompt = """你是一个翻译助手。请将输入的中文关键词翻译成最相关的1-3个英文关键词，用逗号分隔。
直接返回翻译结果，不要加任何解释。

例如：
输入：'保险理财知识'
输出：insurance,finance,investment"""

        result = self.generate_completion(
            system_prompt=system_prompt,
            user_prompt=text,
            temperature=0.3,
            max_tokens=50
        )

        return result
