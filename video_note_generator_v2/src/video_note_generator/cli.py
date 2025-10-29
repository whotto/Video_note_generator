"""
命令行界面
"""
import sys
from pathlib import Path
from typing import List
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import get_settings
from .utils.logger import setup_logger
from .utils.text_utils import extract_urls
from .processor import VideoNoteProcessor

console = Console()


@click.group()
@click.version_option(version="2.0.0")
def cli():
    """视频笔记生成器 V2 - 将视频转换为优质笔记"""
    pass


@cli.command()
@click.argument('input_source')
@click.option('--no-xiaohongshu', is_flag=True, help='不生成小红书版本')
@click.option('--config', type=click.Path(exists=True), help='配置文件路径')
def process(input_source: str, no_xiaohongshu: bool, config: str):
    """
    处理视频链接或包含链接的文件

    INPUT_SOURCE 可以是:
    - 单个视频 URL
    - 包含 URL 的文本文件
    - Markdown 文件（自动提取链接）
    """
    # 加载配置
    settings = get_settings()

    # 设置日志
    logger = setup_logger(
        name="video_note_generator",
        log_dir=settings.log_dir,
        log_level=settings.log_level
    )

    console.print("[bold green]视频笔记生成器 V2[/bold green]\n")

    # 解析输入源
    urls = _parse_input_source(input_source)

    if not urls:
        console.print("[red]错误：未找到有效的视频链接[/red]")
        sys.exit(1)

    console.print(f"[cyan]找到 {len(urls)} 个视频链接[/cyan]\n")

    # 创建处理器
    processor = VideoNoteProcessor(settings=settings, logger=logger)

    # 处理视频
    generate_xiaohongshu = not no_xiaohongshu

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for i, url in enumerate(urls, 1):
            task = progress.add_task(
                f"[cyan]处理视频 {i}/{len(urls)}...",
                total=None
            )

            console.print(f"\n[yellow]正在处理:[/yellow] {url}")

            try:
                files = processor.process_video(url, generate_xiaohongshu)

                if files:
                    console.print(f"[green]✓ 成功生成 {len(files)} 个文件:[/green]")
                    for file in files:
                        console.print(f"  - {file}")
                else:
                    console.print("[red]✗ 处理失败[/red]")

            except Exception as e:
                console.print(f"[red]✗ 错误: {e}[/red]")
                logger.error(f"处理视频失败: {url}", exc_info=True)

            progress.remove_task(task)

    console.print("\n[bold green]处理完成！[/bold green]")


@cli.command()
def check():
    """检查环境配置"""
    from .utils.logger import get_logger

    logger = get_logger()
    console.print("[bold]检查环境配置...[/bold]\n")

    # 检查配置
    try:
        settings = get_settings()
        console.print("[green]✓ 配置文件加载成功[/green]")

        # 检查必要的 API 密钥
        if settings.openrouter_api_key:
            console.print("[green]✓ OpenRouter API 密钥已配置[/green]")
        else:
            console.print("[red]✗ OpenRouter API 密钥未配置[/red]")

        if settings.unsplash_access_key:
            console.print("[green]✓ Unsplash API 密钥已配置[/green]")
        else:
            console.print("[yellow]⚠ Unsplash API 密钥未配置（图片功能将不可用）[/yellow]")

        # 检查目录
        console.print(f"\n[cyan]输出目录:[/cyan] {settings.output_dir}")
        console.print(f"[cyan]缓存目录:[/cyan] {settings.cache_dir}")
        console.print(f"[cyan]日志目录:[/cyan] {settings.log_dir}")

        # 检查 Whisper 模型
        console.print(f"\n[cyan]Whisper 模型:[/cyan] {settings.whisper_model}")
        console.print(f"[cyan]AI 模型:[/cyan] {settings.ai_model}")

    except Exception as e:
        console.print(f"[red]✗ 配置检查失败: {e}[/red]")
        sys.exit(1)

    console.print("\n[bold green]环境检查完成！[/bold green]")


def _parse_input_source(input_source: str) -> List[str]:
    """
    解析输入源，提取视频URL

    Args:
        input_source: 输入源（URL 或文件路径）

    Returns:
        URL 列表
    """
    # 检查是否是文件
    if Path(input_source).exists():
        try:
            with open(input_source, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试 GBK 编码
            with open(input_source, 'r', encoding='gbk') as f:
                content = f.read()

        # 提取 URL
        return extract_urls(content)

    # 检查是否是有效的 URL
    elif input_source.startswith(('http://', 'https://')):
        return [input_source]

    else:
        console.print(f"[red]错误：无法识别的输入源: {input_source}[/red]")
        return []


def main():
    """主入口"""
    cli()


if __name__ == '__main__':
    main()
