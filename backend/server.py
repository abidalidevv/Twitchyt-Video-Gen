import os
import sys
import shutil
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Suppress benign Windows asyncio ConnectionResetError [WinError 10054]
if sys.platform == "win32":
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

        def _silent_call_connection_lost(self, exc=None):
            try:
                _orig_call_connection_lost(self, exc)
            except (ConnectionResetError, OSError):
                pass

        _ProactorBasePipeTransport._call_connection_lost = _silent_call_connection_lost
    except Exception:
        pass

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict

from .config import (
    BASE_DIR,
    DATA_DIR,
    OUTPUT_DIR,
    TEMP_DIR,
    DOWNLOADS_DIR,
    AVATARS_DIR,
    BGM_DIR,
    FRONTEND_DIR,
    find_ffmpeg,
    find_ffprobe,
    detect_hardware_encoder,
    load_settings,
    save_settings,
    get_recent_logs,
    clear_logs,
    log_error,
    ERROR_LOG_FILE,
    LOGS_DIR
)
from .api_pool import groq_pool
from .groq_metadata import generate_youtube_metadata
from .downloader import is_url, probe_local_media, fetch_url_info
from .task_manager import task_manager

app = FastAPI(title="StreamMix Studio API", version="2.2.0")

# Enable CORS for desktop/browser integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    error_msgs = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []) if l != "body")
        msg = err.get("msg", "invalid")
        error_msgs.append(f"[{loc}]: {msg}")
    full_str = " | ".join(error_msgs)
    log_error("validation", f"Request validation failed on {request.url.path}: {full_str}")
    return JSONResponse(
        status_code=422,
        content={"detail": full_str, "errors": exc.errors()}
    )

# Static file mounts
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend_static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")
app.mount("/temp", StaticFiles(directory=str(TEMP_DIR)), name="temp")
app.mount("/avatars", StaticFiles(directory=str(AVATARS_DIR)), name="avatars")
app.mount("/bgm", StaticFiles(directory=str(BGM_DIR)), name="bgm")
app.mount("/downloads", StaticFiles(directory=str(DOWNLOADS_DIR)), name="downloads")


@app.get("/")
async def root():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "StreamMix Studio backend is running."}


@app.get("/docs-guide")
async def docs_guide():
    docs_path = FRONTEND_DIR / "docs.html"
    if docs_path.exists():
        return FileResponse(str(docs_path))
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/api/health")
async def api_health():
    settings = load_settings()
    detected_gpu = detect_hardware_encoder()
    all_tasks = task_manager.get_all_tasks()
    active_count = len([t for t in all_tasks if t["status"] in ("ACTIVE", "QUEUED")])
    return {
        "status": "online",
        "ffmpeg": find_ffmpeg(),
        "ffprobe": find_ffprobe(),
        "detected_encoder": detected_gpu,
        "configured_encoder": settings.get("hardware_encoder", "auto"),
        "active_tasks": active_count,
        "total_outputs": len(list(OUTPUT_DIR.glob("*.mp4")))
    }


# --- SETTINGS & HARDWARE ---
@app.get("/api/settings")
async def get_settings():
    return load_settings()


class SettingsUpdate(BaseModel):
    hardware_encoder: Optional[str] = None
    bitrate_mode: Optional[str] = None
    default_bg_blur: Optional[int] = None
    default_yt_opacity: Optional[int] = None
    default_audio_speed: Optional[float] = None
    default_pitch_semitones: Optional[float] = None
    default_bgm_volume: Optional[float] = None
    copyright_shield: Optional[bool] = None
    auto_open_folder: Optional[bool] = None


@app.post("/api/settings")
async def update_settings(req: SettingsUpdate):
    saved = save_settings(req.model_dump(exclude_none=True))
    return {"success": True, "settings": saved}


# --- GROQ API POOL MANAGER ---
@app.get("/api/keys")
async def get_api_keys():
    return groq_pool.get_all_keys()


class AddKeyRequest(BaseModel):
    key: str
    label: Optional[str] = None


@app.post("/api/keys")
async def add_api_key(req: AddKeyRequest):
    if not req.key.strip():
        raise HTTPException(status_code=400, detail="Key cannot be empty.")
    entry = groq_pool.add_key(req.key.strip(), req.label)
    return {"success": True, "key": entry}


@app.delete("/api/keys/{key_id}")
async def delete_api_key(key_id: str):
    groq_pool.remove_key(key_id)
    return {"success": True}


class TestKeyRequest(BaseModel):
    key: str


@app.post("/api/keys/test")
async def test_key_latency(req: TestKeyRequest):
    valid, latency, msg = groq_pool.test_key(req.key.strip())
    return {"valid": valid, "latency_ms": latency, "message": msg}


@app.get("/api/keys/status")
async def api_get_keys_status():
    """Checks the health of Groq API keys and returns real-time verification status."""
    groq_pool.load_keys()
    keys = groq_pool.keys
    if not keys:
        return {
            "has_working_key": False,
            "total_keys": 0,
            "healthy_count": 0,
            "invalid_count": 0,
            "message": "No Groq API keys found. Please add an API key in the API Keys Pool tab."
        }

    tested_keys = []
    healthy_count = 0
    invalid_count = 0

    for k in keys:
        api_key = k.get("key", "").strip()
        if not api_key:
            k["status"] = "INVALID"
            k["last_error"] = "Empty key string"
            invalid_count += 1
        else:
            valid, latency, msg = await asyncio.to_thread(groq_pool.test_key, api_key)
            k["status"] = "HEALTHY" if valid else "INVALID"
            k["latency_ms"] = latency if valid else 0
            k["last_error"] = None if valid else msg
            if valid:
                healthy_count += 1
            else:
                invalid_count += 1

        masked = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 12 else "gsk_***"
        tested_keys.append({
            "id": k.get("id"),
            "label": k.get("label"),
            "masked_key": masked,
            "status": k.get("status"),
            "latency_ms": k.get("latency_ms", 0),
            "error": k.get("last_error")
        })

    groq_pool.save_keys()

    return {
        "has_working_key": healthy_count > 0,
        "total_keys": len(keys),
        "healthy_count": healthy_count,
        "invalid_count": invalid_count,
        "keys": tested_keys,
        "message": f"Groq API is verified and working ({healthy_count} healthy key{'s' if healthy_count > 1 else ''})." if healthy_count > 0 else "Your Groq API key is expired or invalid (401/429). Please replace it."
    }



# --- MEDIA PROBING & UPLOADS ---
class ProbeRequest(BaseModel):
    source: Optional[str] = None
    path_or_url: Optional[str] = None


@app.post("/api/probe")
@app.post("/api/probe-media")
async def api_probe_media(req: ProbeRequest):
    val = (req.path_or_url or req.source or "").strip()
    if not val:
        raise HTTPException(status_code=400, detail="Missing URL or file path.")
    if is_url(val):
        try:
            info = await asyncio.to_thread(fetch_url_info, val)
            return {"success": True, **info}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to inspect online URL: {e}")
    else:
        try:
            info = await asyncio.to_thread(probe_local_media, val)
            return {"success": True, **info}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to inspect local file: {e}")



@app.post("/api/upload/avatar")
async def upload_avatar(file: UploadFile = File(...)):
    safe_name = f"avatar_{uuid.uuid4().hex[:8]}_{Path(file.filename).name}"
    dest = AVATARS_DIR / safe_name
    def _save():
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
    await asyncio.to_thread(_save)
    return {
        "success": True,
        "filename": file.filename,
        "path": str(dest.resolve()),
        "url": f"/avatars/{safe_name}"
    }


@app.post("/api/upload/bgm")
async def upload_bgm(file: UploadFile = File(...)):
    safe_name = f"bgm_{uuid.uuid4().hex[:8]}_{Path(file.filename).name}"
    dest = BGM_DIR / safe_name
    def _save():
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
    await asyncio.to_thread(_save)
    return {
        "success": True,
        "filename": file.filename,
        "path": str(dest.resolve()),
        "url": f"/bgm/{safe_name}"
    }


@app.post("/api/upload/video")
async def upload_local_video(file: UploadFile = File(...)):
    safe_name = f"local_{uuid.uuid4().hex[:8]}_{Path(file.filename).name}"
    dest = DOWNLOADS_DIR / safe_name
    def _save_and_probe():
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return probe_local_media(str(dest))
    try:
        info = await asyncio.to_thread(_save_and_probe)
        return {
            "success": True,
            "filename": file.filename,
            "path": str(dest.resolve()),
            "duration": info["duration"],
            "url": f"/downloads/{safe_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process video upload: {e}")


# --- METADATA & CHAPTER GENERATOR ---
class MetadataRequest(BaseModel):
    text_or_topic: str


@app.post("/api/metadata/generate")
async def api_generate_metadata(req: MetadataRequest):
    try:
        data = generate_youtube_metadata(req.text_or_topic)
        return {"success": True, **data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Groq Llama-3 generation error: {e}")


# --- RENDERING & TASKS ---
class RenderTaskRequest(BaseModel):
    title: Optional[str] = "StreamMix Project"
    twitch_bg_path: str
    youtube_main_path: str
    twitch_start_sec: Optional[float] = 0.0
    yt_start_sec: Optional[float] = 0.0
    yt_end_sec: Optional[float] = None
    bg_blur: Optional[Union[float, int]] = 18.0
    yt_blur: Optional[Union[float, int]] = 18.0
    yt_opacity: Optional[Union[float, int]] = 35
    audio_speed: Optional[float] = 1.0
    pitch_semitones: Optional[float] = 0.0
    copyright_shield: Optional[bool] = True
    enable_avatar: Optional[bool] = True
    avatar_path: Optional[str] = None
    avatar_anchor: Optional[str] = "right"
    avatar_bounce: Optional[bool] = True
    avatar_sway: Optional[bool] = True
    avatar_sway_speed: Optional[float] = 0.35
    avatar_opacity: Optional[float] = 1.0
    avatar_size: Optional[Union[float, int]] = 420
    avatar_flip: Optional[bool] = False
    avatar_glow: Optional[str] = "cyan"
    avatar_x: Optional[Union[float, int]] = None
    avatar_y: Optional[Union[float, int]] = None
    avatar_crop_left: Optional[Union[float, int]] = 0.0
    avatar_crop_right: Optional[Union[float, int]] = 0.0
    avatar_crop_top: Optional[Union[float, int]] = 0.0
    avatar_crop_bottom: Optional[Union[float, int]] = 0.0
    enable_captions: Optional[bool] = True
    caption_preset: Optional[str] = "capcut_yellow"
    caption_font_family: Optional[str] = "default"
    caption_size: Optional[str] = "large"
    enable_caption_bg: Optional[bool] = False
    caption_bg_color: Optional[str] = "#000000"
    caption_bg_opacity: Optional[Union[float, int]] = 75
    caption_x: Optional[Union[float, int]] = None
    caption_y: Optional[Union[float, int]] = None
    caption_w: Optional[Union[float, int]] = None
    caption_h: Optional[Union[float, int]] = None
    bitrate_mode: Optional[str] = "6500k"
    bgm_path: Optional[str] = None
    bgm_volume: Optional[float] = 0.07
    ass_subtitles_path: Optional[str] = None

    model_config = ConfigDict(extra="allow")



@app.post("/api/render")
async def api_render_full(req: RenderTaskRequest):
    try:
        task_id = task_manager.create_task(
            title=req.title or "StreamMix 1080p Video",
            params=req.model_dump(),
            is_preview=False
        )
        return {"success": True, "task_id": task_id, "status": "QUEUED"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/preview")
@app.post("/api/render-preview")
async def api_render_30s_preview(req: RenderTaskRequest):
    try:
        task_id = task_manager.create_task(
            title=f"⚡ 30s Quick Slice ({req.title or 'Preview'})",
            params=req.model_dump(),
            is_preview=True
        )
        return {"success": True, "task_id": task_id, "status": "QUEUED"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/tasks")
async def api_get_tasks():
    return task_manager.get_all_tasks()


@app.get("/api/tasks/{task_id}")
async def api_get_task(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    resp = dict(task)
    if task.get("output_path") and Path(task["output_path"]).exists():
        resp["video_url"] = f"/outputs/{Path(task['output_path']).name}"
    return resp


@app.post("/api/tasks/{task_id}/cancel")
async def api_cancel_task(task_id: str):
    cancelled = task_manager.cancel_task(task_id)
    return {"success": cancelled}


@app.post("/api/tasks/clear-completed")
async def api_clear_completed_tasks():
    cleared = task_manager.clear_finished_tasks()
    return {"success": True, "cleared_count": cleared}


@app.post("/api/tasks/open-folder")
async def api_open_outputs_folder():
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(OUTPUT_DIR.resolve()))
            return {"success": True}
        else:
            subprocess.Popen(["xdg-open", str(OUTPUT_DIR.resolve())])
            return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open folder: {e}")



# --- OUTPUTS MANAGEMENT ---
@app.get("/api/outputs")
async def api_list_outputs():
    items = []
    for p in sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True):
        items.append({
            "name": p.name,
            "path": str(p.resolve()),
            "url": f"/outputs/{p.name}",
            "size_mb": round(p.stat().st_size / (1024 * 1024), 2),
            "mtime": p.stat().st_mtime
        })
    return items


@app.delete("/api/outputs/{filename}")
async def api_delete_output(filename: str):
    target = OUTPUT_DIR / filename
    if target.exists() and target.is_file():
        target.unlink()
        return {"success": True, "deleted": filename}
    raise HTTPException(status_code=404, detail="Output file not found")


class OpenOutputRequest(BaseModel):
    path: Optional[str] = None


@app.post("/api/open-output")
async def api_open_output(req: OpenOutputRequest):
    target = req.path or str(OUTPUT_DIR)
    if os.name == "nt":
        try:
            if hasattr(os, "startfile"):
                if os.path.isfile(target):
                    os.startfile(str(Path(target).parent))
                else:
                    os.startfile(target)
            else:
                os.system(f'explorer "{target}"')
        except Exception as e:
            print(f"[OpenOutput] Error: {e}")
    return {"success": True}


# --- STORAGE & CACHE MANAGEMENT ---
def _format_size(num_bytes: int) -> str:
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    elif num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


def _calc_dir_stats(dir_path: Path):
    if not dir_path.exists():
        return 0, 0
    total_bytes = 0
    count = 0
    for p in dir_path.rglob("*"):
        if p.is_file():
            try:
                total_bytes += p.stat().st_size
                count += 1
            except Exception:
                pass
    return total_bytes, count


@app.get("/api/storage/stats")
async def api_storage_stats():
    """Calculates disk burden of temp files, download cache, and output renders."""
    temp_bytes, temp_count = _calc_dir_stats(TEMP_DIR)
    dl_bytes, dl_count = _calc_dir_stats(DOWNLOADS_DIR)
    out_bytes, out_count = _calc_dir_stats(OUTPUT_DIR)
    logs_bytes, logs_count = _calc_dir_stats(LOGS_DIR)

    cache_bytes = temp_bytes + dl_bytes
    total_bytes = cache_bytes + out_bytes + logs_bytes

    return {
        "success": True,
        "temp": {
            "bytes": temp_bytes,
            "mb": round(temp_bytes / (1024 * 1024), 2),
            "formatted": _format_size(temp_bytes),
            "files": temp_count
        },
        "downloads": {
            "bytes": dl_bytes,
            "mb": round(dl_bytes / (1024 * 1024), 2),
            "formatted": _format_size(dl_bytes),
            "files": dl_count
        },
        "outputs": {
            "bytes": out_bytes,
            "mb": round(out_bytes / (1024 * 1024), 2),
            "formatted": _format_size(out_bytes),
            "files": out_count
        },
        "cache_reclaimable": {
            "bytes": cache_bytes,
            "mb": round(cache_bytes / (1024 * 1024), 2),
            "formatted": _format_size(cache_bytes)
        },
        "total_burden": {
            "bytes": total_bytes,
            "mb": round(total_bytes / (1024 * 1024), 2),
            "formatted": _format_size(total_bytes)
        }
    }


class CleanStorageRequest(BaseModel):
    clean_temp: bool = True
    clean_downloads: bool = True
    clean_outputs: bool = False
    clean_logs: bool = False


@app.post("/api/storage/clean")
async def api_storage_clean(req: CleanStorageRequest):
    """Safely cleans selected cache folders while keeping finished output videos safe by default."""
    freed_bytes = 0
    deleted_files = 0
    errors = []

    def _purge_dir(dir_path: Path):
        nonlocal freed_bytes, deleted_files
        if not dir_path.exists():
            return
        for p in list(dir_path.rglob("*")):
            if p.is_file():
                try:
                    sz = p.stat().st_size
                    p.unlink()
                    freed_bytes += sz
                    deleted_files += 1
                except Exception as e:
                    errors.append(f"{p.name}: {e}")

    if req.clean_temp:
        await asyncio.to_thread(_purge_dir, TEMP_DIR)

    if req.clean_downloads:
        await asyncio.to_thread(_purge_dir, DOWNLOADS_DIR)

    # OUTPUTS ARE PROTECTED — Only clean if explicitly checked by user
    if req.clean_outputs:
        await asyncio.to_thread(_purge_dir, OUTPUT_DIR)

    if req.clean_logs:
        await asyncio.to_thread(_purge_dir, LOGS_DIR)

    return {
        "success": True,
        "freed_bytes": freed_bytes,
        "freed_mb": round(freed_bytes / (1024 * 1024), 2),
        "freed_formatted": _format_size(freed_bytes),
        "deleted_count": deleted_files,
        "errors": errors
    }


# --- ERROR LOGS API ---
@app.get("/api/logs")
async def api_get_logs():
    return {
        "success": True,
        "logs": get_recent_logs(max_lines=300),
        "log_path": str(ERROR_LOG_FILE.resolve())
    }


@app.delete("/api/logs")
async def api_clear_logs():
    cleared = clear_logs()
    return {"success": cleared, "message": "Error log cleared."}


