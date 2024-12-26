import gradio as gr
from gradio_modal import Modal

from src.setting.setting import global_setting, check_required_keys, load_settings, update_and_save_settings
from video_note_generator import generate_video_note


def update_input_visibility(choice):
    return (
        gr.update(visible=(choice == "单URL")),
        # gr.update(visible=(choice == "多行URL文档")),
        gr.update(visible=(choice == "MD文档")),
        gr.update(visible=(choice == "本地视频文件"))
    )

def check_if_valid_url(content):
    if not content:
        return False
    try:
        urls = content.split('\n')
        for url in urls:
            url = url.strip()
            if not url.startswith("http") and not url.startswith("https"):
                return False
        return True
    except Exception as e:
        return False

def generate_btn_if_enabled(model_name, parse_type, url_input, md_file_input, local_video_input):
    required_keys_valid = check_required_keys()
    input_valid = (
        (parse_type == "单URL" and check_if_valid_url(url_input)) or
        (parse_type == "MD文档" and md_file_input) or
        (parse_type == "本地视频文件" and local_video_input)
    )
    return gr.Button(value="生成", interactive=(model_name and input_valid and required_keys_valid))

def main():
    with gr.Blocks(title='爆款生成器') as webui:
        local_storage = gr.BrowserState(storage_key='g_setting', default_value=global_setting, secret='asdc123')

        gr.Markdown("# 操作区")

        with gr.Row():
            model_name = gr.Textbox(label="Openrouter模型名", value="google/gemini-2.0-flash-exp:free",
                                    interactive=True)
            parse_type = gr.Radio(
                label="解析内容",
                choices=["单URL", "MD文档", "本地视频文件"],
                value="单URL", interactive=True
            )

        with gr.Group():
            url_input = gr.Textbox(label="url 名称", visible=True, interactive=True)
            md_file_input = gr.File(label="上传文档", visible=False, interactive=True, type='binary')
            local_video_input = gr.File(label="上传视频", visible=False, interactive=True, type='filepath')

        parse_type.change(
            fn=update_input_visibility,
            inputs=[parse_type],
            outputs=[url_input, md_file_input, local_video_input]
        )

        with gr.Row():
            settings_btn = gr.Button("设置")
            generate_btn = gr.Button("生成", interactive=False)

        warning_icon = gr.Markdown("⚠️ 必选参数配置缺失", visible=not check_required_keys(local_storage.value))

        # Add event listeners to update generate_btn
        model_name.change(generate_btn_if_enabled,
                          inputs=[model_name, parse_type, url_input, md_file_input, local_video_input],
                          outputs=generate_btn)
        parse_type.change(generate_btn_if_enabled,
                          inputs=[model_name, parse_type, url_input, md_file_input, local_video_input],
                          outputs=generate_btn)
        url_input.change(generate_btn_if_enabled,
                         inputs=[model_name, parse_type, url_input, md_file_input, local_video_input],
                         outputs=generate_btn)
        # file_input.change(generate_btn_if_enabled,
        #                   inputs=[model_name, parse_type, url_input, md_file_input, local_video_input],
        #                   outputs=generate_btn)
        md_file_input.change(generate_btn_if_enabled,
                             inputs=[model_name, parse_type, url_input, md_file_input, local_video_input],
                             outputs=generate_btn)
        local_video_input.change(generate_btn_if_enabled,
                                 inputs=[model_name, parse_type, url_input, md_file_input,
                                         local_video_input], outputs=generate_btn)

        with Modal(visible=False) as settings_modal:
            gr.Markdown("# 设置")

            with gr.Tabs():
                with gr.TabItem("OpenRouter设置"):
                    openrouter_api_key = gr.Textbox(label="OPENROUTER_API_KEY", interactive=True,
                                                    placeholder="Require, Fill your API key here")
                    openrouter_api_url = gr.Textbox(label="OPENROUTER_API_URL", interactive=True,
                                                    placeholder="Require, OpenRouter API URL")
                    openrouter_app_name = gr.Textbox(label="OPENROUTER_APP_NAME", interactive=True,
                                                     placeholder="Require, OpenRouter App Name")
                    openrouter_http_referer = gr.Textbox(label="OPENROUTER_HTTP_REFERER", interactive=True,
                                                         placeholder="Require, OpenRouter HTTP Referer")

                with gr.TabItem("Unsplash设置"):
                    unsplash_access_key = gr.Textbox(label="UNSPLASH_ACCESS_KEY", interactive=True,
                                                     placeholder="Unsplash Access Key")
                    unsplash_secret_key = gr.Textbox(label="UNSPLASH_SECRET_KEY", interactive=True,
                                                     placeholder="Unsplash Secret Key")
                    unsplash_redirect_uri = gr.Textbox(label="UNSPLASH_REDIRECT_URI", interactive=True,
                                                       placeholder="Unsplash Redirect URI")

                with gr.TabItem("Whisper设置"):
                    whisper_model = gr.Radio(
                        label="WHISPER_MODEL",
                        choices=["tiny", "base", "small", "medium", "large-v2"], interactive=True
                    )
                    whisper_language = gr.Radio(
                        label="WHISPER_LANGUAGE",
                        choices=["zh", "en", "ja"], interactive=True
                    )
                    ffmpeg_path = gr.Textbox(label="FFMPEG_PATH", interactive=True,
                                             placeholder="Windows 用户需要设置 FFmpeg 路径，Mac/Linux 用户通常不需要")

                with gr.TabItem("代理设置"):
                    http_proxy = gr.Textbox(label="HTTP_PROXY", interactive=True)
                    https_proxy = gr.Textbox(label="HTTPS_PROXY", interactive=True)

                with gr.TabItem("生成设置"):
                    output_dir = gr.Textbox(label="OUTPUT_DIR", interactive=True, placeholder="Output Directory")
                    max_tokens = gr.Slider(label="MAX_TOKENS", minimum=100, maximum=5000, step=100, interactive=True,
                                           info='生成小红书内容的最大长度')
                    content_chunk_size = gr.Slider(label="CONTENT_CHUNK_SIZE", minimum=100, maximum=5000, step=100,
                                                   interactive=True, info='长文本分块大小（字符数）')
                    temperature = gr.Slider(label="TEMPERATURE", minimum=0.0, maximum=1.0, step=0.1, interactive=True,
                                            info='AI 创造性程度 (0.0-1.0)')
                    top_p = gr.Slider(label="TOP_P", minimum=0.0, maximum=1.0, step=0.1, interactive=True,
                                      info='采样阈值 (0.0-1.0)')
                    use_emoji = gr.Checkbox(label="USE_EMOJI", interactive=True, info='是否在内容中使用表情符号')
                    tag_count = gr.Slider(label="TAG_COUNT", minimum=1, maximum=10, step=1, interactive=True,
                                          info='生成的标签数量')
                    min_paragraphs = gr.Slider(label="MIN_PARAGRAPHS", minimum=1, maximum=10, step=1, interactive=True,
                                               info='最少段落数')
                    max_paragraphs = gr.Slider(label="MAX_PARAGRAPHS", minimum=1, maximum=10, step=1, interactive=True,
                                               info='最多段落数')

                with gr.TabItem("调试设置"):
                    debug = gr.Checkbox(label="DEBUG", interactive=True)
                    log_level = gr.Radio(
                        label="LOG_LEVEL",
                        choices=["debug", "info", "warning", "error"], interactive=True
                    )

            confirm_btn = gr.Button("确认")

            webui.load(load_settings, inputs=[local_storage], outputs=[
                warning_icon,
                openrouter_api_key, openrouter_api_url, openrouter_app_name,
                openrouter_http_referer, unsplash_access_key, unsplash_secret_key,
                unsplash_redirect_uri, whisper_model, whisper_language,
                ffmpeg_path, http_proxy, https_proxy, output_dir,
                max_tokens, content_chunk_size, temperature,
                top_p, use_emoji, tag_count,
                min_paragraphs, max_paragraphs, debug,
                log_level,
            ])

            settings_btn.click(lambda: Modal(visible=True), None, settings_modal)

            confirm_btn.click(
                fn=update_and_save_settings,
                inputs=[
                    openrouter_api_key, openrouter_api_url, openrouter_app_name,
                    openrouter_http_referer, unsplash_access_key, unsplash_secret_key,
                    unsplash_redirect_uri, whisper_model, whisper_language,
                    ffmpeg_path, http_proxy, https_proxy, output_dir,
                    max_tokens, content_chunk_size, temperature,
                    top_p, use_emoji, tag_count,
                    min_paragraphs, max_paragraphs, debug,
                    log_level
                ],
                outputs=[warning_icon, settings_modal, local_storage]
            )

        result_status = gr.Textbox('生成中...', interactive=False, visible=False, show_label=False)
        with gr.Tabs(visible=False) as result_tabs:

            with gr.TabItem("原始笔记"):
                transcript_output = gr.Markdown(show_copy_button=True)

            with gr.TabItem("整理版笔记"):
                organized_output = gr.Markdown(show_copy_button=True)

            with gr.TabItem("小红书版本"):
                xiaohongshu_output = gr.Markdown(show_copy_button=True)
                with gr.Row():
                    note_images = gr.Gallery(label='推荐配图',
                                             show_label=False, columns=[3], rows=[1],
                                             object_fit="contain", height="auto")

        # 生成
        def on_btn_click():
            return gr.Button(interactive=False), gr.Tabs(visible=True), gr.Textbox('生成中...', interactive=False, visible=True, show_label=False)

        async def generate(*args):
            # 调用逻辑
            model_name = args[0]
            gen_parse_type = args[1]
            input_content = None
            if gen_parse_type == "单URL":
                input_content = args[2]
            elif gen_parse_type == "MD文档":
                input_content = args[3]
            elif gen_parse_type == "本地视频文件":
                input_content = args[4]

            notice_info, transcript_output_tran, organized_output_tran, xiaohongshu_output_tran, images = await generate_video_note(model_name, gen_parse_type, input_content)

            return [gr.Textbox(notice_info, visible=True), transcript_output_tran, organized_output_tran, xiaohongshu_output_tran, gr.Button(interactive=True), images]

        def after_slow_function():
            return gr.Button(interactive=True), gr.Textbox('生成中...', interactive=False, visible=False, show_label=False)

        generate_btn.click(
            fn=on_btn_click,
            outputs=[generate_btn, result_tabs, result_status]
        ).then(
            fn=generate,
            inputs = [model_name, parse_type,
                    url_input, md_file_input, local_video_input, local_storage],
            outputs=[warning_icon, transcript_output, organized_output, xiaohongshu_output, generate_btn, note_images]
        ).then(
            fn=after_slow_function,
            outputs=[generate_btn, result_status]
        )

    webui.launch()


if __name__ == "__main__":
    main()
