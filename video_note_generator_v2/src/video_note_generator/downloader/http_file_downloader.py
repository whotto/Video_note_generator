"""
基于 res-downloader 思路实现的多线程 HTTP 文件下载器

实现要点：
- 先执行 HEAD 请求探测文件大小、是否支持 Range 分段
- 若支持 Range 且文件较大，则按分片并行下载
- 下载过程保留调用者提供的 headers/proxies 以兼容反爬策略
"""
from __future__ import annotations

import math
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Dict, Optional

import httpx


class DownloadError(Exception):
    """下载失败异常"""


ProgressCallback = Callable[[int, Optional[int]], None]


class HttpFileDownloader:
    """多线程 HTTP 下载器"""

    _MIN_CHUNK_SIZE = 1 * 1024 * 1024  # 1MB
    _MAX_RETRIES = 3

    def __init__(
        self,
        url: str,
        target_path: Path,
        headers: Optional[Dict[str, str]] = None,
        proxies: Optional[Dict[str, str]] = None,
        max_workers: int = 4,
        chunk_size: int = _MIN_CHUNK_SIZE,
        timeout: float = 30.0,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        self.url = url
        self.target_path = Path(target_path)
        self.headers = headers.copy() if headers else {}
        self.proxies = proxies
        self.max_workers = max(1, max_workers)
        self.chunk_size = max(chunk_size, self._MIN_CHUNK_SIZE)
        self.timeout = timeout
        self.progress_callback = progress_callback

        self._total_size: Optional[int] = None
        self._support_range = False
        self._downloaded = 0
        self._download_lock = threading.Lock()
        self._file_lock = threading.Lock()

    def _build_client(self) -> httpx.Client:
        client_kwargs = {
            'headers': self.headers,
            'follow_redirects': True,
            'timeout': self.timeout,
        }

        # 兼容不同版本的 httpx
        if self.proxies:
            try:
                # 新版本 httpx 使用 proxy 参数
                return httpx.Client(proxy=self.proxies, **client_kwargs)
            except TypeError:
                # 旧版本 httpx 使用 proxies 参数
                client_kwargs['proxies'] = self.proxies
                return httpx.Client(**client_kwargs)
        else:
            return httpx.Client(**client_kwargs)

    def _probe(self) -> None:
        """执行 HEAD 请求探测下载能力"""
        with self._build_client() as client:
            response = client.head(self.url)
            response.raise_for_status()

            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    self._total_size = int(content_length)
                except ValueError:
                    self._total_size = None
            accept_ranges = response.headers.get("Accept-Ranges", "")
            self._support_range = (
                self._total_size is not None
                and self._total_size > self.chunk_size
                and "bytes" in accept_ranges.lower()
            )

    def _ensure_target_file(self) -> None:
        self.target_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "wb"
        if self._support_range and self._total_size is not None:
            mode = "r+b"
        if not self.target_path.exists():
            with open(self.target_path, "wb") as f:
                if self._support_range and self._total_size:
                    f.truncate(self._total_size)
        self._file_handle = open(self.target_path, mode)

    def _close_file(self) -> None:
        if hasattr(self, "_file_handle") and self._file_handle:
            self._file_handle.close()

    def _report_progress(self, chunk_size: int) -> None:
        if not self.progress_callback:
            return
        with self._download_lock:
            self._downloaded += chunk_size
            self.progress_callback(self._downloaded, self._total_size)

    def _download_range(self, start: int, end: Optional[int]) -> None:
        attempt = 0
        while attempt < self._MAX_RETRIES:
            attempt += 1
            try:
                headers = self.headers.copy()
                if end is not None:
                    headers["Range"] = f"bytes={start}-{end}"
                else:
                    headers["Range"] = f"bytes={start}-"

                with self._build_client().stream("GET", self.url, headers=headers) as resp:
                    resp.raise_for_status()
                    offset = start
                    for chunk in resp.iter_bytes(1024 * 64):
                        if not chunk:
                            continue
                        with self._file_lock:
                            self._file_handle.seek(offset)
                            self._file_handle.write(chunk)
                        offset += len(chunk)
                        self._report_progress(len(chunk))
                return
            except Exception as exc:  # pylint: disable=broad-except
                if attempt >= self._MAX_RETRIES:
                    raise DownloadError(f"下载 range {start}-{end} 失败: {exc}") from exc

    def _download_single(self) -> None:
        attempt = 0
        while attempt < self._MAX_RETRIES:
            attempt += 1
            try:
                with self._build_client().stream("GET", self.url) as resp:
                    resp.raise_for_status()
                    with open(self.target_path, "wb") as out:
                        for chunk in resp.iter_bytes(1024 * 64):
                            if not chunk:
                                continue
                            out.write(chunk)
                            self._report_progress(len(chunk))
                return
            except Exception as exc:  # pylint: disable=broad-except
                if attempt >= self._MAX_RETRIES:
                    raise DownloadError(f"下载失败: {exc}") from exc

    def download(self) -> Path:
        """执行下载"""
        try:
            self._probe()

            if not self._support_range:
                self._download_single()
                return self.target_path

            self._ensure_target_file()

            assert self._total_size is not None  # for type checker
            ranges = []
            parts = math.ceil(self._total_size / self.chunk_size)
            workers = min(self.max_workers, parts)

            for idx in range(parts):
                start = idx * self.chunk_size
                end = min(start + self.chunk_size - 1, self._total_size - 1)
                ranges.append((start, end))

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(self._download_range, start, end) for start, end in ranges]
                for future in as_completed(futures):
                    future.result()

            return self.target_path
        finally:
            self._close_file()

