import asyncio
import os
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import DOWNLOADS_DIR
from .turbo_renderer import render_stream_mix
from .downloader import is_url, download_stream


class StreamMixTaskManager:
    """
    Dual-Worker Concurrent Task Queue Engine.
    Handles up to 2 concurrent 1080p GPU rendering tasks simultaneously.
    """
    def __init__(self, max_concurrent: int = 2):
        self.max_concurrent = max_concurrent
        self._semaphore: Optional[asyncio.Semaphore] = None
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.active_processes: Dict[str, Any] = {}

    def _get_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self._semaphore

    def create_task(self, title: str, params: Dict[str, Any], is_preview: bool = False) -> str:
        task_id = str(uuid.uuid4())[:8]
        params["task_id"] = task_id
        params["is_preview"] = is_preview

        yt_online = is_url(params.get("youtube_main_path", ""))
        twitch_online = is_url(params.get("twitch_bg_path", ""))

        self.tasks[task_id] = {
            "id": task_id,
            "title": title,
            "is_preview": is_preview,
            "status": "QUEUED",
            "progress": 0.0,
            "stage": "Waiting in queue...",
            "fps": 0,
            "eta": "--:--",
            "created_at": time.time(),
            "output_path": None,
            "error": None,
            "params": params,
            "downloads": {
                "twitch": {
                    "pct": 100.0 if not twitch_online else 0.0,
                    "speed": "",
                    "is_local": not twitch_online,
                    "status": "Local File (Ready)" if not twitch_online else "Queued"
                },
                "youtube": {
                    "pct": 100.0 if not yt_online else 0.0,
                    "speed": "",
                    "is_local": not yt_online,
                    "status": "Local File (Ready)" if not yt_online else "Queued"
                }
            }
        }
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._worker(task_id))
        except RuntimeError:
            asyncio.create_task(self._worker(task_id))
        return task_id

    async def _worker(self, task_id: str):
        sem = self._get_semaphore()
        async with sem:
            task = self.tasks.get(task_id)
            if not task or task.get("status") == "CANCELLED":
                return

            params = task["params"]
            is_preview = bool(task.get("is_preview", False))
            task["status"] = "ACTIVE"

            try:
                # 1. Resolve source paths & initial offsets
                yt_val = params.get("youtube_main_path", "")
                yt_start = float(params.get("yt_start_sec", 0.0) or 0.0)
                yt_end = params.get("yt_end_sec")
                yt_end = float(yt_end) if yt_end is not None else None

                twitch_val = params.get("twitch_bg_path", "")
                twitch_start = float(params.get("twitch_start_sec", 0.0) or 0.0)

                target_duration = None
                if yt_end is not None and yt_end > yt_start:
                    target_duration = yt_end - yt_start

                # 2. Resolve Target Duration before downloading
                yt_is_online = is_url(yt_val)
                twitch_is_online = is_url(twitch_val)

                if is_preview:
                    target_duration = 30.0
                elif target_duration is None:
                    if yt_is_online:
                        try:
                            from .downloader import fetch_url_info
                            yt_info = await asyncio.to_thread(fetch_url_info, yt_val)
                            dur = float(yt_info.get("duration", 0.0) or 0.0)
                            if dur > 0:
                                target_duration = max(1.0, dur - yt_start)
                        except Exception as e:
                            print(f"[TaskManager] Quick duration probe note: {e}")
                    elif Path(yt_val).exists():
                        try:
                            from .downloader import probe_local_media
                            yt_probe = probe_local_media(yt_val)
                            dur = float(yt_probe.get("duration", 0.0) or 0.0)
                            if dur > 0:
                                target_duration = max(1.0, dur - yt_start)
                        except Exception:
                            pass

                # Progress state tracker for parallel downloads
                prog_state = {"yt_pct": 0, "twitch_pct": 0, "yt_speed": "", "twitch_speed": ""}

                def update_parallel_stage():
                    if yt_is_online and twitch_is_online:
                        task["stage"] = f"Downloading YT: {prog_state['yt_pct']}% | Twitch: {prog_state['twitch_pct']}%"
                        avg_pct = (prog_state["yt_pct"] + prog_state["twitch_pct"]) / 2.0
                        task["progress"] = round(avg_pct * 0.25, 1)
                    elif yt_is_online:
                        sp = f" ({prog_state['yt_speed']})" if prog_state['yt_speed'] else ""
                        task["stage"] = f"Downloading YouTube: {prog_state['yt_pct']}%{sp}"
                        task["progress"] = round(prog_state["yt_pct"] * 0.25, 1)
                    elif twitch_is_online:
                        sp = f" ({prog_state['twitch_speed']})" if prog_state['twitch_speed'] else ""
                        task["stage"] = f"Downloading Twitch BG: {prog_state['twitch_pct']}%{sp}"
                        task["progress"] = round(prog_state["twitch_pct"] * 0.25, 1)

                async def download_yt_task():
                    if not yt_is_online:
                        p = Path(yt_val)
                        if not p.is_absolute() or not p.exists():
                            cand = DOWNLOADS_DIR / p.name
                            if cand.exists():
                                res_path = str(cand.resolve())
                            else:
                                res_path = yt_val
                        else:
                            res_path = yt_val
                        if "downloads" in task:
                            task["downloads"]["youtube"] = {"pct": 100.0, "speed": "", "is_local": True, "status": "✓ Local File (Ready)"}
                        return res_path

                    if "downloads" in task:
                        task["downloads"]["youtube"] = {"pct": 0.0, "speed": "", "is_local": False, "status": "Connecting..."}

                    def dl_yt_prog(pct, speed):
                        prog_state["yt_pct"] = round(pct, 1)
                        prog_state["yt_speed"] = speed
                        if "downloads" in task:
                            sp_str = f" ({speed})" if speed else ""
                            task["downloads"]["youtube"] = {
                                "pct": round(pct, 1),
                                "speed": speed,
                                "is_local": False,
                                "status": f"{round(pct, 1)}%{sp_str}"
                            }
                        update_parallel_stage()

                    res = await asyncio.to_thread(
                        download_stream,
                        url=yt_val,
                        output_prefix="youtube_main",
                        start_seconds=yt_start,
                        duration_seconds=target_duration,
                        progress_callback=dl_yt_prog
                    )
                    if "downloads" in task:
                        task["downloads"]["youtube"] = {"pct": 100.0, "speed": "", "is_local": False, "status": "✓ Ready"}
                    return res

                async def download_twitch_task():
                    if not twitch_is_online:
                        p = Path(twitch_val)
                        if not p.is_absolute() or not p.exists():
                            cand = DOWNLOADS_DIR / p.name
                            if cand.exists():
                                res_path = str(cand.resolve())
                            else:
                                res_path = twitch_val
                        else:
                            res_path = twitch_val
                        if "downloads" in task:
                            task["downloads"]["twitch"] = {"pct": 100.0, "speed": "", "is_local": True, "status": "✓ Local File (Ready)"}
                        return res_path

                    if "downloads" in task:
                        task["downloads"]["twitch"] = {"pct": 0.0, "speed": "", "is_local": False, "status": "Connecting..."}

                    is_yt_bg = "youtube.com" in twitch_val.lower() or "youtu.be" in twitch_val.lower()
                    prefix = "bg_gameplay" if is_yt_bg else "twitch_bg"

                    def dl_twitch_prog(pct, speed):
                        prog_state["twitch_pct"] = round(pct, 1)
                        prog_state["twitch_speed"] = speed
                        if "downloads" in task:
                            sp_str = f" ({speed})" if speed else ""
                            task["downloads"]["twitch"] = {
                                "pct": round(pct, 1),
                                "speed": speed,
                                "is_local": False,
                                "status": f"{round(pct, 1)}%{sp_str}"
                            }
                        update_parallel_stage()

                    twitch_cut_sec = float(params.get("twitch_cut_sec", 0.0) or 0.0)
                    dl_dur = twitch_cut_sec if twitch_cut_sec > 0 else ((target_duration + 5.0) if target_duration else None)

                    res = await asyncio.to_thread(
                        download_stream,
                        url=twitch_val,
                        output_prefix=prefix,
                        start_seconds=twitch_start,
                        duration_seconds=dl_dur,
                        progress_callback=dl_twitch_prog
                    )
                    if "downloads" in task:
                        task["downloads"]["twitch"] = {"pct": 100.0, "speed": "", "is_local": False, "status": "✓ Ready"}
                    return res

                # Execute both streams simultaneously in parallel!
                if yt_is_online or twitch_is_online:
                    task["stage"] = "Connecting & Initializing High-Speed Slicers..."
                    task["progress"] = 2.0
                    yt_local, twitch_local = await asyncio.gather(download_yt_task(), download_twitch_task())
                    params["youtube_main_path"] = yt_local
                    params["twitch_bg_path"] = twitch_local
                    if target_duration:
                        if yt_is_online:
                            params["yt_start_sec"] = 0.0
                            params["yt_end_sec"] = target_duration
                        if twitch_is_online:
                            params["twitch_start_sec"] = 0.0
                else:
                    if "downloads" in task:
                        task["downloads"]["twitch"] = {"pct": 100.0, "speed": "", "is_local": True, "status": "✓ Local File (Ready)"}
                        task["downloads"]["youtube"] = {"pct": 100.0, "speed": "", "is_local": True, "status": "✓ Local File (Ready)"}

                # 3. Dynamic Subtitles Generation (Groq Whisper + 18 Typography Presets)
                is_captions_enabled = bool(params.get("enable_captions", True))
                if is_captions_enabled and not params.get("ass_subtitles_path"):
                    try:
                        task["stage"] = "🎙️ Extracting speech audio for Groq Whisper..."
                        task["progress"] = 15.0
                        from .subtitle_generator import transcribe_audio_words, create_ass_subtitles
                        from .config import find_ffmpeg, TEMP_DIR
                        from .downloader import probe_local_media
                        import subprocess

                        yt_src = params["youtube_main_path"]
                        # Resolve video duration if target_duration wasn't determined
                        if not target_duration or target_duration <= 0:
                            try:
                                yt_probe = probe_local_media(yt_src)
                                dur = float(yt_probe.get("duration", 0.0) or 0.0)
                                if dur > 0:
                                    target_duration = max(1.0, dur - float(params.get("yt_start_sec", 0.0) or 0.0))
                            except Exception:
                                pass

                        temp_audio = str((TEMP_DIR / f"speech_{task_id}.mp3").resolve())
                        yt_start_offset = float(params.get("yt_start_sec", 0.0) or 0.0)

                        # KEY FIX: For 30s preview, turbo_renderer.py seeks to the MIDDLE
                        # of the video (slice_offset = duration/2 - 15). We MUST extract audio
                        # from the exact same position, otherwise captions will transcribe the
                        # beginning while the video plays the middle — causing total mismatch!
                        if is_preview:
                            extract_dur = 30.0
                            if target_duration and target_duration > 30.0:
                                slice_offset = max(0.0, (target_duration / 2.0) - 15.0)
                                yt_start_offset = yt_start_offset + slice_offset
                        else:
                            extract_dur = target_duration or 60.0

                        extract_cmd = [find_ffmpeg(), "-y"]
                        if yt_start_offset > 0.05:
                            extract_cmd.extend(["-ss", f"{yt_start_offset:.2f}"])
                        extract_cmd.extend([
                            "-i", yt_src,
                            "-t", str(extract_dur),
                            "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k",
                            temp_audio
                        ])
                        await asyncio.to_thread(
                            subprocess.run, extract_cmd,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                        )
                        if os.path.exists(temp_audio):
                            task["stage"] = "🤖 Groq Whisper: Generating Word-Level AI Subtitles..."
                            task["progress"] = 22.0
                            caption_lang = params.get("caption_language") or None
                            words = await asyncio.to_thread(
                                transcribe_audio_words, temp_audio, extract_dur, caption_lang
                            )
                            if not words:
                                from .subtitle_generator import generate_fallback_speech_words
                                words = generate_fallback_speech_words(extract_dur)
                            if words:
                                ass_file = create_ass_subtitles(
                                    words=words,
                                    preset_key=params.get("caption_preset", "capcut_yellow"),
                                    caption_size=params.get("caption_size", "large"),
                                    font_family=params.get("caption_font_family"),
                                    custom_y=params.get("caption_y"),
                                    custom_x=params.get("caption_x"),
                                    custom_w=params.get("caption_w"),
                                    custom_h=params.get("caption_h")
                                )
                                params["ass_subtitles_path"] = ass_file
                        task["progress"] = 30.0
                    except Exception as sub_err:
                        print(f"[TaskManager] Subtitle generation note: {sub_err}")
                elif not is_captions_enabled:
                    print(f"[TaskManager] Captions disabled by user — skipping Whisper transcription.")

                # 4. GPU Single-Pass Compositing
                base_pct = 30.0 if is_captions_enabled else 10.0
                comp_weight = (100.0 - base_pct) / 100.0
                task["stage"] = "🚀 GPU Single-Pass Compositing & Rendering..."
                task["progress"] = base_pct

                def update_progress(pct: float, fps: int, eta: str):
                    if task_id in self.tasks and self.tasks[task_id]["status"] != "CANCELLED":
                        overall = base_pct + (pct * comp_weight)
                        self.tasks[task_id]["progress"] = round(overall, 1)
                        self.tasks[task_id]["fps"] = fps
                        self.tasks[task_id]["eta"] = eta
                        eta_label = f" (ETA: {eta})" if eta and eta != "--:--" else ""
                        self.tasks[task_id]["stage"] = f"Compositing 1080p @ {fps} FPS{eta_label}"

                def on_process_launch(proc):
                    self.active_processes[task_id] = proc

                try:
                    output_file = await asyncio.to_thread(
                        render_stream_mix,
                        params=params,
                        progress_callback=update_progress,
                        process_callback=on_process_launch
                    )
                finally:
                    self.active_processes.pop(task_id, None)

                task["status"] = "COMPLETED"
                task["progress"] = 100.0
                task["stage"] = "✅ Render Complete!"
                task["output_path"] = output_file
                if "downloads" in task:
                    task["downloads"]["twitch"]["pct"] = 100.0
                    task["downloads"]["twitch"]["status"] = "✓ Ready"
                    task["downloads"]["youtube"]["pct"] = 100.0
                    task["downloads"]["youtube"]["status"] = "✓ Ready"

            except Exception as e:
                from .config import log_error
                log_error("task_manager", f"Task #{task_id} failed during execution: {e}", exc=e, task_id=task_id)
                task["status"] = "FAILED"
                task["error"] = str(e)
                task["stage"] = f"Error: {str(e)[:70]}"

    def cancel_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if task and task["status"] in ("QUEUED", "ACTIVE"):
            task["status"] = "CANCELLED"
            task["stage"] = "Task Cancelled by User"
            proc = self.active_processes.get(task_id)
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
                self.active_processes.pop(task_id, None)
            return True
        return False

    def clear_finished_tasks(self) -> int:
        """Removes all finished (completed, cancelled, failed) tasks, keeping active and queued."""
        to_delete = [
            tid for tid, t in self.tasks.items()
            if t.get("status") in ("COMPLETED", "DONE", "CANCELLED", "FAILED")
        ]
        for tid in to_delete:
            del self.tasks[tid]
        return len(to_delete)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        return list(self.tasks.values())


task_manager = StreamMixTaskManager(max_concurrent=2)
