# 视频笔记生成器 V2 🎥

> 一键将视频转换为优质笔记，支持博客文章和小红书格式

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🎯 核心功能

- 🎬 **多平台支持**：YouTube（完全支持）、Bilibili（字幕提取）
- 🤖 **AI 智能处理**：基于 OpenRouter API，自动生成优质笔记
- 📝 **多种输出格式**：
  - 原始转录笔记
  - 结构化整理笔记
  - 深度博客文章
  - 小红书爆款笔记
- 🌐 **双端支持**：Web 可视化界面 + CLI 命令行
- ⚡ **批量处理**：支持同时处理多个视频
- 🎨 **现代 UI**：Glassmorphism 设计风格，美观易用
- 📊 **历史记录**：自动保存处理历史，支持预览/复制/下载

## 🎨 两种使用方式

### 🌐 Web 界面（推荐新手）

**特点**：
- ✨ 专业美观的可视化界面（Glassmorphism 设计）
- 🚀 支持单个/批量处理
- 📈 实时进度显示
- 📋 文件预览、复制、下载功能
- 💾 历史记录管理
- 🎯 零学习成本

**启动方式**：
```bash
# 启动 Web 服务
python web_app.py

# 或使用 uvicorn（推荐）
uvicorn web_app:app --host 0.0.0.0 --port 8001 --reload
```

访问 `http://localhost:8001` 即可使用。

### ⌨️ 命令行（推荐开发者）

**特点**：
- ⚡ 轻量快速
- 🔧 脚本集成友好
- 🤖 适合自动化

**使用方式**：
```bash
# 检查环境配置
vnote check

# 处理单个视频
vnote process https://youtube.com/watch?v=xxxxx

# 处理包含多个链接的文件
vnote process urls.txt

# 不生成小红书版本
vnote process https://youtube.com/watch?v=xxxxx --no-xiaohongshu
```

---

## 🚀 快速开始

### 1️⃣ 系统要求

**必需软件**：
- Python 3.8 或更高版本
- FFmpeg（用于音频处理）

**FFmpeg 安装**：

**macOS**:
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Linux (CentOS/RHEL)**:
```bash
sudo yum install ffmpeg
```

**Windows**:
1. 从 [FFmpeg 官网](https://ffmpeg.org/download.html) 下载
2. 解压到任意目录（如 `C:\ffmpeg`）
3. 将 `bin` 目录添加到系统环境变量 PATH 中

**验证 FFmpeg 安装**:
```bash
ffmpeg -version
```

### 2️⃣ 安装项目

```bash
# 克隆仓库
git clone https://github.com/whotto/Video_note_generator.git
cd video_note_generator_v2

# 创建虚拟环境（强烈推荐）
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 或者以开发模式安装
pip install -e .
```

### 3️⃣ 配置 API 密钥

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入必要的 API 密钥
# macOS/Linux 使用：
nano .env
# 或
vim .env

# Windows 使用：
notepad .env
```

**必需配置项**：

```ini
# OpenRouter API 密钥（必需）
# 获取地址：https://openrouter.ai/keys
OPENROUTER_API_KEY=your_openrouter_key_here

# Unsplash API 密钥（可选，用于获取配图）
# 获取地址：https://unsplash.com/developers
UNSPLASH_ACCESS_KEY=your_unsplash_key_here

# AI 模型配置（推荐使用 Gemini Flash）
AI_MODEL=google/gemini-2.0-flash-exp:free

# Whisper 模型大小（medium 推荐，quality/speed 平衡）
WHISPER_MODEL=medium
```

### 4️⃣ 配置 Cookies（重要！）

**为什么需要配置 Cookies？**
- YouTube 和其他平台加强了反爬虫机制
- 需要 cookies 才能下载视频和提取内容

**一键配置方案**（推荐）：

```bash
# 运行自动导出脚本
python export_cookies.py
```

**操作步骤**：
1. 选择浏览器（推荐 Chrome）
2. 当弹出授权窗口时，**点击「始终允许」**
3. 等待完成，cookies 会自动保存

**结果**：
- ✅ 只需授权一次
- ✅ 以后不会再弹窗
- ✅ YouTube 和 B站视频都能正常处理

📖 **详细指南**：[QUICK_SETUP.md](QUICK_SETUP.md) | [COOKIES_GUIDE.md](COOKIES_GUIDE.md)

---

### 5️⃣ 验证安装

```bash
# 检查环境配置
vnote check

# 如果一切正常，会看到：
# ✅ Python version: 3.x.x
# ✅ FFmpeg installed
# ✅ OpenRouter API key configured
# ✅ All dependencies installed
```

---

## 📖 详细使用指南

### Web 界面使用

1. **启动服务**：
   ```bash
   python web_app.py
   ```

2. **打开浏览器**访问 `http://localhost:8001`

3. **处理视频**：
   - **单个处理**：在"单个视频处理"标签页输入视频 URL，点击"开始处理"
   - **批量处理**：在"批量处理"标签页输入多个 URL（每行一个），点击"批量处理"

4. **查看结果**：
   - 处理完成后，在"处理历史"中可以查看所有生成的文件
   - 点击"预览"查看内容
   - 点击"复制"将内容复制到剪贴板
   - 点击"下载"保存文件到本地

### 命令行使用

```bash
# 基本用法
vnote process <URL或文件路径>

# 处理 YouTube 视频
vnote process https://www.youtube.com/watch?v=dQw4w9WgXcQ

# 处理包含多个链接的文件
vnote process video_urls.txt

# 只生成博客文章，不生成小红书笔记
vnote process <URL> --no-xiaohongshu

# 检查环境配置
vnote check

# 查看帮助
vnote --help
```

---

## 🌐 平台支持详情

### ✅ YouTube（完全支持）

**支持方式**：
- ✅ 官方字幕提取（YouTube Transcript API）
- ✅ 音频下载 + Whisper 转录
- ✅ 官方 iframe 嵌入播放

**示例链接**：
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://www.youtube.com/watch?v=9bZkp7q19f0
```

**处理速度**：30-120 秒（取决于视频长度）

**成功率**：95%+

---

### 🟡 Bilibili（字幕支持）

**当前状态**：
- ✅ **官方字幕提取**（推荐，超快速度）
- ❌ 音频下载（受反爬虫限制，暂不支持）

**使用建议**：
1. **优先选择有字幕的 B 站视频**
2. 系统会自动提取官方字幕生成笔记
3. 如果视频无字幕，目前暂不支持

**如何识别有字幕的视频**：
- B 站播放器右下角有 "CC" 字幕按钮

**处理速度**：
| 视频时长 | 处理时间 |
|---------|---------|
| 1-3分钟 | 5-10秒 ✨ |
| 3-5分钟 | 10-20秒 ✨ |
| 5-10分钟 | 20-40秒 ✨ |

**为什么不支持无字幕视频**：
- B站在 2024 年加强了反爬虫策略
- 视频流需要复杂的 token 和签名
- 但官方字幕 API 仍然可用

**💡 如需下载 B站视频（非字幕提取）**：
- 可以配置浏览器 Cookies 文件
- 查看详细指南：[COOKIES_GUIDE.md](COOKIES_GUIDE.md)

---

### 🔧 其他平台

基于 `yt-dlp` 理论上支持 1000+ 网站，包括：
- Vimeo
- Facebook
- Twitter/X
- TikTok
- 等等...

但需要逐个测试验证，目前未充分测试。

📖 **详细的平台支持说明**：[PLATFORM_SUPPORT.md](PLATFORM_SUPPORT.md)

---

## 📁 项目结构

```
video_note_generator_v2/
├── src/
│   └── video_note_generator/
│       ├── __init__.py
│       ├── config.py              # 配置管理（Pydantic）
│       ├── cli.py                 # CLI 命令行界面
│       ├── processor.py           # 主处理器
│       ├── transcriber.py         # Whisper 转录服务
│       ├── ai_processor.py        # AI 内容处理
│       ├── image_service.py       # 图片服务（Unsplash）
│       ├── downloader/            # 下载器模块
│       │   ├── __init__.py
│       │   ├── base.py            # 下载器基类
│       │   ├── ytdlp_downloader.py    # yt-dlp 下载器
│       │   └── bilibili_downloader.py # B站字幕提取器
│       ├── generators/            # 内容生成器
│       │   ├── __init__.py
│       │   ├── xiaohongshu.py     # 小红书笔记生成器
│       │   └── blog.py            # 博客文章生成器
│       └── utils/                 # 工具模块
│           ├── __init__.py
│           ├── logger.py          # 日志系统（Rich）
│           └── text_utils.py      # 文本处理工具
├── static/                        # Web 静态资源
│   ├── css/
│   │   └── style.css             # Glassmorphism 样式
│   └── js/
│       └── app.js                # 前端交互逻辑
├── templates/
│   └── index.html                # Web 主页面
├── web_app.py                    # FastAPI Web 应用
├── requirements.txt              # Python 依赖
├── requirements_full.txt         # 完整依赖（含版本锁定）
├── setup.py                      # 安装脚本
├── .env.example                  # 配置模板
├── .gitignore                    # Git 忽略文件
├── README.md                     # 项目说明（本文件）
└── PLATFORM_SUPPORT.md           # 平台支持详情
```

---

## 🛠️ 技术栈

**后端**：
- **Web 框架**: FastAPI + Uvicorn
- **视频下载**: yt-dlp、you-get
- **语音识别**: OpenAI Whisper
- **AI 处理**: OpenRouter API（Gemini 2.0 Flash）
- **图片服务**: Unsplash API
- **CLI 框架**: Click + Rich
- **配置管理**: Pydantic + python-dotenv
- **HTTP 客户端**: httpx、requests

**前端**：
- HTML5 + CSS3（Glassmorphism 设计）
- Vanilla JavaScript
- LocalStorage（历史记录）

---

## 📝 输出文件说明

每个视频会生成最多 **4 个文件**：

### 1. 原始笔记 (`YYYYMMDD_HHMMSS_original.md`)
- 完整的视频转录文本
- 视频元信息（标题、作者、链接等）
- 原始时间戳

### 2. 整理版笔记 (`YYYYMMDD_HHMMSS_organized.md`)
- AI 优化后的结构化内容
- 清晰的章节划分
- 重点内容提炼
- 段落优化和语言润色

### 3. 博客文章 (`YYYYMMDD_HHMMSS_blog.md`)
- 深度博客文章格式
- 引人入胜的标题
- 完整的论述结构
- 思想的重塑和提炼
- 包含元信息（来源、链接等）

### 4. 小红书笔记 (`YYYYMMDD_HHMMSS_xiaohongshu.md`)
- 爆款标题（多个备选）
- 600-800 字精华内容
- 相关配图推荐
- 优化的标签系统

**输出目录**：默认保存在 `generated_notes/` 目录

---

## ⚙️ 配置说明

所有配置都在 `.env` 文件中管理。

### 完整配置示例

```ini
# ==========================================
# API Configuration
# ==========================================

# OpenRouter API Key (必需)
# 获取地址：https://openrouter.ai/keys
OPENROUTER_API_KEY=your_key_here

# Unsplash Access Key (可选)
# 获取地址：https://unsplash.com/developers
UNSPLASH_ACCESS_KEY=your_key_here

# ==========================================
# AI Model Configuration
# ==========================================

# AI 模型选择
# 推荐：google/gemini-2.0-flash-exp:free（免费且高质量）
# 其他选项：anthropic/claude-3-sonnet, openai/gpt-4, etc.
AI_MODEL=google/gemini-2.0-flash-exp:free

# Whisper 模型大小
# 选项：tiny, base, small, medium, large
# 推荐：medium（质量和速度的平衡）
WHISPER_MODEL=medium

# ==========================================
# Content Generation Settings
# ==========================================

# 最大生成 token 数
MAX_TOKENS=4000

# 内容分块大小
CONTENT_CHUNK_SIZE=2000

# 生成温度（0.0-1.0）
# 越高越有创意，越低越保守
TEMPERATURE=0.7

# ==========================================
# Directory Configuration
# ==========================================

# 输出目录
OUTPUT_DIR=generated_notes

# 缓存目录
CACHE_DIR=.cache

# 日志目录
LOG_DIR=logs

# ==========================================
# Advanced Settings
# ==========================================

# 是否启用缓存
ENABLE_CACHE=true

# 日志级别（DEBUG, INFO, WARNING, ERROR）
LOG_LEVEL=INFO

# 是否启用彩色日志
ENABLE_COLOR_LOG=true
```

---

## 🐛 常见问题与故障排除

### Q1: FFmpeg not found 错误

**症状**：
```
ERROR: FFmpeg not found. Please install FFmpeg first.
```

**解决方案**：
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`
- **Windows**: 从官网下载并添加到 PATH

验证安装：`ffmpeg -version`

---

### Q2: B站视频处理失败

**症状**：
```
处理失败：视频没有字幕或无法访问
```

**解决方案**：
1. **确认视频有字幕**：B站播放器右下角应有 "CC" 按钮
2. **选择有字幕的视频**：搜索时筛选"有字幕"条件
3. **避免会员专享视频**：选择公开视频

**推荐视频类型**：
- ✅ 教程类、演讲类（字幕率高）
- ✅ 最近发布的视频
- ❌ 无字幕视频
- ❌ 会员专享视频

---

### Q3: OpenRouter API 错误

**症状**：
```
AI processing failed: API key not configured
```

**解决方案**：
1. 检查 `.env` 文件中 `OPENROUTER_API_KEY` 是否正确配置
2. 确认 API key 有效：访问 https://openrouter.ai/keys
3. 确认账户有足够余额（Gemini Flash 模型是免费的）

---

### Q4: Whisper 转录速度慢

**症状**：
- 转录过程耗时很长

**解决方案**：
1. **降低模型大小**：在 `.env` 中设置 `WHISPER_MODEL=small` 或 `base`
2. **使用 GPU 加速**（如果有 NVIDIA GPU）：
   ```bash
   pip install openai-whisper[gpu]
   ```
3. **优先使用有字幕的视频**：跳过 Whisper 转录步骤

---

### Q5: Web 界面无法访问

**症状**：
```
无法访问 http://localhost:8001
```

**解决方案**：
1. **检查端口占用**：
   ```bash
   # macOS/Linux
   lsof -ti:8001

   # Windows
   netstat -ano | findstr :8001
   ```

2. **更改端口**：
   ```bash
   # 使用其他端口启动
   uvicorn web_app:app --port 8002
   ```

3. **检查防火墙设置**：确保端口未被阻止

---

### Q6: 依赖安装失败

**症状**：
```
ERROR: Could not install packages due to an OSError
```

**解决方案**：

**Windows 用户**：
```bash
# 以管理员身份运行 PowerShell
pip install --upgrade pip
pip install -r requirements.txt
```

**macOS/Linux 用户**：
```bash
# 升级 pip
python -m pip install --upgrade pip

# 如果权限问题
pip install --user -r requirements.txt
```

**使用国内镜像（中国用户）**：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 🔧 开发指南

### 开发环境设置

```bash
# 安装开发依赖（如需要）
pip install pytest black isort mypy

# 运行测试
pytest tests/

# 代码格式化
black src/
isort src/

# 类型检查
mypy src/
```

### 添加新平台支持

如果你想添加新平台，需要实现 `BaseDownloader` 接口：

```python
from video_note_generator.downloader.base import BaseDownloader

class NewPlatformDownloader(BaseDownloader):
    def supports(self, url: str) -> bool:
        """检查是否支持该 URL"""
        return 'newplatform.com' in url

    def get_video_info(self, url: str) -> VideoInfo:
        """获取视频信息"""
        # 实现信息提取
        pass

    def download(self, url: str, output_dir: Path) -> tuple:
        """下载视频/音频"""
        # 实现下载逻辑
        pass
```

---

## 📊 性能参考

| 视频平台 | 视频时长 | 处理时间 | 成功率 |
|---------|---------|---------|--------|
| YouTube | 1-3分钟 | 30-60秒 | 95%+ |
| YouTube | 3-10分钟 | 1-3分钟 | 95%+ |
| B站(有字幕) | 1-3分钟 | 5-10秒 ✨ | 100% |
| B站(有字幕) | 3-10分钟 | 10-30秒 ✨ | 100% |

*测试环境：macOS M1, 16GB RAM, 100Mbps 网络*

---

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 👤 作者

- **作者**：huanwang.org
- **GitHub**：[whotto/Video_note_generator](https://github.com/whotto/Video_note_generator)
- **Email**：grow8org@gmail.com

---

## 🙏 致谢

感谢以下开源项目：

- [Whisper](https://github.com/openai/whisper) - OpenAI 语音识别模型
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载工具
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [OpenRouter](https://openrouter.ai/) - AI API 聚合服务
- [Click](https://click.palletsprojects.com/) - Python CLI 框架
- [Rich](https://rich.readthedocs.io/) - 终端美化库
- [Unsplash](https://unsplash.com/) - 高质量图片 API

---

## 📈 更新日志

### V2.0.0 (2024-10-29)

**新特性**：
- ✨ 添加 FastAPI Web 界面，替代 Streamlit
- ✨ Glassmorphism UI 设计风格
- ✨ 新增博客文章生成功能
- ✨ 文件预览、复制、下载功能
- ✨ 历史记录管理
- ✨ 批量处理支持

**改进**：
- 🔧 全面重构代码架构
- 🔧 添加完整类型注解
- 🔧 改进日志系统（Rich 彩色输出）
- 🔧 添加 Whisper 缓存机制
- 🔧 修复小红书笔记重复内容问题
- 🔧 修复博客文章元信息重复问题
- 🔧 优化 B站字幕提取速度
- 🍪 **Cookie 自动管理**：程序启动时自动导出浏览器 cookies，无需手动配置
- 🔄 **B站限流智能处理**：自动检测限流并重试，提供友好的错误提示
- ⏱️ **支持长视频处理**：前端超时时间从10分钟提升至30分钟

**平台支持**：
- ✅ YouTube 完全支持（字幕 + Whisper）
- ✅ Bilibili 字幕提取支持
- 📝 添加详细的平台支持文档

**跨平台**：
- 🖥️ macOS、Linux、Windows 全平台支持
- 📦 更新依赖包，确保跨平台兼容性

---

## 📞 支持与反馈

- **问题反馈**：[GitHub Issues](https://github.com/whotto/Video_note_generator/issues)
- **功能建议**：[GitHub Discussions](https://github.com/whotto/Video_note_generator/discussions)
- **邮件联系**：grow8org@gmail.com

---

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！**
