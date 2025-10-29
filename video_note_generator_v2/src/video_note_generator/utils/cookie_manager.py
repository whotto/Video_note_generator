"""
Cookies 自动管理模块

在程序启动时自动检测和导出 cookies
"""
import os
import subprocess
from pathlib import Path
from typing import Optional


class CookieManager:
    """Cookies 管理器"""

    def __init__(self, cookie_file: str = "cookies.txt", logger=None):
        """
        初始化 Cookie 管理器

        Args:
            cookie_file: Cookies 文件路径
            logger: 日志记录器
        """
        self.cookie_file = Path(cookie_file)
        self.logger = logger

    def has_cookies(self) -> bool:
        """检查是否已有 cookies 文件"""
        return self.cookie_file.exists() and self.cookie_file.stat().st_size > 0

    def export_cookies(self, browser: str = "chrome") -> bool:
        """
        从浏览器导出 cookies

        Args:
            browser: 浏览器名称（chrome, firefox, edge, safari）

        Returns:
            是否成功导出
        """
        if self.logger:
            self.logger.info(f"🍪 正在从 {browser.upper()} 浏览器导出 cookies...")
            self.logger.info("⚠️  首次运行会弹出授权窗口，请点击「始终允许」")

        try:
            # 使用 yt-dlp 导出 cookies
            cmd = [
                "yt-dlp",
                "--cookies-from-browser", browser,
                "--cookies", str(self.cookie_file),
                "--print", "webpage_url",
                "--skip-download",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 60秒超时
                cwd=str(self.cookie_file.parent)
            )

            # 检查是否成功
            if self.cookie_file.exists() and self.cookie_file.stat().st_size > 0:
                if self.logger:
                    self.logger.info(f"✅ Cookies 导出成功！文件：{self.cookie_file}")
                return True
            else:
                if self.logger:
                    if "Sign in to confirm" in result.stderr:
                        self.logger.warning("⚠️  需要登录 YouTube 才能导出 cookies")
                    else:
                        self.logger.error(f"❌ Cookies 导出失败：{result.stderr[:200]}")
                return False

        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.error("❌ 超时：请确保点击了授权窗口的「始终允许」")
            return False
        except FileNotFoundError:
            if self.logger:
                self.logger.error("❌ 错误：yt-dlp 未安装")
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ 导出失败: {e}")
            return False

    def auto_setup(self) -> bool:
        """
        自动设置 cookies

        如果没有 cookies 文件，自动尝试从浏览器导出

        Returns:
            是否成功设置（已有或成功导出）
        """
        # 如果已有 cookies，直接返回
        if self.has_cookies():
            if self.logger:
                self.logger.debug(f"✅ 已有 cookies 文件：{self.cookie_file}")
            return True

        # 尝试导出 cookies
        if self.logger:
            self.logger.warning("⚠️  未找到 cookies 文件")
            self.logger.info("🔄 正在尝试自动导出 cookies...")
            self.logger.info("💡 这是首次运行，需要您授权访问浏览器 cookies")
            self.logger.info("⚠️  请在弹出的授权窗口中点击「始终允许」")

        # 按优先级尝试不同浏览器
        browsers = ["chrome", "edge", "firefox", "safari"]
        for browser in browsers:
            if self.logger:
                self.logger.info(f"🔄 尝试从 {browser.upper()} 导出...")

            if self.export_cookies(browser):
                if self.logger:
                    self.logger.info(f"✅ 成功从 {browser.upper()} 导出 cookies")
                return True

        # 所有浏览器都失败
        if self.logger:
            self.logger.warning("⚠️  自动导出失败")
            self.logger.warning("💡 您可以手动导出 cookies：")
            self.logger.warning("   1. 运行: python export_cookies.py")
            self.logger.warning("   2. 或参考文档: QUICK_SETUP.md")

        return False

    def update_env_file(self) -> bool:
        """更新 .env 文件，添加 COOKIE_FILE 配置"""
        env_file = Path(".env")

        if not env_file.exists():
            return False

        # 读取现有内容
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否已有配置
        if 'COOKIE_FILE' in content and not content.count('# COOKIE_FILE'):
            return True  # 已有配置

        # 添加配置
        with open(env_file, 'a', encoding='utf-8') as f:
            f.write(f"\n# Cookies 配置（自动导出）\n")
            f.write(f"COOKIE_FILE={self.cookie_file}\n")

        if self.logger:
            self.logger.info(f"✅ 已更新 .env 文件：COOKIE_FILE={self.cookie_file}")

        return True
