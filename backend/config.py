import sys
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

import threading

# Frozen / Standalone Execution Path Resolution
IS_FROZEN = getattr(sys, "frozen", False)
if IS_FROZEN:
    EXE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", EXE_DIR / "_internal"))
else:
    EXE_DIR = Path(__file__).resolve().parent.parent
    BUNDLE_DIR = EXE_DIR

BASE_DIR = EXE_DIR

# Robust Frontend & Binary Directory Resolution
if (BUNDLE_DIR / "frontend").exists():
    FRONTEND_DIR = BUNDLE_DIR / "frontend"
elif (EXE_DIR / "frontend").exists():
    FRONTEND_DIR = EXE_DIR / "frontend"
else:
    FRONTEND_DIR = BASE_DIR / "frontend"

if (BUNDLE_DIR / "bin").exists():
    BIN_DIR = BUNDLE_DIR / "bin"
elif (EXE_DIR / "bin").exists():
    BIN_DIR = EXE_DIR / "bin"
else:
    BIN_DIR = BASE_DIR / "bin"


def _resolve_data_dir() -> Path:
    """
    Selects a writable data directory:
    1. Portable: EXE_DIR / 'data' (if writable)
    2. Fallback: %LOCALAPPDATA%/StreamMixStudio/data (if EXE_DIR is read-only or in Program Files)
    """
    target = EXE_DIR / "data"
    try:
        target.mkdir(parents=True, exist_ok=True)
        test_file = target / ".write_probe"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return target
    except Exception:
        pass

    local_app_data = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    user_data = Path(local_app_data) / "StreamMixStudio" / "data"
    user_data.mkdir(parents=True, exist_ok=True)
    return user_data


DATA_DIR = _resolve_data_dir()
OUTPUT_DIR = DATA_DIR / "outputs"
TEMP_DIR = DATA_DIR / "temp"
DOWNLOADS_DIR = DATA_DIR / "downloads"
AVATARS_DIR = DATA_DIR / "avatars"
BGM_DIR = DATA_DIR / "bgm"
FONTS_DIR = DATA_DIR / "fonts"
SETTINGS_FILE = DATA_DIR / "settings.json"
API_KEYS_FILE = DATA_DIR / "api_keys.json"
LOGS_DIR = DATA_DIR / "logs"
ERROR_LOG_FILE = LOGS_DIR / "error.log"

for directory in [DATA_DIR, OUTPUT_DIR, TEMP_DIR, DOWNLOADS_DIR, AVATARS_DIR, BGM_DIR, FONTS_DIR, LOGS_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

# Seed default bundled assets (avatars, fonts, etc.) if missing in DATA_DIR
for seed_src in [BUNDLE_DIR / "data", EXE_DIR / "data"]:
    if seed_src.exists() and seed_src != DATA_DIR:
        for sub in ["fonts", "avatars", "bgm"]:
            src_sub = seed_src / sub
            dst_sub = DATA_DIR / sub
            if src_sub.exists() and src_sub.is_dir():
                dst_sub.mkdir(parents=True, exist_ok=True)
                for f in src_sub.glob("*"):
                    if f.is_file() and not (dst_sub / f.name).exists():
                        try:
                            shutil.copy2(f, dst_sub / f.name)
                        except Exception:
                            pass

# Prepend portable bin/ directory to system PATH so yt-dlp and FFmpeg are detected
bin_str = str(BIN_DIR.resolve())
if bin_str not in os.environ.get("PATH", ""):
    os.environ["PATH"] = bin_str + os.pathsep + os.environ.get("PATH", "")


def ensure_bundled_fonts():
    """Ensures required viral fonts (Poppins Black, Outfit ExtraBold, Montserrat Black, etc.) are present in data/fonts without blocking startup."""
    font_urls = {
        "Poppins.ttf": "https://fonts.gstatic.com/s/poppins/v24/pxiByp8kv8JHgFVrLBT5V1s.ttf",
        "Outfit.ttf": "https://fonts.gstatic.com/s/outfit/v15/QGYyz_MVcBeNP4NjuGObqx1XmO1I4bCyC4E.ttf",
        "Montserrat.ttf": "https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCvC70w-.ttf",
        "Montserrat-Bold.ttf": "https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCvC70w-.ttf",
        "Montserrat-Black.ttf": "https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCvC70w-.ttf"
    }

    # First check if fonts exist in BUNDLE_DIR or EXE_DIR and copy them
    for seed_dir in [BUNDLE_DIR / "data" / "fonts", EXE_DIR / "data" / "fonts"]:
        if seed_dir.exists():
            for fname in font_urls:
                src_font = seed_dir / fname
                dst_font = FONTS_DIR / fname
                if src_font.exists() and not dst_font.exists():
                    try:
                        shutil.copy2(src_font, dst_font)
                    except Exception:
                        pass

    def _bg_download():
        import urllib.request
        for fname, url in font_urls.items():
            dest = FONTS_DIR / fname
            if not dest.exists() or dest.stat().st_size < 10000:
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=5) as resp, open(dest, "wb") as f:
                        f.write(resp.read())
                except Exception:
                    pass

    # Launch font verification in non-blocking background thread so startup is instant (0ms)
    threading.Thread(target=_bg_download, daemon=True).start()

ensure_bundled_fonts()



def log_error(module: str, message: str, exc: Optional[Exception] = None, task_id: Optional[str] = None):
    """Writes detailed timestamped error messages and tracebacks to data/logs/error.log."""
    import datetime
    import traceback

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tid_str = f" [Task: {task_id}]" if task_id else ""
    log_entry = [f"\n{'='*70}\n[{timestamp}] [{module.upper()}]{tid_str} ERROR: {message}"]
    if exc:
        log_entry.append(f"Exception Type: {type(exc).__name__}")
        log_entry.append(f"Exception Message: {str(exc)}")
        tb_str = traceback.format_exc()
        if tb_str and tb_str.strip() != "NoneType: None":
            log_entry.append("Traceback:\n" + tb_str.strip())
    log_entry.append("=" * 70)
    formatted = "\n".join(log_entry) + "\n"

    try:
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted)
    except Exception as io_err:
        print(f"[Logger] Failed to write to {ERROR_LOG_FILE}: {io_err}")

    # Also output to stderr for immediate terminal visibility
    print(f"[{timestamp}] [{module.upper()}] ERROR: {message} ({exc or ''})", file=sys.stderr)


def get_recent_logs(max_lines: int = 250) -> str:
    """Returns recent lines from data/logs/error.log."""
    if not ERROR_LOG_FILE.exists():
        return "No errors logged yet. System running smoothly."
    try:
        with open(ERROR_LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            return "".join(lines[-max_lines:])
    except Exception as e:
        return f"Error reading log file: {e}"


def clear_logs() -> bool:
    """Clears the error.log file."""
    try:
        with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")
        return True
    except Exception:
        return False

DEFAULT_SETTINGS: Dict[str, Any] = {
    "hardware_encoder": "auto",  # auto, h264_nvenc, h264_qsv, h264_amf, libx264
    "bitrate_mode": "6500k",
    "resolution": "1920x1080",
    "fps": 60,
    "default_bg_blur": 18,
    "default_yt_opacity": 35,
    "default_audio_speed": 1.0,
    "default_pitch_semitones": 0.0,
    "default_bgm_volume": 0.07,
    "copyright_shield": True,
    "auto_open_folder": True,
    "cleanup_temp": True
}

DEFAULT_API_KEYS: Dict[str, Any] = {
    "active_key_index": 0,
    "keys": [],
    "pexels_api_key": "",
    "pixabay_api_key": "",
    "gemini_api_keys": []
}


def find_ffmpeg() -> str:
    """Finds path to ffmpeg executable with portable ./bin priority."""
    candidates = [
        BIN_DIR / "ffmpeg.exe",
        BIN_DIR / "ffmpeg",
        BASE_DIR / "ffmpeg.exe"
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    system_path = shutil.which("ffmpeg")
    return system_path or "ffmpeg"


def find_ffprobe() -> str:
    """Finds path to ffprobe executable with portable ./bin priority."""
    candidates = [
        BIN_DIR / "ffprobe.exe",
        BIN_DIR / "ffprobe",
        BASE_DIR / "ffprobe.exe"
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    system_path = shutil.which("ffprobe")
    return system_path or "ffprobe"


_CACHED_HARDWARE_ENCODER = None

def detect_hardware_encoder() -> str:
    """
    Tests FFmpeg against available hardware encoders (NVENC, QSV, AMF, CPU)
    and returns the best supported encoder string. Caches result for instant 0ms retrieval.
    """
    global _CACHED_HARDWARE_ENCODER
    if _CACHED_HARDWARE_ENCODER is not None:
        return _CACHED_HARDWARE_ENCODER

    ffmpeg_bin = find_ffmpeg()
    encoders_to_test = [
        ("h264_nvenc", "Nvidia NVENC"),
        ("h264_qsv", "Intel QuickSync (QSV)"),
        ("h264_amf", "AMD AMF"),
        ("h264_mf", "Windows MediaFoundation"),
        ("libx264", "Software CPU (libx264)")
    ]

    for enc, desc in encoders_to_test:
        test_cmd = [
            ffmpeg_bin, "-y", "-f", "lavfi",
            "-i", "color=c=black:s=256x256:d=0.2",
            "-c:v", enc,
            "-f", "null", "-"
        ]
        try:
            res = subprocess.run(
                test_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            if res.returncode == 0:
                _CACHED_HARDWARE_ENCODER = enc
                return enc
        except Exception:
            continue

    _CACHED_HARDWARE_ENCODER = "libx264"
    return _CACHED_HARDWARE_ENCODER


def load_settings() -> dict:
    merged = DEFAULT_SETTINGS.copy()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                merged.update(saved)
        except Exception:
            pass
    # Machine-independent portability: sanitize paths if settings moved across PCs
    for path_key in ("output_dir", "bgm_path", "avatar_path"):
        if path_key in merged and merged[path_key]:
            try:
                val = Path(str(merged[path_key]))
                if not val.exists():
                    merged[path_key] = DEFAULT_SETTINGS.get(path_key)
            except Exception:
                merged[path_key] = DEFAULT_SETTINGS.get(path_key)
    return merged


def save_settings(new_settings: dict) -> dict:
    current = load_settings()
    current.update(new_settings)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
    except Exception as e:
        print(f"[Config] Error saving settings: {e}")
    return current


def load_api_keys() -> dict:
    if API_KEYS_FILE.exists():
        try:
            with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                merged = DEFAULT_API_KEYS.copy()
                merged.update(saved)
                return merged
        except Exception:
            pass
    return DEFAULT_API_KEYS.copy()


def save_api_keys(new_keys_data: dict) -> dict:
    current = load_api_keys()
    current.update(new_keys_data)
    try:
        with open(API_KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
    except Exception as e:
        print(f"[Config] Error saving api keys: {e}")
    return current


if not SETTINGS_FILE.exists():
    save_settings(DEFAULT_SETTINGS)

if not API_KEYS_FILE.exists():
    save_api_keys(DEFAULT_API_KEYS)


class Config:
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    BIN_DIR = BIN_DIR
    OUTPUT_DIR = OUTPUT_DIR
    TEMP_DIR = TEMP_DIR
    DOWNLOADS_DIR = DOWNLOADS_DIR
    AVATARS_DIR = AVATARS_DIR
    BGM_DIR = BGM_DIR
    FFMPEG_BIN = find_ffmpeg()
    FFPROBE_BIN = find_ffprobe()
    DETECTED_HARDWARE = detect_hardware_encoder()


config = Config()

