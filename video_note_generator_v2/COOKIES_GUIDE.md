# Cookies 配置指南

## 为什么需要配置 Cookies？

大多数公开视频（如 YouTube）**不需要** cookies 就可以下载。但以下情况需要配置 cookies：

1. ✅ **YouTube** 公开视频 → 不需要 cookies
2. ⚠️ **Bilibili** 部分视频 → 可能需要 cookies（会员视频、地区限制等）
3. 🔒 **需要登录的视频** → 必须配置 cookies

---

## 如何导出 Cookies？

### 方法一：使用浏览器插件（推荐）

#### Chrome / Edge 用户：

1. **安装插件**：
   - 打开 Chrome Web Store
   - 搜索 **"Get cookies.txt LOCALLY"**
   - 点击"添加到 Chrome"

2. **导出 Cookies**：
   - 访问目标网站（如 bilibili.com）并登录
   - 点击浏览器右上角的插件图标
   - 点击 "Export" 按钮
   - 保存为 `cookies.txt` 文件

#### Firefox 用户：

1. **安装插件**：
   - 打开 Firefox Add-ons
   - 搜索 **"cookies.txt"**
   - 点击"添加到 Firefox"

2. **导出 Cookies**：
   - 访问目标网站并登录
   - 点击浏览器右上角的插件图标
   - 点击 "Export" 按钮
   - 保存为 `cookies.txt` 文件

---

### 方法二：使用开发者工具（高级）

1. **打开开发者工具**：
   - 按 `F12` 或右键 → "检查"
   - 切换到 "Application" 或 "存储" 标签

2. **查看 Cookies**：
   - 左侧菜单选择 "Cookies"
   - 选择目标网站
   - 手动复制所需的 cookie 信息

3. **转换为 Netscape 格式**：
   - 使用在线工具或脚本转换为 Netscape 格式
   - 保存为 `.txt` 文件

---

## 如何配置 Cookies？

### 步骤 1：保存 Cookies 文件

将导出的 `cookies.txt` 文件保存到项目目录或安全位置：

```bash
# 推荐位置（项目根目录）
video_note_generator_v2/
├── cookies.txt        # 你的 cookies 文件
├── .env               # 配置文件
├── ...
```

**⚠️ 重要提醒**：
- Cookies 文件包含敏感信息，**不要上传到 GitHub**
- `.gitignore` 已自动排除 `cookies.txt`

---

### 步骤 2：配置 .env 文件

编辑 `.env` 文件，添加以下配置：

```ini
# Cookies 配置（可选）
COOKIE_FILE=cookies.txt

# 或使用绝对路径
# COOKIE_FILE=/Users/your-name/path/to/cookies.txt
```

**配置说明**：
- 相对路径：从项目根目录开始
- 绝对路径：完整文件路径（推荐 Windows 用户）

---

### 步骤 3：验证配置

运行以下命令测试：

```bash
# 测试 YouTube 视频（不需要 cookies）
vnote process https://www.youtube.com/watch?v=xxxxx

# 测试 Bilibili 视频（可能需要 cookies）
vnote process https://www.bilibili.com/video/BVxxxxxxx
```

如果配置成功，你会在日志中看到：

```
DEBUG: 使用cookies文件: cookies.txt
```

---

## 常见问题

### Q1: 配置 cookies 后仍然弹出授权窗口？

**A**: 请检查：
1. `.env` 文件中的 `COOKIE_FILE` 路径是否正确
2. `cookies.txt` 文件是否存在
3. 重启终端或 IDE，确保环境变量生效

---

### Q2: Cookies 文件格式错误？

**A**: 确保导出的是 **Netscape 格式**：

```
# Netscape HTTP Cookie File
# This is a generated file! Do not edit.
.bilibili.com	TRUE	/	FALSE	1234567890	cookie_name	cookie_value
```

如果格式不对，重新使用推荐的浏览器插件导出。

---

### Q3: Cookies 过期了怎么办？

**A**: Cookies 有时效性，过期后需要：
1. 重新登录目标网站
2. 重新导出 cookies 文件
3. 替换旧的 `cookies.txt`

建议每个月更新一次 cookies。

---

### Q4: 是否可以同时配置多个网站的 Cookies？

**A**: 可以！在同一个 `cookies.txt` 文件中可以包含多个网站的 cookies：

```
# YouTube Cookies
.youtube.com	TRUE	/	FALSE	1234567890	cookie1	value1

# Bilibili Cookies
.bilibili.com	TRUE	/	FALSE	1234567890	cookie2	value2
```

---

### Q5: 不配置 Cookies 有什么影响？

**A**:
- ✅ **YouTube 公开视频**：完全没有影响
- ⚠️ **Bilibili 公开视频**：可以提取字幕，但无法下载音频
- ❌ **需要登录的视频**：无法下载

---

## 安全建议

1. **不要分享你的 cookies 文件**：包含登录信息
2. **定期更新 cookies**：避免过期和安全风险
3. **使用专用账号**：不要使用主账号的 cookies
4. **不要上传到公开仓库**：确保 `.gitignore` 已排除

---

## 推荐的浏览器插件

### Chrome / Edge:
- **Get cookies.txt LOCALLY**
  - ✅ 安全（本地处理）
  - ✅ Netscape 格式
  - ✅ 一键导出

### Firefox:
- **cookies.txt**
  - ✅ 开源
  - ✅ Netscape 格式
  - ✅ 简单易用

---

## 总结

| 使用场景 | 是否需要 Cookies | 推荐方案 |
|---------|----------------|---------|
| YouTube 公开视频 | ❌ 不需要 | 不配置 |
| Bilibili 公开视频（有字幕） | ❌ 不需要 | 不配置 |
| Bilibili 视频下载 | ✅ 可能需要 | 配置 cookies |
| 需要登录的视频 | ✅ 必须 | 配置 cookies |

**最佳实践**：
- 日常使用 YouTube → 不配置 cookies
- 需要处理 Bilibili 或其他平台 → 按需配置

---

**更新时间**: 2024-10-29
**版本**: v2.0
