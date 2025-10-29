#!/usr/bin/env python3
"""
自动从浏览器导出 Cookies 脚本

使用方法：
    python export_cookies.py

功能：
    - 自动从 Chrome/Firefox 浏览器导出 cookies
    - 保存为 Netscape 格式的 cookies.txt
    - 只需授权一次，之后不会再弹窗
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header():
    """打印脚本头部信息"""
    print("=" * 60)
    print("🍪 视频笔记生成器 - Cookies 导出工具")
    print("=" * 60)
    print()


def check_yt_dlp():
    """检查 yt-dlp 是否安装"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ yt-dlp 版本: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 错误：yt-dlp 未安装")
        print("\n请先安装 yt-dlp：")
        print("  pip install yt-dlp")
        return False


def export_cookies(browser="chrome", output_file="cookies.txt"):
    """
    从浏览器导出 cookies

    Args:
        browser: 浏览器名称（chrome, firefox, edge, safari）
        output_file: 输出文件路径
    """
    print(f"\n📦 从 {browser.upper()} 浏览器导出 cookies...")
    print("⚠️  首次运行会弹出授权窗口，请点击「始终允许」")
    print()

    # 使用 yt-dlp 导出 cookies
    try:
        cmd = [
            "yt-dlp",
            "--cookies-from-browser", browser,
            "--cookies", output_file,
            "--print", "webpage_url",
            "--skip-download",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # 任意 YouTube 视频
        ]

        print(f"🔄 执行命令: {' '.join(cmd[:4])}...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        # 检查输出文件是否存在
        if Path(output_file).exists():
            file_size = Path(output_file).stat().st_size
            print(f"\n✅ Cookies 导出成功！")
            print(f"📄 文件位置: {Path(output_file).absolute()}")
            print(f"📊 文件大小: {file_size} 字节")
            return True
        else:
            print(f"\n❌ 导出失败")
            if result.stderr:
                print(f"错误信息: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("\n❌ 超时：请确保点击了授权窗口")
        return False
    except Exception as e:
        print(f"\n❌ 导出失败: {e}")
        return False


def update_env_file(cookie_file="cookies.txt"):
    """更新 .env 文件，添加 COOKIE_FILE 配置"""
    env_file = Path(".env")

    if not env_file.exists():
        print("\n⚠️  警告：.env 文件不存在")
        print("请根据 .env.example 创建 .env 文件")
        return False

    # 读取现有内容
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 检查是否已有 COOKIE_FILE 配置
    has_cookie_config = any('COOKIE_FILE' in line and not line.strip().startswith('#') for line in lines)

    if has_cookie_config:
        print("\n✅ .env 文件已包含 COOKIE_FILE 配置")
        return True

    # 添加配置
    with open(env_file, 'a', encoding='utf-8') as f:
        f.write(f"\n# Cookies 配置（自动导出）\n")
        f.write(f"COOKIE_FILE={cookie_file}\n")

    print(f"\n✅ 已更新 .env 文件，添加配置：COOKIE_FILE={cookie_file}")
    return True


def main():
    """主函数"""
    print_header()

    # 检查 yt-dlp
    if not check_yt_dlp():
        sys.exit(1)

    print("\n🌐 支持的浏览器:")
    print("  1. Chrome (推荐)")
    print("  2. Firefox")
    print("  3. Edge")
    print("  4. Safari")

    # 选择浏览器
    browser_choice = input("\n请选择浏览器 [1-4] (默认: 1): ").strip()

    browsers = {
        "1": "chrome",
        "2": "firefox",
        "3": "edge",
        "4": "safari",
        "": "chrome"  # 默认
    }

    browser = browsers.get(browser_choice, "chrome")

    # 导出 cookies
    output_file = "cookies.txt"
    success = export_cookies(browser, output_file)

    if not success:
        print("\n💡 提示:")
        print("  1. 确保浏览器已登录 YouTube")
        print("  2. 点击授权窗口中的「始终允许」按钮")
        print("  3. 如果使用 Chrome，可以尝试其他浏览器")
        sys.exit(1)

    # 更新 .env 文件
    update_env_file(output_file)

    print("\n" + "=" * 60)
    print("🎉 配置完成！")
    print("=" * 60)
    print("\n现在可以正常使用视频笔记生成器了，不会再弹出授权窗口。")
    print("\n💡 建议每个月重新运行此脚本更新 cookies")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
