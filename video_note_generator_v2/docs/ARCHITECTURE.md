# 架构设计文档

## 项目概述

视频笔记生成器 V2 是一个模块化的 Python 应用，用于将在线视频转换为结构化的笔记内容。

## 核心架构

### 分层架构

```
┌─────────────────────────────────────┐
│         CLI 层 (cli.py)             │  ← 用户交互
├─────────────────────────────────────┤
│     处理器层 (processor.py)         │  ← 业务编排
├─────────────────────────────────────┤
│       服务层 (多个模块)             │  ← 核心功能
│  - downloader/                      │
│  - transcriber.py                   │
│  - ai_processor.py                  │
│  - generators/                      │
│  - image_service.py                 │
├─────────────────────────────────────┤
│      工具层 (utils/)                │  ← 通用工具
│  - logger.py                        │
│  - text_utils.py                    │
├─────────────────────────────────────┤
│    配置层 (config.py)               │  ← 配置管理
└─────────────────────────────────────┘
```

## 模块说明

### 1. CLI 层 (cli.py)

**职责**：
- 命令行参数解析
- 用户交互
- 进度显示

**技术栈**：
- Click: 命令行框架
- Rich: 终端美化

**关键命令**：
- `vnote process`: 处理视频
- `vnote check`: 环境检查

### 2. 处理器层 (processor.py)

**职责**：
- 业务流程编排
- 协调各个服务模块
- 文件管理

**核心类**：
```python
class VideoNoteProcessor:
    def process_video(url) -> List[Path]
    def process_multiple_videos(urls) -> dict
```

**处理流程**：
```
下载视频 → 转录音频 → 整理内容 → 生成笔记 → 获取图片 → 保存文件
```

### 3. 下载器模块 (downloader/)

**设计模式**：策略模式 + 注册表模式

**结构**：
```
downloader/
├── base.py              # 抽象基类和注册表
└── ytdlp_downloader.py  # yt-dlp 实现
```

**可扩展性**：
```python
# 添加新平台支持
class BilibiliDownloader(BaseDownloader):
    def supports(self, url): ...
    def download(self, url, output_dir): ...

# 注册到系统
registry.register(BilibiliDownloader())
```

### 4. 转录服务 (transcriber.py)

**设计模式**：单例模式

**特性**：
- Whisper 模型缓存
- 转录结果缓存
- 支持多种模型大小

**核心类**：
```python
class WhisperTranscriber:
    def transcribe(audio_path, model_name) -> str
    def _load_model(model_name) -> whisper.Whisper

class TranscriptionCache:
    def get(audio_path, model_name) -> Optional[str]
    def set(audio_path, model_name, text)
```

### 5. AI 处理器 (ai_processor.py)

**职责**：
- 内容整理
- 内容生成
- 翻译服务

**核心方法**：
```python
class AIProcessor:
    def organize_content(content) -> str
    def organize_long_content(content, chunk_size) -> str
    def translate_to_english(text) -> str
```

**分块策略**：
- 保持段落完整性
- 智能重叠
- 上下文连贯

### 6. 生成器模块 (generators/)

**设计模式**：策略模式

**结构**：
```
generators/
└── xiaohongshu.py  # 小红书生成器
```

**可扩展**：
- 可轻松添加新的生成器（如博客、知乎等）
- 每个生成器独立实现

### 7. 图片服务 (image_service.py)

**职责**：
- 图片搜索
- 关键词翻译
- URL 获取

**核心类**：
```python
class UnsplashImageService:
    def search_photos(query, count) -> List[str]
    def get_photos_for_xiaohongshu(titles, tags) -> List[str]
```

### 8. 配置管理 (config.py)

**技术栈**：Pydantic Settings

**特性**：
- 类型验证
- 自动类型转换
- 环境变量读取
- 配置验证

**核心类**：
```python
class Settings(BaseSettings):
    # API 配置
    openrouter_api_key: str
    unsplash_access_key: Optional[str]

    # 模型配置
    ai_model: str = "google/gemini-pro"
    whisper_model: str = "medium"

    # 验证器
    @validator("max_paragraphs")
    def validate_paragraph_range(cls, v, values): ...
```

### 9. 工具模块 (utils/)

**logger.py**：
- 彩色日志输出
- 文件日志（自动轮转）
- 错误日志分离

**text_utils.py**：
- 文本分割
- URL 提取
- 文本清理

## 设计原则

### 1. 单一职责原则 (SRP)

每个模块只负责一个功能领域：
- downloader: 视频下载
- transcriber: 音频转录
- ai_processor: AI 处理
- generators: 内容生成

### 2. 开放封闭原则 (OCP)

通过抽象基类和注册表，支持扩展而无需修改核心代码：

```python
# 扩展下载器
class NewPlatformDownloader(BaseDownloader):
    ...

# 扩展生成器
class BlogGenerator:
    ...
```

### 3. 依赖倒置原则 (DIP)

高层模块（processor）依赖抽象（接口），而不是具体实现：

```python
class VideoNoteProcessor:
    def __init__(self, settings, logger):
        # 依赖注入
        self.downloader_registry = DownloaderRegistry()
        self.transcriber = WhisperTranscriber(logger)
```

### 4. 接口隔离原则 (ISP)

下载器接口简洁明确：

```python
class BaseDownloader(ABC):
    @abstractmethod
    def supports(self, url) -> bool: ...

    @abstractmethod
    def download(self, url, output_dir) -> tuple: ...
```

## 数据流

### 视频处理流程

```
用户输入 URL
    ↓
CLI 解析
    ↓
Processor 接收
    ↓
1. Downloader 下载 → 音频文件
    ↓
2. Transcriber 转录 → 文本
    ↓
3. AIProcessor 整理 → 结构化内容
    ↓
4. Generator 生成 → 小红书笔记
    ↓
5. ImageService 获取 → 图片URL
    ↓
6. 保存文件
    ↓
返回文件路径列表
```

## 错误处理

### 分层错误处理

1. **模块级别**：
   - 捕获并记录错误
   - 返回 None 或空值
   - 不中断整个流程

2. **处理器级别**：
   - 决定是否继续
   - 记录失败原因
   - 清理临时文件

3. **CLI 级别**：
   - 显示用户友好的错误信息
   - 提供故障排查建议

### 自定义异常

```python
class DownloadError(Exception):
    def __init__(self, message, platform, error_type, details): ...
```

## 性能优化

### 1. 模型缓存

- Whisper 模型只加载一次（单例模式）
- 缓存在内存中，避免重复加载

### 2. 转录缓存

- 转录结果持久化到磁盘
- 使用文件哈希作为缓存键
- 避免重复转录相同音频

### 3. 批量处理

- 复用已加载的模型
- 减少初始化开销

## 安全性

### 1. 移除不安全代码

- ✅ 移除 SSL 验证禁用
- ✅ 移除不必要的全局配置
- ✅ 使用安全的文件路径操作

### 2. 配置验证

- 使用 Pydantic 进行类型和值验证
- 防止无效配置导致的问题

### 3. 错误日志

- 敏感信息不记录到日志
- 日志文件权限控制

## 可测试性

### 单元测试

每个模块都可以独立测试：

```python
def test_downloader():
    downloader = YtDlpDownloader()
    assert downloader.supports("https://youtube.com/...")

def test_text_split():
    chunks = split_content(text, max_chars=1000)
    assert all(len(chunk) <= 1000 for chunk in chunks)
```

### 集成测试

测试完整的处理流程：

```python
def test_full_process():
    processor = VideoNoteProcessor(settings, logger)
    files = processor.process_video(test_url)
    assert len(files) >= 2
```

## 未来扩展

### 1. 插件系统

```python
class PluginManager:
    def register_downloader(self, downloader): ...
    def register_generator(self, generator): ...
```

### 2. 异步处理

```python
async def process_video_async(url):
    # 使用 asyncio 提高并发性能
    ...
```

### 3. Web API

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/process")
async def process_video(url: str):
    ...
```

### 4. 数据库支持

- 存储处理历史
- 缓存到数据库
- 用户管理

## 总结

V2 架构的核心优势：

1. **模块化**：清晰的模块划分，易于理解和维护
2. **可扩展**：通过抽象和注册表，支持灵活扩展
3. **可测试**：每个模块可独立测试
4. **类型安全**：完整的类型注解
5. **配置化**：集中式配置管理
6. **安全性**：移除了不安全的代码
7. **性能**：缓存和单例模式提高效率
