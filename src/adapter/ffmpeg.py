import subprocess

from src.logger import app_logger


class FfmpegAdapter:
    def __init__(self):
        ffmpeg_path = None
        try:
            subprocess.run(["/opt/homebrew/bin/ffmpeg", "-version"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
            app_logger.info("✅ ffmpeg is available at /opt/homebrew/bin/ffmpeg")
            ffmpeg_path = "/opt/homebrew/bin/ffmpeg"
        except Exception:
            try:
                subprocess.run(["ffmpeg", "-version"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
                app_logger.info("✅ ffmpeg is available (from PATH)")
                ffmpeg_path = "ffmpeg"
            except Exception as e:
                app_logger.warning(f"⚠️ ffmpeg not found: {str(e)}")
        self.ffmpeg_path = ffmpeg_path
