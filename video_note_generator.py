# main
import os
import shutil
from typing import Tuple

from src.adapter.ffmpeg import FfmpegAdapter
from src.adapter.openrouter import OpenRouterAdapter
from src.adapter.unsplash import UnsplashAdapter
from src.environment.env import Environment
from src.logger import app_logger
from src.setting.setting import global_setting
from src.video.convert import VideoNoteGenerator


async def generate_video_note(model_name, parse_type, input_content) -> Tuple[str, str, str, str, list] or None:
    try:
        env = Environment(model_name)
        Environment.config_proxy()

        # Init open router adapter
        openrouter_adapter = OpenRouterAdapter(env)
        openrouter_adapter.connect()

        # Init adapter
        ffmpeg_adapter = FfmpegAdapter()
        unsplash_adapter = UnsplashAdapter(env=env)

        generator = None
        output_dir = global_setting['output_dir']
        os.makedirs(output_dir, exist_ok=True)

        # generate video note
        generator = VideoNoteGenerator(
            output_dir=output_dir,
            openrouter_adapter=openrouter_adapter,
            unsplash_adapter=unsplash_adapter,
            ffmpeg_path=ffmpeg_adapter.ffmpeg_path,
        )

        app_logger.info("📹 正在生成视频笔记...")

        notice = ''
        transcript_output_tran = ''
        organized_output_tran = ''
        xiaohongshu_output_tran = ''
        images = []
        # Generate video note
        if parse_type == '单URL':
            (notice, transcript_output_tran, organized_output_tran,
             xiaohongshu_output_tran, images) = await generator.process_video_full(input_content.strip())
        elif parse_type == 'MD文档':
            (notice, transcript_output_tran, organized_output_tran,
             xiaohongshu_output_tran, images) = await generator.process_video_organized(input_content.strip())
        elif parse_type == '本地视频文件':
            video_file_path = input_content
            app_logger.info("📹 本地视频文件，正在转换为视频笔记...")
            app_logger.info(f"📹 视频路径：{video_file_path}")
            # Create temporary folder
            temp_dir = os.path.join(generator.output_dir, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            (notice, transcript_output_tran, organized_output_tran,
             xiaohongshu_output_tran, images) = await generator.process_video_path(video_file_path, temp_dir)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        return notice, transcript_output_tran, organized_output_tran, xiaohongshu_output_tran, images
    except Exception as e:
        app_logger.error(f"❌ 生成视频笔记失败：{str(e)}")
        return None


# async def main():
#
#     if os.path.exists(args.input):
#         try:
#             with open(args.input, 'r', encoding='utf-8') as f:
#                 content = f.read()
#         except UnicodeDecodeError:
#             try:
#                 # 尝试使用gbk编码
#                 with open(args.input, 'r', encoding='gbk') as f:
#                     content = f.read()
#             except Exception as e:
#                 app_logger.error(f"❌ 无法读取文件: {str(e)}")
#                 sys.exit(1)
#
#         # if filename contain '_organized' and end with '.md', generate rednote directly
#         if '_organized' in args.input and args.input.endswith('.md'):
#             app_logger.info("📝 检测到文件名包含 '_organized', 将直接生成小红书笔记")
#             timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#             output_file_path = os.path.join(output_dir, f"{timestamp}_xiaohongshu.md")
#             # get organized_content from args.input
#             with open(args.input, 'r', encoding='utf-8') as f:
#                 content = f.read()
#             await generator.gen_rednote_version(content, output_file_path)
#             app_logger.info(f"📝 小红书笔记已生成：{output_file_path}")
#             sys.exit(0)
#
#         # if file name contain '.md', get urls from markdown file
#         urls = []
#         if args.input.endswith('.md'):
#             app_logger.info("📝 检测到文件名为 '.md', 将从markdown文件中获取视频链接")
#             urls = process_markdown_file(args.input)
#         else:
#             urls = extract_urls_from_text(content)
#
#         if not urls:
#             app_logger.error("❌ 未在文件中找到视频链接")
#             sys.exit(1)
#
#         # generate video note
#         app_logger.info(f"📋 从文件中找到 {len(urls)} 个URL")
#         for i, url in enumerate(urls, 1):
#             app_logger.info(f"📹 正在处理第 {i}/{len(urls)} 个视频：{url}")
#             try:
#                 await generator.process_video_full(url)
#             except Exception as e:
#                 app_logger.error(f"❌ 处理视频失败：{str(e)}")
#                 sys.exit(1)
#     else:
#         # check input
#         if not args.input.startswith(('http://', 'https://')):
#             print("⚠️ 错误：请输入有效的URL、包含URL的文件或markdown文件路径")
#             print("\n使用示例：")
#             print("1. 处理单个视频：")
#             print("   python video_note_generator.py https://example.com/video")
#             print("\n2. 处理包含URL的文件：")
#             print("   python video_note_generator.py urls.txt")
#             print("   - 文件中的URL可以是任意格式，每行一个或多个")
#             print("   - 支持带有其他文字的行")
#             print("   - 支持使用#注释")
#             print("\n3. 处理Markdown文件：")
#             print("   python video_note_generator.py notes.md")
#             sys.exit(1)
#         # generate video note
#         app_logger.info(f"📹 正在处理视频：{args.input}")
#         try:
#             await generator.process_video_full(args.input)
#         except Exception as e:
#             app_logger.error(f"❌ 处理视频失败：{str(e)}")
#             sys.exit(1)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())