import ssl
from dotenv import load_dotenv
import os


class Environment(object):
    def __init__(self):
        # load environment variables
        load_dotenv()
        self.__class__._env_check()

        # OpenRouter configuration
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_api_url = os.getenv('OPENROUTER_API_URL')
        self.openrouter_app_name = os.getenv('OPENROUTER_APP_NAME', 'video_note_generator')
        self.openrouter_http_referer = os.getenv('OPENROUTER_HTTP_REFERER', 'https://github.com')
        self.openrouter_ai_model = os.getenv('OPENROUTER_API_MODEL', 'google/gemini-2.0-flash-exp:free')
        self.openrouter_available = False

        # Unsplash configuration
        self.unsplash_access_key = os.getenv('UNSPLASH_ACCESS_KEY')
        self.unsplash_secret_key = os.getenv('UNSPLASH_SECRET_KEY')
        self.unsplash_redirect_uri = os.getenv('UNSPLASH_REDIRECT_URI', 'https://github.com')
        self.unsplash_available = False

    @classmethod
    def _env_check(cls):
        # check necessary environment variables
        required_env_vars = {
            'OPENROUTER_API_KEY': '用于OpenRouter API',
            'OPENROUTER_API_URL': '用于OpenRouter API',
            'OPENROUTER_APP_NAME': '用于OpenRouter API',
            'OPENROUTER_HTTP_REFERER': '用于OpenRouter API',
            'UNSPLASH_ACCESS_KEY': '用于图片搜索',
            'UNSPLASH_SECRET_KEY': '用于Unsplash认证'
        }
        missing_env_vars = []

        for key, value in required_env_vars.items():
            if not os.getenv(key):
                missing_env_vars.append(key)

        if missing_env_vars:
            print("注意：以下环境变量未设置：")
            print("\n".join(missing_env_vars))
            print("\n将使用基本功能继续运行（无AI优化和图片）。")
            print("如需完整功能，请在 .env 文件中设置相应的 API 密钥。")
            print("继续处理...\n")
            return False
        else:
            return True

    @classmethod
    def config_proxy(cls):
        if os.getenv('HTTP_PROXY'):
            http_proxy = os.getenv('HTTP_PROXY')
            https_proxy = os.getenv('HTTPS_PROXY')
            proxies = {
                'http': http_proxy,
                'https': https_proxy
            }
            return proxies
        else:
            return None

    @classmethod
    def disabled_ssl_verify(cls):
        ssl._create_default_https_context = ssl._create_unverified_context