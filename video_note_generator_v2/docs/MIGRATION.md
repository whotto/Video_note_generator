# V1 到 V2 迁移指南

如果你之前使用的是 V1 版本，这份指南将帮助你迁移到 V2。

## 主要变化

### 1. 命令行接口

**V1:**
```bash
python video_note_generator.py https://youtube.com/watch?v=xxxxx
```

**V2:**
```bash
vnote process https://youtube.com/watch?v=xxxxx
```

### 2. 配置文件

V2 使用相同的 `.env` 文件格式，但添加了更多配置选项。你可以直接复用 V1 的配置文件，但建议查看 `.env.example` 了解新增的配置项。

### 3. 输出文件

输出文件的格式和内容基本相同，但文件名格式更加规范：

**V1:**
- 文件名可能不一致

**V2:**
- `{timestamp}_original.md`
- `{timestamp}_organized.md`
- `{timestamp}_xiaohongshu.md`

### 4. Python API

如果你在代码中使用了 V1 的 API，需要更新导入：

**V1:**
```python
from video_note_generator import VideoNoteGenerator

generator = VideoNoteGenerator(output_dir="notes")
generator.process_video(url)
```

**V2:**
```python
from video_note_generator import VideoNoteProcessor, get_settings, setup_logger

settings = get_settings()
logger = setup_logger()
processor = VideoNoteProcessor(settings=settings, logger=logger)
processor.process_video(url)
```

## 安全性改进

V2 移除了以下不安全的做法：

1. **SSL 验证禁用**：V1 中全局禁用了 SSL 验证，V2 已移除
2. **代理配置**：V2 提供了更安全的代理配置方式

如果你在 V1 中依赖这些"功能"，可能需要：
- 配置正确的 SSL 证书
- 使用 `.env` 文件中的代理配置

## 新功能

### 1. 缓存机制

V2 自动缓存 Whisper 转录结果，避免重复处理：

```bash
# 缓存位置
.cache/transcriptions/
```

### 2. 更好的日志

V2 提供了结构化的日志系统：

```bash
# 日志文件
logs/video_note_generator_YYYYMMDD.log
logs/video_note_generator_error_YYYYMMDD.log
```

### 3. 配置验证

V2 提供了配置检查命令：

```bash
vnote check
```

### 4. 类型安全

V2 使用 Pydantic 进行配置管理，提供了类型检查和验证。

## 性能对比

V2 的性能改进：

1. **模型缓存**：Whisper 模型只加载一次
2. **转录缓存**：相同音频不会重复转录
3. **批量处理**：更高效的批量处理

## 故障排查

### 问题：找不到 `vnote` 命令

**解决方案：**
```bash
# 确保正确安装
pip install -e .

# 或者使用 Python 模块方式运行
python -m video_note_generator.cli process <url>
```

### 问题：SSL 证书错误

V2 不再禁用 SSL 验证，如果遇到证书问题：

1. 更新你的 CA 证书
2. 使用代理
3. 检查系统时间是否正确

### 问题：配置文件不生效

确保 `.env` 文件在当前工作目录或项目根目录。

## 推荐的迁移步骤

1. **备份 V1 的配置和输出**
   ```bash
   cp .env .env.v1.backup
   cp -r temp_notes temp_notes.v1.backup
   ```

2. **安装 V2**
   ```bash
   cd video_note_generator_v2
   pip install -e .
   ```

3. **测试配置**
   ```bash
   vnote check
   ```

4. **处理测试视频**
   ```bash
   vnote process https://youtube.com/watch?v=xxxxx
   ```

5. **对比输出**
   确认 V2 的输出符合预期

6. **更新脚本**
   如果你有自动化脚本，更新为使用 `vnote` 命令

## 获取帮助

如果在迁移过程中遇到问题：

1. 查看日志文件：`logs/`
2. 启用调试模式：`.env` 中设置 `DEBUG=true`
3. 提交 Issue：https://github.com/whotto/Video_note_generator/issues
