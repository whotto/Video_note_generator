# 快速配置 Cookies（解决授权弹窗问题）

## 🎯 问题说明

由于 YouTube 和其他平台的反爬虫机制，需要配置 cookies 才能下载视频。

**症状**：
- ❌ macOS 钥匙串授权窗口频繁弹出
- ❌ "security 想要使用你钥匙串中的 Chrome Safe Storage"
- ❌ YouTube 视频处理失败："Sign in to confirm you're not a bot"

---

## ✅ 一键解决方案

### 方法：运行自动导出脚本

```bash
# 1. 进入项目目录
cd video_note_generator_v2

# 2. 运行 cookies 导出脚本
python export_cookies.py
```

**操作步骤**：
1. 运行脚本后，选择浏览器（推荐选择 1 - Chrome）
2. **重要**：当弹出授权窗口时，点击「**始终允许**」
3. 等待脚本完成，会自动：
   - 导出 cookies 到 `cookies.txt`
   - 更新 `.env` 文件配置
   - 显示成功提示

**结果**：
- ✅ 只需要授权一次
- ✅ 以后不会再弹窗
- ✅ YouTube 和 B站视频都能正常处理

---

## 🎬 导出后的使用

### Web 界面：
1. **重启 Web 服务器**：
   ```bash
   # 停止旧服务器
   pkill -f "python web_app.py"

   # 启动新服务器
   python web_app.py
   ```

2. **刷新浏览器页面** (Cmd+R)

3. **正常使用**，不会再弹窗！

### 命令行：
```bash
# 直接使用，cookies 会自动加载
vnote process https://www.youtube.com/watch?v=xxxxx
```

---

## 🔧 手动导出方法（备选）

如果自动脚本不工作，可以手动导出：

### Chrome/Edge：
1. 安装插件：[Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally)
2. 访问 YouTube 并登录
3. 点击插件图标 → Export
4. 保存为 `cookies.txt`

### Firefox：
1. 安装插件：[cookies.txt](https://addons.mozilla.org/firefox/addon/cookies-txt/)
2. 访问 YouTube 并登录
3. 点击插件图标 → Export
4. 保存为 `cookies.txt`

### 配置：
编辑 `.env` 文件，添加：
```ini
COOKIE_FILE=cookies.txt
```

---

## 📊 验证配置

### 检查 cookies 文件：
```bash
# 查看文件是否存在
ls -lh cookies.txt

# 应该看到类似输出：
# -rw-r--r--  1 user  staff   15K Oct 29 10:00 cookies.txt
```

### 检查 .env 配置：
```bash
grep COOKIE_FILE .env

# 应该看到：
# COOKIE_FILE=cookies.txt
```

### 测试功能：
```bash
# 测试 YouTube 视频
vnote process https://www.youtube.com/watch?v=dQw4w9WgXcQ

# 应该能正常处理，不会弹窗
```

---

## ⚠️ 注意事项

### 安全：
- ✅ cookies.txt 已在 .gitignore 中，不会上传到 GitHub
- ⚠️ 不要分享你的 cookies 文件（包含登录信息）
- 🔒 定期更新 cookies（建议每月一次）

### cookies 过期：
如果一段时间后又出现错误，重新运行：
```bash
python export_cookies.py
```

### 多个浏览器：
可以尝试不同的浏览器导出 cookies：
```bash
python export_cookies.py
# 选择: 1=Chrome, 2=Firefox, 3=Edge, 4=Safari
```

---

## 🆘 常见问题

### Q: 运行脚本后还是失败？
**A**: 确保：
1. 浏览器已登录 YouTube
2. 点击了「始终允许」而不是「允许」
3. cookies.txt 文件存在且不为空
4. 重启了 Web 服务器

### Q: 可以不配置 cookies 吗？
**A**: 可以，但会受限：
- ✅ Bilibili 字幕提取仍然可用
- ❌ YouTube 视频下载可能失败
- ❌ 需要登录的视频无法处理

### Q: cookies 文件在哪里？
**A**: 在项目根目录：
```
video_note_generator_v2/
├── cookies.txt        # 这里
├── .env
├── export_cookies.py
└── ...
```

### Q: 多久需要更新一次 cookies？
**A**: 建议每月更新一次，或当出现授权错误时更新。

---

## 📞 需要帮助？

如果仍然有问题：
1. 查看详细指南：[COOKIES_GUIDE.md](COOKIES_GUIDE.md)
2. 查看错误日志：`tail -100 /tmp/web_app.log`
3. 提交 Issue：[GitHub Issues](https://github.com/whotto/Video_note_generator/issues)

---

**更新时间**: 2024-10-29
