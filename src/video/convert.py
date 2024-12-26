import datetime
import os
import re
import shutil
import urllib
from tkinter import Listbox
from typing import List, Tuple, Any

import openai
import whisper

from src.adapter.openrouter import OpenRouterAdapter
from src.adapter.unsplash import UnsplashAdapter
from src.downloader.downloader import download_video, download_image
from src.logger import app_logger
from src.platform.platfrom import Platform
from src.video.audio import extract_audio_to_mp3
from src.video.prompt import share_prompt


class VideoNoteGenerator:
    def __init__(self, output_dir: str = "temp_notes",
                 openrouter_adapter: OpenRouterAdapter = None,
                 unsplash_adapter: UnsplashAdapter = None,
                 ffmpeg_path: str = None):
        self.output_dir = output_dir

        self.openrouter_adapter = openrouter_adapter
        self.unsplash_adapter = unsplash_adapter
        self.ffmpeg_path = ffmpeg_path
        self.platform = Platform()
        self.whisper_model = None

    async def process_video_full(self, url: str) -> Tuple[str, str, str, str, List[str]]:
        app_logger.info('📹 [完整流程]开始处理视频...')
        # Create temporary folder
        temp_dir = os.path.join(self.output_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Determine platform
        platform = Platform()
        platform.detect(url)

        try:
            app_logger.info('⬇️ 正在下载视频...')
            result = download_video(platform_type=platform.type, url=url, temp_dir=temp_dir)
            if not result:
                app_logger.warning(f"⚠️ 视频下载失败，返回为空: {url}")
                return '⚠️ 视频下载失败', '', '', '', []

            audio_path, video_info = result
            if not audio_path or not video_info:
                app_logger.warning(f"⚠️ 视频下载失败，音轨或视频信息返回为空: {url}")
                return '⚠️ 视频下载失败，音轨或视频信息返回为空', '', '', '', []

            app_logger.info(f"✅ 视频下载成功: {video_info['title']}")

            return await self.process_video_path(audio_path, temp_dir)
        finally:
            # Clear temporary files
            app_logger.info('🗑️ 正在清理临时文件...')
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    async def process_video_organized(self, content: bytes) -> Tuple[str, str, str, str, List[str]]:
        try:
            content_str = content.decode('utf-8')
            if not content_str:
                content_str = content.decode('gbk')
            rednote_content, images = await self.gen_rednote_version(content_str)
            return '✅ 处理成功', '-', content_str, rednote_content, images
        except Exception as e:
            app_logger.error(f"⚠️ 视频处理失败: {str(e)}")
            return '⚠️ 视频处理失败', '', '', '', []

    async def process_video_path(self, file_path: str, temp_dir: str) -> Tuple[str, str, str, str, List[str]]:
        try:
            # create temp audio file use file_path last path without extension
            audio_path = os.path.join(temp_dir, os.path.basename(file_path).split('.')[0] + '.mp3')
            extract_audio_to_mp3(file_path, audio_path)

            # Transcribe audio
            app_logger.info('🎙️ 正在转录音频...')
            app_logger.info('⚠️ 注意：转录音频可能需要几分钟时间，请耐心等待...')
            transcript = self._transcribe_audio(audio_path)
            if not transcript:
                app_logger.warning(f"⚠️ 音频转录失败，返回为空")
                return '⚠️ 音频转录失败', '', '', '', []

            # Organize long content
            app_logger.info('📝 正在整理长文版本...')
            organized_content = await self._organize_long_content(transcript)

            return await self.process_video_organized(organized_content.encode('utf-8'))
        except Exception as e:
            app_logger.error(f"⚠️ 视频处理失败: {str(e)}")
            return '⚠️ 视频处理失败', '', '', '', []

    def load_whisper_model(self):
        """加载Whisper模型"""
        app_logger.info("Initializing Whisper model...")
        self.whisper_model = None
        try:
            self.whisper_model = whisper.load_model("medium", download_root=".")
            app_logger.info("✅ Whisper model loaded successfully")
        except Exception as e:
            app_logger.warning(f"⚠️ Whisper model loading failed: {str(e)}")
            app_logger.info("Will retry loading later...")

    async def gen_rednote_version(self, organized_content: str) -> Tuple[str, List[str]]:
        """Generate rednote version"""
        app_logger.info('📝 正在整理小红书风格笔记...')
        try:
            rednote_content, titles, tags, images = await self._convert_to_xiaohongshu(organized_content)
            # 全文
            full_content = f"# {titles[0]}\n\n{rednote_content}\n\n---\n"
            full_content = full_content + "\n".join([f"#{tag}" for tag in tags])
            return full_content, images
        except Exception as e:
            app_logger.error(f"❌ 生成小红书风格笔记失败: {e}")
            import traceback
            print(f"错误详情:\n{traceback.format_exc()}")
            return '', []

    def _transcribe_audio(self, audio_path: str, language: str = 'zh', prompt: str = '以下是一段视频的转录内容。请用流畅的中文输出。') -> str:
        """Transcribe audio use Whisper"""
        try:
            self._ensure_whisper_model()
            if not self.whisper_model:
                raise Exception("Whisper model not available")
            app_logger.info('正在转录音频（这可能需要几分钟）...')
            result = self.whisper_model.transcribe(
                audio_path,
                language=language,
                task='transcribe',
                best_of=5,
                initial_prompt=prompt,
            )
            return result['text'].strip()
        except Exception as e:
            app_logger.error(f"Transcribe audio error: {e}")
            return ''


    def _ensure_whisper_model(self) -> None:
        """确保Whisper模型已加载"""
        if self.whisper_model is None:
            try:
                app_logger.info("正在加载Whisper模型...")
                self.whisper_model = whisper.load_model("medium")
                app_logger.info("✅ Whisper模型加载成功")
            except Exception as e:
                app_logger.warning(f"⚠️ Whisper模型加载失败: {str(e)}")


    async def _organize_long_content(self, content: str, duration: int = 0) -> str:
        """Use LLM to organize long content"""
        if not content.strip():
            return ""
        if not self.openrouter_adapter.api_available:
            app_logger.error("OpenRouter API not available, can't organize long content")
            return content

        content_chunks = self._split_content(content)
        organized_chunks = []
        app_logger.info(f"🤖 正在组织长内容（共{len(content_chunks)}个chunk）...")

        for i, chunk in enumerate(content_chunks, 1):
            app_logger.info(f"正在处理第 {i}/{len(content_chunks)} 部分...")
            organized_chunk = await self.openrouter_adapter.generate(
                system_prompt_type='organize_system_prompt',
                user_prompt_type='organize_user_prompt',
                content=chunk,
            )
            organized_chunks.append(organized_chunk)

        return "\n\n".join(organized_chunks)

    def _split_content(self, text: str, max_chars: int = 2000) -> List[str]:
        """按段落分割文本，保持上下文的连贯性

        特点：
        1. 保持段落完整性：不会在段落中间断开
        2. 保持句子完整性：确保句子不会被截断
        3. 添加重叠内容：每个chunk都包含上一个chunk的最后一段
        4. 智能分割：对于超长段落，按句子分割并保持完整性
        """
        if not text:
            return []

        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0
        last_paragraph = None  # 用于存储上一个chunk的最后一段

        for para in paragraphs:
            para = para.strip()
            if not para:  # 跳过空段落
                continue

            para_length = len(para)

            # 如果这是新chunk的开始，且有上一个chunk的最后一段，添加它作为上下文
            if not current_chunk and last_paragraph:
                current_chunk.append(f"上文概要：\n{last_paragraph}\n")
                current_length += len(last_paragraph) + 20  # 加上标题的长度

            # 如果单个段落就超过了最大长度，需要按句子分割
            if para_length > max_chars:
                # 如果当前块不为空，先保存
                if current_chunk:
                    last_paragraph = current_chunk[-1]
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                    if last_paragraph:
                        current_chunk.append(f"上文概要：\n{last_paragraph}\n")
                        current_length += len(last_paragraph) + 20

                # 按句子分割长段落
                sentences = re.split(r'([。！？])', para)
                current_sentence = []
                current_sentence_length = 0

                for i in range(0, len(sentences), 2):
                    sentence = sentences[i]
                    # 如果有标点符号，加上标点
                    if i + 1 < len(sentences):
                        sentence += sentences[i + 1]

                    # 如果加上这个句子会超过最大长度，保存当前块并开始新块
                    if current_sentence_length + len(sentence) > max_chars and current_sentence:
                        chunks.append(''.join(current_sentence))
                        current_sentence = [sentence]
                        current_sentence_length = len(sentence)
                    else:
                        current_sentence.append(sentence)
                        current_sentence_length += len(sentence)

                # 保存最后一个句子块
                if current_sentence:
                    chunks.append(''.join(current_sentence))
            else:
                # 如果加上这个段落会超过最大长度，保存当前块并开始新块
                if current_length + para_length > max_chars and current_chunk:
                    last_paragraph = current_chunk[-1]
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                    if last_paragraph:
                        current_chunk.append(f"上文概要：\n{last_paragraph}\n")
                        current_length += len(last_paragraph) + 20
                current_chunk.append(para)
                current_length += para_length

        # 保存最后一个块
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks



    async def _convert_to_xiaohongshu(self, content: str) -> Tuple[str, List[str], List[str], List[str]]:
        """Convert the content into a structured format for xiaohongshu. """
        try:
            xiaohongshu_content = await self.openrouter_adapter.generate(
                system_prompt_type='rednote_system_prompt',
                user_prompt_type='rednote_user_prompt',
                content=content
            )
            app_logger.info(f"✅ 小红书内容转换成功: {xiaohongshu_content[:50]}...")
            # Get title, first line...
            content_lines = xiaohongshu_content.split('\n')
            titles = []
            for line in content_lines:
                line = line.strip()
                if line and not line.startswith('#') and '：' not in line and '。' not in line:
                    titles = [line]
                    break
            if not titles:
                app_logger.info("⚠️ 未找到标题，尝试其他方式提取...")
                # 尝试其他方式提取标题
                title_match = re.search(r'^[^#\n]+', xiaohongshu_content)
                if title_match:
                    titles = [title_match.group(0).strip()]
            if titles:
                app_logger.info(f"✅ 提取到标题: {titles[0]}")
            else:
                app_logger.warning("⚠️ 未能提取到标题")

            # Get Tags, find all tag start with sharp
            tags = []
            tag_matches = re.findall(r'#([^\s#]+)', xiaohongshu_content)
            if tag_matches:
                tags = tag_matches
                app_logger.info(f"✅ 提取到{len(tags)}个标签")
            else:
                app_logger.info("⚠️ 未找到标签")

            # Get Images
            images = []
            if not self.unsplash_adapter.unsplash_available:
                app_logger.error("Unsplash is not available, cannot get images.")
                return xiaohongshu_content, titles, tags, images
            search_terms = titles + tags[:2] if tags else titles
            search_query = ' '.join(search_terms)
            # convert tags to english
            app_logger.info(f"🌐 正在翻译: {search_query}...")
            search_query = await self.openrouter_adapter.generate(
                system_prompt_type='translate_system_prompt',
                user_prompt_type=search_query,
                content=search_query,
            )
            if not search_query:
                search_query = ' '.join(search_terms)
            app_logger.info(f"🌐 正在搜索图片: {search_query}...")
            images = self.unsplash_adapter.get_images(query=search_query)
            if images:
                app_logger.info(f"✅ 提取到{len(images)}张图片")
            else:
                app_logger.warning("⚠️ 未找到图片")
            return xiaohongshu_content, titles, tags, images
        except Exception as e:
            app_logger.error(f"❌ 小红书内容转换失败: {str(e)}")
            return content, [], [], []
            
