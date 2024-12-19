from typing import List

import httpx

from src.environment.env import Environment
from unsplash.api import Api as UnsplashApi
from unsplash.auth import Auth as UnsplashAuth

from src.logger import app_logger


class UnsplashAdapter:
    def __init__(self, env: Environment):
        self.unsplash_client = None
        self.unsplash_available = False
        self.unsplash_access_key = env.unsplash_access_key

        if env.unsplash_access_key:
            auth = UnsplashAuth(
                client_id=env.unsplash_access_key,
                client_secret=None,
                redirect_uri=None
            )
            try:
                unsplash_client = UnsplashApi(auth)
                self.unsplash_client = unsplash_client
                self.unsplash_available = True
                app_logger.info("✅ Unsplash API 配置成功")
            except Exception as e:
                app_logger.error(f"❌ Failed to initialize Unsplash client: {str(e)}")
                self.unsplash_available = False
        else:
            app_logger.warning("⚠️ 未设置 Unsplash API 密钥")
            self.unsplash_available = False

    def get_images(self, query: str, count: int = 3) -> List[str]:
        if not self.unsplash_available:
            app_logger.warning("⚠️ Unsplash API 不可用")
            return []

        try:
            headers = {
                'Authorization': f'Client-ID {self.unsplash_access_key}'
            }
            # Query each keyword
            all_photos = []
            for keyword in query.split(','):
                response = httpx.get(
                    'https://api.unsplash.com/search/photos',
                    params={
                        'query': keyword.strip(),
                        'per_page': count,
                        'orientation': 'portrait',  # 小红书偏好竖版图片
                        'content_filter': 'high'  # 只返回高质量图片
                    },
                    headers=headers,
                    verify=False  # 禁用SSL验证
                )

                if response.status_code == 200:
                    data = response.json()
                    if data['results']:
                        # 获取图片URL，优先使用regular尺寸
                        photos = [photo['urls'].get('regular', photo['urls']['small'])
                                  for photo in data['results']]
                        all_photos.extend(photos)

            # 如果收集到的图片不够，用最后一个关键词继续搜索
            while len(all_photos) < count and query:
                response = httpx.get(
                    'https://api.unsplash.com/search/photos',
                    params={
                        'query': query.split(',')[-1].strip(),
                        'per_page': count - len(all_photos),
                        'orientation': 'portrait',
                        'content_filter': 'high',
                        'page': 2  # 获取下一页的结果
                    },
                    headers=headers,
                    verify=False
                )

                if response.status_code == 200:
                    data = response.json()
                    if data['results']:
                        photos = [photo['urls'].get('regular', photo['urls']['small'])
                                  for photo in data['results']]
                        all_photos.extend(photos)
                    else:
                        break
                else:
                    break

            # 返回指定数量的图片
            return all_photos[:count]

        except Exception as e:
            app_logger.error(f"⚠️ 获取图片失败: {str(e)}")
            return []