import asyncio
from typing import Optional

import openai

from src.environment.env import Environment
from src.logger import app_logger
from src.video.prompt import share_prompt


class OpenRouterAdapter:
    def __init__(self, env: Environment):
        self.client = openai.OpenAI(
            api_key=env.openrouter_api_key,
            base_url=env.openrouter_api_url or 'https://openrouter.ai/api/v1',
            default_headers={
                "HTTP-Referer": env.openrouter_http_referer,
                "X-Title": env.openrouter_app_name
            }
        )
        self.ai_model = env.openrouter_ai_model
        self.api_available = False
        # Initialize the wait queue and flow limiter
        self.wait_queue = asyncio.Queue()
        self.flow_limiter = asyncio.Semaphore(5)  # Allow 5 requests per minute

    def connect(self):
        if self.client.api_key:
            try:
                app_logger.info(f"正在测试 OpenRouter API 连接...")
                response = self.client.models.list()
                app_logger.info("✅ OpenRouter API 连接测试成功")
                self.api_available = True
            except Exception as e:
                app_logger.error(f"❌ OpenRouter API 连接测试失败: {e}")
                app_logger.error("将继续尝试使用API，但可能会遇到问题")
                self.api_available = False

    async def generate(self, system_prompt_type, user_prompt_type, content,
                 temperature=0.7, max_tokens=4000) -> Optional[str]:
        if not self.api_available:
            app_logger.error("OpenRouter API 不可用，无法生成")
            return None

        # Wait for the flow limiter to allow the request
        await self.flow_limiter.acquire()

        try:
            system_prompt = share_prompt(prompt_type=system_prompt_type, content=content)
            user_prompt = share_prompt(prompt_type=user_prompt_type, content=content) or content
            app_logger.info('OpenRouter API 开始请求')

            # Add the request to the wait queue
            await self.wait_queue.put(None)

            # Wait for the previous requests to complete
            await asyncio.sleep(60 / 5)  # 5 requests per minute

            response = self.client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            if not response.choices:
                app_logger.error("OpenRouter API 返回结果为空")
                return None
            return response.choices[0].message.content
        except Exception as e:
            app_logger.error(f"OpenRouter API 请求失败: {e}")
            return None
        finally:
            # Release the flow limiter
            self.flow_limiter.release()
            await self.wait_queue.get()