# 🎬 视频平台支持说明

## 概述

本系统支持多种视频平台的内容提取和笔记生成。根据课堂演示需求，我们采用**三层策略**：

1. **优先提取官方字幕**（最快、最稳定）
2. **下载音频+Whisper转录**（无字幕时的备选）
3. **官方嵌入播放**（兜底方案）

---

## 平台支持详情

### ✅ YouTube（完全支持）

**状态**: 🟢 完全正常

**支持方式**:
- ✅ 官方字幕提取（YouTube Transcript API）
- ✅ 音频下载 + Whisper转录
- ✅ 官方iframe嵌入播放

**示例链接**:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://www.youtube.com/watch?v=9bZkp7q19f0
```

**处理速度**: 30-120秒（取决于视频长度）

**技术实现**:
```python
# 优先提取字幕
from youtube_transcript_api import YouTubeTranscriptApi
transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['zh-Hans', 'zh-Hant', 'en'])

# 备选：yt-dlp下载
yt-dlp --cookies-from-browser chrome -f bestaudio -x --audio-format mp3 [URL]
```

---

### 🟡 Bilibili（部分支持）

**状态**: 🟡 有字幕的视频可用

**支持方式**:
- ✅ **官方字幕提取**（推荐，最稳定）
- ❌ 音频下载（受反爬虫限制）
- ✅ 官方iframe嵌入播放

**使用建议**:
1. **优先选择有字幕的B站视频**
2. 系统会自动提取官方字幕生成笔记
3. 如果视频无字幕，目前暂不支持

**官方嵌入方式**（课堂演示可用）:
```html
<iframe
  src="https://player.bilibili.com/player.html?bvid=BV1xx411c7mD&page=1"
  width="800"
  height="600"
  frameborder="0"
  allowfullscreen>
</iframe>
```

**字幕提取实现**:
```python
# B站字幕API
subtitle_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}"
# 解析subtitle_url中的字幕JSON
```

**为什么不能下载音频？**
- B站在2024年加强了反爬虫策略
- 视频流需要复杂的token和签名
- 即使是专门的工具（you-get, yt-dlp）也经常失败
- **但官方字幕API仍然可用**

---

### 🔧 抖音/TikTok（理论支持，未测试）

**状态**: 🔧 代码支持，但未充分测试

**支持方式**:
- 🔧 yt-dlp下载（理论支持）
- ✅ 官方iframe嵌入

**抖音官方嵌入**:
```javascript
// 通过VideoID获取IFrame代码
// https://developer.open-douyin.com/
```

**TikTok官方嵌入**:
```html
<!-- TikTok oEmbed API -->
https://www.tiktok.com/oembed?url=[VIDEO_URL]
```

**技术实现**:
```bash
# 使用yt-dlp
yt-dlp --cookies-from-browser chrome -g [DOUYIN_URL]
yt-dlp --cookies-from-browser chrome -g [TIKTOK_URL]
```

---

## 实际使用建议

### 课堂演示场景

**最佳实践**:

1. **YouTube视频** → 完美支持，推荐使用
   ```
   直接粘贴链接 → 自动提取字幕/转录 → 生成4种笔记
   ```

2. **B站有字幕视频** → 稳定可靠
   ```
   粘贴链接 → 检测到官方字幕 → 直接生成笔记（秒级完成）
   ```

3. **B站无字幕视频** → 暂不支持
   ```
   系统会提示："该视频没有字幕，暂不支持"
   ```

### 如何找到有字幕的B站视频？

在B站搜索时，筛选条件选择：
- ✅ "有字幕"
- ✅ 最近发布
- ✅ 教程类、演讲类内容（字幕率高）

---

## 技术实现路线图

### 当前架构

```
用户输入URL
    ↓
1. 识别平台（YouTube/B站/抖音等）
    ↓
2. 策略选择
   ├─ YouTube: 字幕API → Whisper转录
   ├─ B站: 字幕API → ❌下载失败
   └─ 其他: yt-dlp尝试
    ↓
3. AI处理
   ├─ 整理笔记
   ├─ 小红书版本
   └─ 博客文章
```

### 未来改进方向

**短期**（可立即实现）:
- [ ] 添加B站字幕检测提示
- [ ] 优化B站字幕提取速度
- [ ] 测试抖音/TikTok支持

**中期**（需要调研）:
- [ ] 探索B站视频下载的合规方案
- [ ] 添加更多平台字幕API支持
- [ ] 支持批量检测字幕可用性

**长期**（需要资源）:
- [ ] 接入第三方B站下载服务API
- [ ] 自建视频处理服务器
- [ ] 支持更多国内外平台

---

## 常见问题 FAQ

### Q1: 为什么B站视频处理失败？

**A**: B站视频失败通常有两个原因：

1. **视频没有字幕**
   - 解决方法：选择有字幕的视频
   - 如何识别：B站播放器右下角有"CC"字幕按钮

2. **视频有地区/权限限制**
   - 某些视频仅限会员或特定地区
   - 系统无法获取这类视频

### Q2: 如何提高成功率？

**YouTube**:
- ✅ 任何公开视频都可以
- ✅ 无需登录
- ✅ 速度快、稳定

**B站**:
- ✅ 选择有字幕的视频（成功率100%）
- ⚠️ 避免无字幕视频
- ⚠️ 避免会员专享视频

### Q3: 能否支持更多平台？

**A**: 理论上，基于yt-dlp可以支持1000+网站，包括：
- Vimeo
- Facebook
- Twitter/X
- Instagram
- 优酷、爱奇艺、腾讯视频
- 等等...

但需要逐个测试验证。

### Q4: 处理时间大概多久？

| 视频时长 | YouTube | B站(有字幕) |
|---------|---------|------------|
| 1-3分钟 | 30-60秒 | 5-10秒 ✨ |
| 3-5分钟 | 1-2分钟 | 10-20秒 ✨ |
| 5-10分钟 | 2-5分钟 | 20-40秒 ✨ |

B站字幕提取非常快，因为不需要下载视频！

---

## 开发者参考

### 添加新平台支持

如果你想添加新平台，需要实现三个方法：

```python
class NewPlatformDownloader(BaseDownloader):
    def supports(self, url: str) -> bool:
        """检查是否支持该URL"""
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

### yt-dlp高级用法

```bash
# 只获取信息，不下载
yt-dlp -J [URL]

# 获取直接播放链接
yt-dlp -g [URL]

# 使用浏览器cookie
yt-dlp --cookies-from-browser chrome [URL]

# 列出所有可用格式
yt-dlp -F [URL]

# 下载最佳音质
yt-dlp -f bestaudio -x --audio-format mp3 [URL]
```

---

## 总结

### 推荐使用优先级

1. 🥇 **YouTube** - 完美支持，强烈推荐
2. 🥈 **B站有字幕** - 超快速度，推荐使用
3. 🥉 **其他平台** - 可以尝试，不保证成功

### 课堂演示建议

准备演示时：
1. 提前准备几个YouTube链接（保底）
2. 找几个有字幕的B站视频（展示速度优势）
3. 测试一遍确保能正常工作

---

**更新时间**: 2025-10-29
**版本**: v2.0
