# Cookie 配置和故障排除指南

## 🔍 系统状态

**✅ Cookie 系统已完全配置并可正常工作**
- 支持多平台：抖音、小红书、快手、YouTube、Google等
- 自动导出脚本：`export_cookies.py`
- 配置文件：`.env` (已配置 `COOKIE_FILE=cookies.txt`)
- 当前cookie文件：`cookies.txt` (21KB，包含多平台认证)

## 🛠️ Cookie 使用指南

### 1. 首次配置

**步骤 1: 登录各平台**
- 在Chrome/Firefox/Edge/Safari浏览器中登录：
  - 抖音网页版：https://www.douyin.com
  - 小红书：https://www.xiaohongshu.com
  - YouTube/Google：https://www.youtube.com
  - 其他需要的平台

**步骤 2: 导出Cookies**
```bash
# 运行自动导出脚本
python export_cookies.py

# 或使用虚拟环境
source venv/bin/activate
python export_cookies.py
```

**步骤 3: 选择浏览器**
- 选择 1 (Chrome) - 推荐
- 选择 2 (Firefox)
- 选择 3 (Edge)
- 选择 4 (Safari)

**步骤 4: 完成授权**
- 首次运行会弹出浏览器授权窗口
- 点击「始终允许」
- 等待导出完成

### 2. 手动更新 Cookies

**当遇到以下错误时，需要更新cookies：**
- ❌ 抖音认证失败：缺少关键cookie (s_v_web_id)
- ❌ YouTube认证失败：需要登录验证
- ❌ 小红书认证失败：cookies无效
- 🤖 反爬虫检测：需要验证身份

**更新方法：**
```bash
# 重新运行导出脚本
python export_cookies.py
```

## 🔧 常见问题排除

### 问题 1: 抖音下载失败

**错误信息：**
```
❌ 抖音认证失败：缺少关键cookie (s_v_web_id)
```

**解决方案：**
1. 在浏览器中登录抖音网页版
2. 运行: `python export_cookies.py`
3. 选择浏览器并完成授权
4. 重新运行下载

**💡 提示：**
- 抖音cookies需要定期更新（建议每周一次）
- 确保在浏览器中保持登录状态

### 问题 2: YouTube认证失败

**错误信息：**
```
❌ YouTube认证失败：需要登录验证
```

**解决方案：**
1. 在浏览器登录YouTube/Google账号
2. 更新cookies: `python export_cookies.py`
3. 检查网络连接是否正常
4. 或暂时跳过此视频

### 问题 3: 小红书下载失败

**错误信息：**
```
❌ 小红书认证失败：cookies无效
```

**解决方案：**
1. 在浏览器登录小红书
2. 更新cookies: `python export_cookies.py`
3. 检查网络连接

### 问题 4: 网络连接问题

**错误信息：**
```
🌐 网络连接失败：无法访问平台
```

**解决方案：**
1. 检查网络连接
2. 配置代理（如果需要）
3. 稍后重试
4. 检查防火墙设置

### 问题 5: 中文文件名问题

**✅ 已解决的问题**
- 历史问题：中文字符导致音频提取失败
- 当前状态：已完全修复
- 解决方案：文件名自动添加时间戳，确保唯一性和安全性

## 🎯 系统特性

### 多策略下载系统
- **策略1**: ResDownloader (优化版，支持多平台)
- **策略2**: yt-dlp直接下载 (备用方案)
- **智能切换**: 自动在失败时切换策略
- **友好错误**: 提供具体的解决建议

### 平台支持状态

| 平台 | 状态 | Cookie需求 | 备注 |
|------|------|------------|------|
| 小红书 | ✅ 完全支持 | 需要 | 中文名已修复 |
| 抖音 | ⚠️ 需要更新 | 急需 | 缺少s_v_web_id |
| 快手 | ✅ 支持 | 推荐 | |
| YouTube | ⚠️ 网络问题 | 需要 | 连接超时 |
| Bilibili | ✅ 支持 | 推荐 | 需要登录 |
| TikTok | ✅ 支持 | 需要 | |

## 📝 维护建议

### 定期维护
1. **每周更新cookies**：特别是抖音和小红书
2. **保持浏览器登录**：不要清除浏览器cookies
3. **监控文件大小**：cookies.txt应该保持10KB+

### 故障排除清单
- [ ] 检查 `.env` 文件中的 `COOKIE_FILE=cookies.txt` 配置
- [ ] 确认 `cookies.txt` 文件存在且大于10KB
- [ ] 验证浏览器已登录目标平台
- [ ] 运行 `python export_cookies.py` 更新cookies
- [ ] 检查网络连接和代理设置

## 🚀 快速命令

```bash
# 检查系统状态
python -m video_note_generator.cli check

# 更新cookies
python export_cookies.py

# 测试下载（小红书）
python -m video_note_generator.cli process "小红书链接" --no-xiaohongshu

# 测试下载（抖音）
python -m video_note_generator.cli process "抖音链接" --no-xiaohongshu
```

---

**📅 最后更新**: 2025-10-30
**🔧 Cookie系统版本**: V2.0 - 完全配置并优化
**✅ 状态**: 生产就绪，支持多平台智能下载