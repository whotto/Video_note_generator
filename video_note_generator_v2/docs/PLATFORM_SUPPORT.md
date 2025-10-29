# 平台支持说明

## 📊 支持情况概览

| 平台 | 支持等级 | 稳定性 | 说明 |
|------|---------|--------|------|
| YouTube | ✅ 完全支持 | ⭐⭐⭐⭐⭐ | 最稳定，推荐使用 |
| Bilibili | ⚠️ 部分支持 | ⭐⭐⭐ | 需要特殊配置 |
| 抖音 | ❌ 不推荐 | ⭐ | 反爬虫严格，成功率低 |
| 本地文件 | 🚧 计划中 | - | 未来版本支持 |

## YouTube

### 支持情况
✅ **完全支持**，这是最推荐使用的平台

### 特点
- 下载稳定可靠
- 支持各种视频质量
- 不需要额外配置
- yt-dlp 原生支持

### 使用示例
```bash
vnote process https://youtube.com/watch?v=dQw4w9WgXcQ
vnote process https://youtu.be/dQw4w9WgXcQ
```

### 注意事项
- 某些地区可能需要代理
- 年龄限制视频可能需要登录

## Bilibili

### 支持情况
⚠️ **部分支持**，可用但需要额外配置

### 特点
- 需要使用专用下载器
- 某些视频需要大会员
- 可能需要 Cookie 文件
- 下载速度较慢

### 基本使用
```bash
# 普通视频（无需登录）
vnote process https://www.bilibili.com/video/BV1xx411c7XZ

# 短链接
vnote process https://b23.tv/xxxxxxx
```

### 高级配置

对于需要登录的视频，需要提供 Cookie：

#### 1. 获取 Cookie
1. 在浏览器中登录 B站
2. 打开开发者工具（F12）
3. 切换到 Network 标签
4. 刷新页面
5. 找到任意请求，复制 Cookie

#### 2. 创建 Cookie 文件
创建 `cookies/bilibili_cookies.txt`（Netscape 格式）：
```
# Netscape HTTP Cookie File
.bilibili.com	TRUE	/	FALSE	1234567890	SESSDATA	your_sessdata_here
```

#### 3. 配置使用
```python
from video_note_generator.downloader import BilibiliDownloader

downloader = BilibiliDownloader(
    cookie_file='cookies/bilibili_cookies.txt'
)
```

### 常见问题

**Q: 下载失败提示 "需要大会员"？**

A: 某些高清晰度视频需要大会员权限，可以：
1. 使用大会员账号的 Cookie
2. 选择较低画质
3. 考虑使用其他平台的相同内容

**Q: 下载速度很慢？**

A: B站对下载速度有限制，建议：
1. 使用国内网络
2. 避免高峰时段
3. 耐心等待

**Q: 提示 "you-get 未安装"？**

A: 安装 you-get 以获得更好的 B站支持：
```bash
pip install you-get
```

## 抖音

### 支持情况
❌ **不推荐使用**，成功率很低

### 问题
- 反爬虫机制严格
- 需要复杂的 Cookie 和签名
- API 经常变化
- 下载成功率 < 30%

### 建议
如果必须处理抖音视频：

1. **使用第三方服务**
   - 抖音去水印网站
   - 下载后作为本地文件处理（未来版本）

2. **手动下载**
   - 使用抖音 App 直接下载
   - 传输到电脑处理

3. **等待官方支持**
   - 未来版本可能改进抖音支持
   - 目前不建议依赖

### 临时方案（不保证成功）
```bash
# 可能成功，但概率很低
vnote process https://www.douyin.com/video/xxxxxxx
```

## 其他平台

yt-dlp 理论上支持 1000+ 网站，但实际效果因平台而异。

### 可能支持的平台
- Vimeo
- DailyMotion
- Twitter 视频
- Facebook 视频（需要登录）
- Instagram（需要登录）

### 使用方式
```bash
# 尝试处理
vnote process <video_url>

# 检查日志了解失败原因
tail -f logs/video_note_generator_*.log
```

## 本地文件支持（计划中）

### V2.1 版本将支持

```bash
# 处理本地视频文件
vnote process /path/to/video.mp4

# 处理目录下所有视频
vnote process /path/to/videos/ --recursive
```

## 改进建议

### 如何添加新平台支持

如果你想为特定平台添加支持，可以：

1. **创建专用下载器**
```python
# src/video_note_generator/downloader/myplatform_downloader.py
from .base import BaseDownloader

class MyPlatformDownloader(BaseDownloader):
    def supports(self, url):
        return 'myplatform.com' in url

    def download(self, url, output_dir, audio_only=True):
        # 实现下载逻辑
        ...
```

2. **注册下载器**
```python
# 在 processor.py 中
from .downloader import MyPlatformDownloader

registry.register(MyPlatformDownloader())
```

3. **贡献代码**
   - Fork 项目
   - 添加你的下载器
   - 提交 Pull Request

## 故障排查

### 下载失败诊断

1. **检查 URL 格式**
   ```bash
   # 确保 URL 完整
   vnote process "https://youtube.com/watch?v=xxxxx"  # 正确
   vnote process youtube.com/watch?v=xxxxx            # 错误
   ```

2. **查看详细日志**
   ```bash
   # 启用调试模式
   export LOG_LEVEL=DEBUG
   vnote process <url>

   # 查看日志
   cat logs/video_note_generator_*.log
   ```

3. **测试网络连接**
   ```bash
   # 测试能否访问目标网站
   curl -I <video_url>

   # 如果需要代理
   export HTTP_PROXY=http://127.0.0.1:7890
   export HTTPS_PROXY=http://127.0.0.1:7890
   ```

4. **更新依赖**
   ```bash
   # yt-dlp 经常更新以应对网站变化
   pip install --upgrade yt-dlp
   ```

### 常见错误及解决方案

**错误：HTTP Error 403: Forbidden**
- 原因：平台检测到爬虫
- 解决：添加 Cookie 文件，使用代理

**错误：Video unavailable**
- 原因：视频被删除、私密或地区限制
- 解决：检查视频是否可访问，使用 VPN

**错误：FFmpeg not found**
- 原因：未安装 FFmpeg
- 解决：`brew install ffmpeg` (Mac) 或从官网下载

**错误：Timeout**
- 原因：网络慢或视频太大
- 解决：增加超时时间，使用更好的网络

## 推荐工作流程

### 最佳实践

1. **优先使用 YouTube**
   - 最稳定可靠
   - 内容丰富
   - 不需要额外配置

2. **Bilibili 作为补充**
   - 仅处理中文内容
   - 提前准备好 Cookie
   - 预期较长下载时间

3. **避免抖音**
   - 成功率太低
   - 考虑其他途径获取内容

4. **本地处理**
   - 如果下载频繁失败
   - 考虑先手动下载
   - 等待本地文件支持（V2.1）

## 性能对比

基于实际测试（10分钟视频）：

| 平台 | 平均下载时间 | 成功率 | 音频质量 |
|------|-------------|--------|---------|
| YouTube | 2-3 分钟 | 95%+ | 高 |
| Bilibili | 5-10 分钟 | 70% | 中 |
| 抖音 | 10+ 分钟或失败 | <30% | 低 |

## 未来计划

### V2.1
- [ ] 本地视频文件支持
- [ ] Bilibili Cookie 自动管理
- [ ] 改进错误提示

### V2.2
- [ ] 批量下载优化
- [ ] 断点续传
- [ ] 更多平台支持

### V3.0
- [ ] Web UI 上传本地文件
- [ ] 云端处理
- [ ] 实时字幕

## 总结

**目前最可靠的使用方式：**

1. 主要使用 YouTube（成功率 95%+）
2. 必要时使用 Bilibili（需要配置）
3. 避免使用抖音（成功率太低）
4. 等待本地文件支持（V2.1）

**关键建议：**
- 不要期望所有平台都能完美工作
- YouTube 是最佳选择
- 其他平台需要额外配置和耐心
- 查看日志了解失败原因
- 及时更新 yt-dlp

---

有任何问题或建议？欢迎在 GitHub 提 Issue：
https://github.com/whotto/Video_note_generator/issues
