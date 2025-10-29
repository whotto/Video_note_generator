"""
图片服务模块

从 Unsplash 获取相关图片
"""
from typing import Optional, List
import logging
import httpx


class UnsplashImageService:
    """Unsplash 图片服务"""

    def __init__(
        self,
        access_key: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化图片服务

        Args:
            access_key: Unsplash Access Key
            logger: 日志记录器
        """
        self.access_key = access_key
        self.logger = logger or logging.getLogger(__name__)
        self.base_url = "https://api.unsplash.com"

    def search_photos(
        self,
        query: str,
        count: int = 3,
        orientation: str = "portrait"
    ) -> List[str]:
        """
        搜索图片

        Args:
            query: 搜索关键词
            count: 返回图片数量
            orientation: 图片方向 (portrait/landscape/squarish)

        Returns:
            图片URL列表
        """
        try:
            headers = {
                'Authorization': f'Client-ID {self.access_key}'
            }

            all_photos = []

            # 对每个关键词分别搜索
            keywords = query.split(',')
            for keyword in keywords:
                keyword = keyword.strip()
                if not keyword:
                    continue

                response = httpx.get(
                    f'{self.base_url}/search/photos',
                    params={
                        'query': keyword,
                        'per_page': count,
                        'orientation': orientation,
                        'content_filter': 'high'
                    },
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    if data['results']:
                        photos = [
                            photo['urls'].get('regular', photo['urls']['small'])
                            for photo in data['results']
                        ]
                        all_photos.extend(photos)

            # 如果收集到的图片不够，用第一个关键词继续搜索
            if len(all_photos) < count and keywords:
                response = httpx.get(
                    f'{self.base_url}/search/photos',
                    params={
                        'query': keywords[0],
                        'per_page': count - len(all_photos),
                        'orientation': orientation,
                        'content_filter': 'high',
                        'page': 2
                    },
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    if data['results']:
                        photos = [
                            photo['urls'].get('regular', photo['urls']['small'])
                            for photo in data['results']
                        ]
                        all_photos.extend(photos)

            # 返回指定数量的图片
            result = all_photos[:count]
            self.logger.info(f"成功获取 {len(result)} 张图片")
            return result

        except Exception as e:
            self.logger.error(f"获取图片失败: {e}")
            return []

    def get_photos_for_xiaohongshu(
        self,
        titles: List[str] = None,
        tags: List[str] = None,
        count: int = 3,
        ai_processor = None,
        content: str = None
    ) -> List[str]:
        """
        为小红书笔记获取相关图片

        Args:
            titles: 标题列表（已弃用，保留用于向后兼容）
            tags: 标签列表（已弃用，保留用于向后兼容）
            count: 图片数量
            ai_processor: AI 处理器（用于提取关键词）
            content: 视频原始内容（优先使用）

        Returns:
            图片URL列表
        """
        search_query = None

        # 优先使用视频内容提取关键词（更准确）
        if content and ai_processor:
            try:
                self.logger.info("正在从视频内容提取图片搜索关键词...")
                search_query = ai_processor.extract_image_keywords(content)
                if search_query:
                    self.logger.info(f"使用提取的关键词搜索: {search_query}")
            except Exception as e:
                self.logger.warning(f"从内容提取关键词失败: {e}")

        # 备用方案：使用标题和标签（向后兼容）
        if not search_query:
            if titles or tags:
                self.logger.info("使用标题和标签作为搜索关键词（备用方案）")
                search_terms = []
                if titles:
                    search_terms.extend(titles[:1])  # 只用第一个标题
                if tags:
                    search_terms.extend(tags[:2])  # 只用前两个标签
                search_query = ' '.join(search_terms)

                # 翻译成英文
                if ai_processor:
                    try:
                        english_query = ai_processor.translate_to_english(search_query)
                        if english_query:
                            search_query = english_query
                            self.logger.info(f"使用翻译后的关键词: {search_query}")
                    except Exception as e:
                        self.logger.warning(f"翻译关键词失败: {e}")

        # 如果仍然没有搜索词，使用默认值
        if not search_query:
            self.logger.warning("无法生成搜索关键词，使用默认关键词")
            search_query = "abstract,creative,colorful"

        return self.search_photos(search_query, count)
