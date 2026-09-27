import os
import subprocess
import json
import uuid
import re
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from .config import find_ffprobe, find_ffmpeg, DOWNLOADS_DIR, TEMP_DIR


def is_url(string_val: str) -> bool:
    """Checks if a string is an HTTP/HTTPS URL."""
    if not string_val:
        return False
    return bool(re.match(r'^https?://', string_val.strip(), re.IGNORECASE))


def probe_local_media(file_path: str) -> Dict[str, Any]:
    """Uses ffprobe to inspect local video or audio duration and streams."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Local file does not exist: {file_path}")

    ffprobe_bin = find_ffprobe()
    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-show_entries", "format=duration,size:stream=width,height,codec_type",
        "-of", "json",
        str(p.resolve())
    ]
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        if res.returncode == 0:
            data = json.loads(res.stdout)
            duration = float(data.get("format", {}).get("duration", 0.0))
            width, height = 1920, 1080
            has_audio = False
            for s in data.get("streams", []):
                if s.get("codec_type") == "video":
                    width = int(s.get("width", 1920))
                    height = int(s.get("height", 1080))
                elif s.get("codec_type") == "audio":
                    has_audio = True
            return {
                "title": p.stem,
                "duration": round(duration, 2),
                "path": str(p.resolve()),
                "is_local": True,
                "width": width,
                "height": height,
                "has_audio": has_audio,
                "thumbnail": None
            }
    except Exception as e:
        print(f"[Downloader] Error probing local file: {e}")

    return {
        "title": p.stem,
        "duration": 0.0,
        "path": str(p.resolve()),
        "is_local": True,
        "width": 1920,
        "height": 1080,
        "thumbnail": None
    }


def fetch_url_info(url: str) -> Dict[str, Any]:
    """Extracts metadata from YouTube or Twitch URL without downloading the video."""
    import yt_dlp

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Online Stream"),
            "duration": float(info.get("duration", 0.0)),
            "thumbnail": info.get("thumbnail"),
            "url": url,
            "is_local": False,
            "uploader": info.get("uploader") or info.get("channel") or "Unknown"
        }


def download_stream(
    url: str,
    output_prefix: str = "stream",
    start_seconds: Optional[float] = None,
    duration_seconds: Optional[float] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> str:
    """
    Downloads YouTube or Twitch stream in 1080p (or best <= 1080p) via yt-dlp.
    If start_seconds and duration_seconds are provided, it downloads ONLY that time slice!
    Returns the absolute path to the downloaded MP4 file.
    """
    import yt_dlp

    output_filename = f"{output_prefix}_{uuid.uuid4().hex[:8]}.mp4"
    output_target = DOWNLOADS_DIR / output_filename

    def yt_hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
            downloaded = d.get("downloaded_bytes", 0)
            pct = round((downloaded / total) * 100.0, 1)
            speed = d.get("_speed_str", "-- MB/s")
            if progress_callback:
                progress_callback(pct, speed)

    from .config import log_error

    ffmpeg_path = find_ffmpeg()
    is_twitch = "twitch.tv" in url.lower()

    ydl_opts = {
        "format": "best[height<=1080]/bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best" if is_twitch else "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        "outtmpl": str(output_target),
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [yt_hook],
        "merge_output_format": "mp4",
        "ffmpeg_location": ffmpeg_path,
        "concurrent_fragment_downloads": 10,
        "retries": 10,
        "fragment_retries": 10,
        "buffersize": 1024 * 1024 * 16,
        "http_chunk_size": 10485760,
    }

    # Slicing optimization: if duration is specified, slice on the fly!
    if duration_seconds is not None and duration_seconds > 0:
        start = max(0.0, start_seconds or 0.0)
        end = start + duration_seconds
        try:
            ydl_opts["download_ranges"] = yt_dlp.utils.download_range_func(None, [(start, end)])
            ydl_opts["force_keyframes_at_cuts"] = True
        except Exception as e:
            print(f"[Downloader] Range cut warning: {e}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        log_error("downloader", f"Download failed for URL: {url}", exc=e)
        raise RuntimeError(f"Download stream error: {e}")

    return str(output_target.resolve())

