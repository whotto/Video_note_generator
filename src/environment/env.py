import ssl
from dotenv import load_dotenv
import os

from src.setting.setting import global_setting


class Environment(object):
    def __init__(self, model_name):
        self.openrouter_ai_model = model_name
        # OpenRouter configuration
        self.openrouter_api_key = global_setting['openrouter_api_key']
        self.openrouter_api_url = global_setting['openrouter_api_url']
        self.openrouter_app_name = global_setting['openrouter_app_name']
        self.openrouter_http_referer = global_setting['openrouter_http_referer']
        self.openrouter_available = False

        # Unsplash configuration
        self.unsplash_access_key = global_setting['unsplash_access_key']
        self.unsplash_secret_key = global_setting['unsplash_secret_key']
        self.unsplash_redirect_uri = global_setting['unsplash_redirect_uri']
        self.unsplash_available = False

    @classmethod
    def config_proxy(cls):
        if global_setting['http_proxy']:
            os.environ['HTTP_PROXY'] = global_setting['http_proxy']
        if global_setting['https_proxy']:
            os.environ['HTTPS_PROXY'] = global_setting['https_proxy']

    @classmethod
    def disabled_ssl_verify(cls):
        ssl._create_default_https_context = ssl._create_unverified_context