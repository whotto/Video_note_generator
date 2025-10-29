#!/usr/bin/env python3
"""
视频笔记生成器 - FastAPI Web应用
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from pathlib import Path
import sys
import logging
from datetime import datetime
from typing import List, Optional
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from video_note_generator.config import Settings
from video_note_generator.processor import VideoNoteProcessor
from video_note_generator.utils.cookie_manager import CookieManager

# 创建FastAPI应用
app = FastAPI(
    title="视频笔记生成器",
    description="AI驱动的视频笔记生成工具",
    version="2.0.0"
)

# 挂载静态文件
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 模板配置
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 线程池用于处理视频（避免阻塞异步循环）
executor = ThreadPoolExecutor(max_workers=3)


# ========== 请求/响应模型 ==========

class VideoProcessRequest(BaseModel):
    url: str = Field(..., description="视频URL")
    generate_xiaohongshu: bool = Field(True, description="是否生成小红书笔记")
    generate_blog: bool = Field(True, description="是否生成博客文章")


class VideoProcessResponse(BaseModel):
    success: bool
    message: str
    files: List[str] = []
    error: Optional[str] = None


class BatchProcessRequest(BaseModel):
    urls: List[str] = Field(..., description="视频URL列表")
    generate_xiaohongshu: bool = Field(True, description="是否生成小红书笔记")
    generate_blog: bool = Field(True, description="是否生成博客文章")


class BatchProcessResponse(BaseModel):
    total: int
    success_count: int
    failed_count: int
    results: List[VideoProcessResponse]


class ConfigCheckResponse(BaseModel):
    configured: bool
    message: str
    settings: Optional[dict] = None


# ========== 工具函数 ==========

def get_settings() -> Settings:
    """获取配置"""
    try:
        return Settings()
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        raise


def validate_url(url: str) -> bool:
    """验证URL格式"""
    url = url.strip()
    return url.startswith(('http://', 'https://')) and len(url) > 10


def process_video_sync(
    url: str,
    generate_xiaohongshu: bool,
    generate_blog: bool,
    settings: Settings
) -> VideoProcessResponse:
    """同步处理单个视频（在线程池中运行）"""
    try:
        logger.info(f"开始处理视频: {url}")

        # 创建处理器
        processor = VideoNoteProcessor(settings=settings, logger=logger)

        # 处理视频
        files = processor.process_video(
            url=url,
            generate_xiaohongshu=generate_xiaohongshu,
            generate_blog=generate_blog
        )

        # 转换Path对象为字符串
        file_paths = [str(f) for f in files]

        # 检查是否真的生成了文件
        if not files or len(files) == 0:
            logger.warning(f"视频处理完成但未生成任何文件: {url}")
            return VideoProcessResponse(
                success=False,
                message="处理失败：未生成任何文件",
                error="视频处理过程中出现错误，没有生成笔记文件。可能原因：1) 视频无法下载 2) 音频提取失败 3) 转录失败"
            )

        logger.info(f"视频处理成功: {url}, 生成 {len(files)} 个文件")

        return VideoProcessResponse(
            success=True,
            message=f"成功生成 {len(files)} 个文件",
            files=file_paths
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"处理视频失败: {url}\n{traceback.format_exc()}")

        return VideoProcessResponse(
            success=False,
            message="处理失败",
            error=error_msg
        )


# ========== API路由 ==========

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """返回主页面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/config/check", response_model=ConfigCheckResponse)
async def check_config():
    """检查配置状态"""
    try:
        settings = get_settings()

        # 检查API密钥是否配置
        api_configured = (
            settings.openrouter_api_key and
            settings.openrouter_api_key != "your-api-key-here"
        )

        if api_configured:
            return ConfigCheckResponse(
                configured=True,
                message="API已配置",
                settings={
                    "ai_model": settings.ai_model,
                    "whisper_model": settings.whisper_model,
                    "output_dir": str(settings.output_dir)
                }
            )
        else:
            return ConfigCheckResponse(
                configured=False,
                message="请在.env文件中配置OPENROUTER_API_KEY"
            )

    except Exception as e:
        return ConfigCheckResponse(
            configured=False,
            message=f"配置检查失败: {str(e)}"
        )


@app.post("/api/process", response_model=VideoProcessResponse)
async def process_video(request: VideoProcessRequest):
    """处理单个视频"""
    try:
        # 验证URL
        if not validate_url(request.url):
            raise HTTPException(
                status_code=400,
                detail="无效的URL格式（需以http://或https://开头）"
            )

        # 获取配置
        settings = get_settings()

        # 在线程池中处理视频（避免阻塞事件循环）
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            process_video_sync,
            request.url,
            request.generate_xiaohongshu,
            request.generate_blog,
            settings
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API错误: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/batch-process", response_model=BatchProcessResponse)
async def batch_process(request: BatchProcessRequest):
    """批量处理视频"""
    try:
        # 验证所有URL
        invalid_urls = [url for url in request.urls if not validate_url(url)]
        if invalid_urls:
            raise HTTPException(
                status_code=400,
                detail=f"发现 {len(invalid_urls)} 个无效URL"
            )

        # 获取配置
        settings = get_settings()

        # 处理所有视频
        results = []
        loop = asyncio.get_event_loop()

        for url in request.urls:
            result = await loop.run_in_executor(
                executor,
                process_video_sync,
                url,
                request.generate_xiaohongshu,
                request.generate_blog,
                settings
            )
            results.append(result)

        # 统计结果
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count

        return BatchProcessResponse(
            total=len(request.urls),
            success_count=success_count,
            failed_count=failed_count,
            results=results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量处理错误: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{file_path:path}")
async def download_file(file_path: str):
    """下载生成的文件"""
    try:
        # 安全检查：确保文件在输出目录内
        settings = get_settings()
        full_path = Path(file_path)

        # 检查文件是否存在
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="文件不存在")

        # 检查文件是否在允许的目录内
        if not str(full_path).startswith(str(settings.output_dir)):
            raise HTTPException(status_code=403, detail="禁止访问此文件")

        return FileResponse(
            path=full_path,
            filename=full_path.name,
            media_type='text/markdown'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/file-content/{file_path:path}")
async def get_file_content(file_path: str):
    """获取文件内容（用于预览）"""
    try:
        # 安全检查
        settings = get_settings()
        full_path = Path(file_path)

        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="文件不存在")

        if not str(full_path).startswith(str(settings.output_dir)):
            raise HTTPException(status_code=403, detail="禁止访问此文件")

        # 读取文件内容
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return JSONResponse(content={
            "filename": full_path.name,
            "content": content,
            "size": len(content)
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件读取错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ========== 启动事件 ==========

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("=" * 60)
    logger.info("🚀 视频笔记生成器正在启动...")
    logger.info("=" * 60)

    # 自动检测和导出 cookies
    try:
        settings = Settings()
        cookie_file = settings.cookie_file or "cookies.txt"
        cookie_manager = CookieManager(cookie_file=cookie_file, logger=logger)

        logger.info("\n🍪 检查 Cookies 配置...")
        if not cookie_manager.has_cookies():
            logger.warning("⚠️  未找到 cookies 文件")
            logger.info("🔄 正在自动导出 cookies...")
            logger.info("💡 首次运行需要授权访问浏览器 cookies")
            logger.info("⚠️  请在弹出的授权窗口中点击「始终允许」\n")

            # 尝试自动导出
            success = cookie_manager.auto_setup()

            if success:
                logger.info("✅ Cookies 配置成功！")
                # 更新 .env 文件
                cookie_manager.update_env_file()
            else:
                logger.warning("⚠️  Cookies 自动导出失败")
                logger.warning("💡 您可以稍后手动配置：")
                logger.warning("   python export_cookies.py")
                logger.warning("   或参考文档：QUICK_SETUP.md\n")
        else:
            logger.info(f"✅ 已有 cookies 文件：{cookie_file}")

    except Exception as e:
        logger.error(f"❌ Cookies 初始化失败：{e}")
        logger.warning("💡 程序将继续运行，但可能无法处理某些视频\n")

    logger.info("=" * 60)
    logger.info("✅ 应用启动完成！")
    logger.info("🌐 访问: http://localhost:8001")
    logger.info("=" * 60)


# ========== 启动配置 ==========

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "web_app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
