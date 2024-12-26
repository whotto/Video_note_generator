# src/settings/setting.py
import json
import gradio as gr

from src.logger import app_logger

global_setting = {
    "openrouter_api_key": '',
    "openrouter_api_url": 'https://openrouter.ai/api/v1',
    "openrouter_app_name": 'rednote-generator',
    "openrouter_http_referer": 'https://github.com',
    "unsplash_access_key": '',
    "unsplash_secret_key": '',
    "unsplash_redirect_uri": 'https://github.com',
    "whisper_model": 'medium',
    "whisper_language": 'zh',
    "ffmpeg_path": '',
    "http_proxy": '',
    "https_proxy": '',
    "output_dir": 'generated_notes',
    "max_tokens": 5000,
    "content_chunk_size": 2000,
    "temperature": 0.7,
    "top_p": 0.9,
    "use_emoji": True,
    "tag_count": 5,
    "min_paragraphs": 3,
    "max_paragraphs": 6,
    "debug": False,
    "log_level": 'info'
}


def update_and_save_settings(*args):
    keys = list(global_setting.keys())
    updated_settings = {key: value for key, value in zip(keys, args)}
    global_setting.update(updated_settings)

    required_keys_filled = check_required_keys()
    status_message = "设置已更新" if required_keys_filled else "⚠️ 必选参数配置缺失"

    # convert global_setting to json str
    saved_settings = json.dumps(global_setting)

    return [status_message, gr.update(visible=False), saved_settings]


# 修改 load_settings 函数
def load_settings(saved_settings: str):
    try:
        # convert json str to dict
        if saved_settings:
            saved_settings = json.loads(saved_settings)
            global_setting.update(saved_settings)
    except Exception as e:
        gr.Error(f"Error loading settings: {e}")

    required_keys_filled = check_required_keys()
    return_dict = {
        'warning_icon': gr.update(visible=not required_keys_filled),
    }

    # append global_setting values to return_dict
    for key in global_setting.keys():
        return_dict[key] = global_setting[key]

    return [return_dict[key] for key in return_dict.keys()]


def     check_required_keys(setting_str: str = None):
    if setting_str:
        setting_dict = json.loads(setting_str)
        global_setting.update(setting_dict)
    required_keys = ["openrouter_api_key"]
    return all(global_setting[key] for key in required_keys)