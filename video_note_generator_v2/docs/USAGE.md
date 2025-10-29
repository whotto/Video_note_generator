# 使用指南

## 安装

### 从源码安装

```bash
git clone https://github.com/whotto/Video_note_generator.git
cd video_note_generator_v2
pip install -e .
```

### 从 PyPI 安装（如果已发布）

```bash
pip install video-note-generator
```

## 配置

### 1. 创建配置文件

```bash
cp .env.example .env
```

### 2. 编辑配置文件

编辑 `.env` 文件，填入必要的 API 密钥：

```ini
# OpenRouter API（必需）
OPENROUTER_API_KEY=your-openrouter-api-key

# Unsplash API（可选，用于图片）
UNSPLASH_ACCESS_KEY=your-unsplash-access-key
```

### 3. 验证配置

```bash
vnote check
```

## 基本使用

### 处理单个视频

```bash
vnote process https://youtube.com/watch?v=xxxxx
```

### 处理文本文件中的链接

创建一个 `urls.txt` 文件：

```
https://youtube.com/watch?v=xxxxx
https://bilibili.com/video/BVxxxxxxx
https://douyin.com/video/xxxxxx
```

然后运行：

```bash
vnote process urls.txt
```

### 处理 Markdown 文件

如果你有一个包含视频链接的 Markdown 文件：

```markdown
# 学习笔记

## 视频1
[Python 教程](https://youtube.com/watch?v=xxxxx)

## 视频2
https://bilibili.com/video/BVxxxxxxx
```

运行：

```bash
vnote process notes.md
```

### 不生成小红书版本

如果只想要原始转录和整理版，不需要小红书版本：

```bash
vnote process https://youtube.com/watch?v=xxxxx --no-xiaohongshu
```

## 高级配置

### 修改模型

编辑 `.env` 文件：

```ini
# 使用不同的 AI 模型
AI_MODEL=anthropic/claude-2

# 使用不同的 Whisper 模型
WHISPER_MODEL=large  # tiny, base, small, medium, large
```

### 调整内容生成参数

```ini
# 生成更长的内容
MAX_TOKENS=4000

# 调整创造性
TEMPERATURE=0.9

# 调整分块大小
CONTENT_CHUNK_SIZE=3000
```

### 使用代理

```ini
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

## 输出文件

处理完成后，会在 `generated_notes/` 目录下生成以下文件：

1. `{timestamp}_original.md` - 原始转录
2. `{timestamp}_organized.md` - 整理版
3. `{timestamp}_xiaohongshu.md` - 小红书版本（如果启用）

## Python API

你也可以在 Python 代码中使用：

```python
from video_note_generator import VideoNoteProcessor, get_settings, setup_logger

# 设置
settings = get_settings()
logger = setup_logger()

# 创建处理器
processor = VideoNoteProcessor(settings=settings, logger=logger)

# 处理视频
files = processor.process_video(
    url="https://youtube.com/watch?v=xxxxx",
    generate_xiaohongshu=True
)

print(f"生成的文件: {files}")
```

## 常见问题

### Q: 下载失败怎么办？

A: 可能的原因：
1. 网络问题：尝试配置代理
2. 平台限制：某些平台可能需要登录或有地区限制
3. URL 格式错误：确保 URL 格式正确

### Q: 转录速度很慢？

A: Whisper 转录需要时间，特别是长视频。建议：
1. 使用更小的模型（如 `base` 或 `small`）
2. 确保有足够的 RAM 和 CPU
3. 如果有 NVIDIA GPU，安装 CUDA 版本的 PyTorch

### Q: 如何避免重复转录？

A: 项目内置了缓存机制，相同的音频文件只会转录一次。缓存保存在 `.cache/transcriptions/` 目录。

### Q: 可以处理本地视频文件吗？

A: 当前版本主要支持在线视频链接。处理本地文件的功能将在未来版本中添加。

## 故障排除

### 日志文件

查看 `logs/` 目录下的日志文件获取详细信息：

- `video_note_generator_YYYYMMDD.log` - 所有日志
- `video_note_generator_error_YYYYMMDD.log` - 仅错误日志

### 调试模式

启用调试模式获取更多信息：

```ini
# .env
DEBUG=true
LOG_LEVEL=DEBUG
```

### 清除缓存

如果遇到问题，尝试清除缓存：

```bash
rm -rf .cache/
```

## 性能优化

### 1. 使用更小的 Whisper 模型

对于中文内容，`base` 或 `small` 模型通常就足够了：

```ini
WHISPER_MODEL=small
```

### 2. 调整分块大小

如果内存有限，可以减小分块大小：

```ini
CONTENT_CHUNK_SIZE=1500
```

### 3. 批量处理

批量处理多个视频比逐个处理更高效，因为可以复用已加载的模型。
