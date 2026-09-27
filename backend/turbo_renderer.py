import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Callable, Optional

from .config import (
    find_ffmpeg,
    detect_hardware_encoder,
    OUTPUT_DIR,
    TEMP_DIR,
    FONTS_DIR,
    load_settings,
    log_error
)
from .audio_engine import build_audio_filter_chain, build_video_shield_filter
from .downloader import probe_local_media


def escape_ffmpeg_path(path_str: str) -> str:
    """Escapes file paths for FFmpeg filter arguments on Windows."""
    p = path_str.replace("\\", "/")
    p = p.replace(":", "\\:")
    p = p.replace("'", "'\\''")
    return p


def create_caption_bg_image(w: int, h: int, hex_color: str, opacity: float, task_id: str, radius: int = 16) -> str:
    """Generates an anti-aliased RGBA PNG with rounded corners matching stage preview."""
    try:
        from PIL import Image, ImageDraw
        hex_clean = hex_color.replace("#", "")
        r = int(hex_clean[0:2], 16) if len(hex_clean) >= 2 else 0
        g = int(hex_clean[2:4], 16) if len(hex_clean) >= 4 else 0
        b = int(hex_clean[4:6], 16) if len(hex_clean) >= 6 else 0
        alpha = max(10, min(255, int(opacity * 255)))

        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            [0, 0, w - 1, h - 1],
            radius=radius,
            fill=(r, g, b, alpha),
            outline=(255, 255, 255, 38),
            width=1
        )
        out_file = TEMP_DIR / f"cap_bg_{task_id}.png"
        img.save(out_file, "PNG")
        return str(out_file.resolve())
    except Exception as e:
        print(f"[Renderer] Error creating caption bg image: {e}")
        return ""


def apply_avatar_outer_glow(avatar_path: str, glow_type: str, task_id: str) -> str:
    """Renders soft outer glow border onto avatar matching CSS preview drop-shadow."""
    if not glow_type or glow_type.lower() == "none" or not Path(avatar_path).exists():
        return avatar_path

    from PIL import Image, ImageFilter
    glow_colors = {
        "cyan":  (0, 242, 254),
        "white": (255, 255, 255),
        "gold":  (251, 191, 36),
    }
    glow_rgb = glow_colors.get(glow_type.lower())
    if not glow_rgb:
        return avatar_path

    try:
        av = Image.open(avatar_path).convert("RGBA")
        pad = 28
        w, h = av.size
        glow_canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))

        alpha = av.split()[3]
        blurred_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=12))

        glow_layer = Image.new("RGBA", (w, h), (*glow_rgb, 200))
        glow_canvas.paste(glow_layer, (pad, pad), blurred_alpha)
        glow_canvas.paste(av, (pad, pad), av)

        out_path = TEMP_DIR / f"avatar_glow_{task_id}.png"
        glow_canvas.save(out_path, "PNG")
        return str(out_path.resolve())
    except Exception as e:
        print(f"[Renderer] Avatar glow note: {e}")
        return avatar_path


def render_stream_mix(
    params: Dict[str, Any],
    progress_callback: Optional[Callable[[float, int, str], None]] = None
) -> str:
    """
    Executes master single-pass FFmpeg streaming pipeline:
    - Layer 1: Twitch Gameplay Background (Muted, Gaussian Blur, Looped, In-Trim)
    - Layer 2: YouTube Main Video (50% Opacity, Duration Driver, Pitch Shift, Copyright Shield)
    - Layer 3: Host Avatar Cutout (Ping-Pong Harmonic Float + Audio-Reactive Bounce + Outer Glow)
    - Layer 4a: Optional Caption Background Box (Custom rounded box backdrop)
    - Layer 4b: Optional Captions (Burned ASS with neon glow and custom font family)
    - Layer 5: Ambient BGM (Duck-mixed @ 7% volume)
    """
    settings = load_settings()
    ffmpeg_bin = find_ffmpeg()

    # 1. Inputs
    twitch_path = params.get("twitch_bg_path")
    youtube_path = params.get("youtube_main_path")
    avatar_path = params.get("avatar_path")
    bgm_path = params.get("bgm_path")

    if not youtube_path or not Path(youtube_path).exists():
        raise FileNotFoundError(f"YouTube Main video not found: {youtube_path}")

    # Probe YouTube video for master duration
    yt_info = probe_local_media(youtube_path)
    raw_duration = yt_info["duration"] or 3600.0

    # In / Out Trimming
    yt_start = float(params.get("yt_start_sec") or 0.0)
    yt_end = float(params.get("yt_end_sec") or raw_duration)
    if yt_end <= yt_start:
        yt_end = raw_duration
    master_duration = max(1.0, yt_end - yt_start)

    twitch_start = float(params.get("twitch_start_sec") or 0.0)

    # Quick 30s slice mode
    is_30s_preview = bool(params.get("is_preview", False))
    if is_30s_preview:
        render_duration = min(30.0, master_duration)
        slice_offset = max(0.0, (master_duration / 2.0) - 15.0)
        yt_start = yt_start + slice_offset
    else:
        render_duration = master_duration

    # Output file
    task_id = str(params.get("task_id", int(time.time())))[:8]
    output_filename = f"StreamMix_{task_id}.mp4" if not is_30s_preview else f"QuickTest_{task_id}.mp4"
    output_path = OUTPUT_DIR / output_filename

    # Encoder & Hardware Tuning
    pref_enc = settings.get("hardware_encoder", "auto")
    encoder = detect_hardware_encoder() if pref_enc == "auto" else pref_enc
    bitrate = params.get("bitrate_mode") or settings.get("bitrate_mode", "6500k")

    # Visual Parameters
    bg_blur = max(0, min(40, int(params.get("bg_blur", 0) or 0)))
    yt_blur = max(0, min(40, int(params.get("yt_blur", 0) or 0)))
    yt_opacity = max(10, min(100, int(params.get("yt_opacity", 75) or 75))) / 100.0
    copyright_shield = bool(params.get("copyright_shield", True))
    speed = float(params.get("audio_speed", 1.0))
    pitch = float(params.get("pitch_semitones", 0.0))
    avatar_anchor = str(params.get("avatar_anchor", "right")).lower()
    avatar_bounce = bool(params.get("avatar_bounce", True))
    avatar_sway = bool(params.get("avatar_sway", True))
    avatar_sway_speed = float(params.get("avatar_sway_speed", 0.35))
    avatar_opacity = max(0.1, min(1.0, float(params.get("avatar_opacity", 1.0))))
    avatar_size = int(params.get("avatar_size", 420))
    avatar_flip = bool(params.get("avatar_flip", False))
    avatar_glow = str(params.get("avatar_glow", "cyan"))
    avatar_x_custom = params.get("avatar_x")
    avatar_y_custom = params.get("avatar_y")
    enable_avatar = bool(params.get("enable_avatar", True)) and bool(avatar_path and Path(avatar_path).exists())
    bgm_volume = float(params.get("bgm_volume", 0.07))

    # Caption Background Box parameters
    enable_caption_bg = bool(params.get("enable_caption_bg", False))
    caption_bg_path = None
    cap_box_x = 384
    cap_box_y = 778
    if enable_caption_bg:
        custom_w = params.get("caption_w")
        custom_h = params.get("caption_h")
        custom_x = params.get("caption_x")
        custom_y = params.get("caption_y")

        bw = int(float(custom_w)) if custom_w is not None else 1152
        bh = int(float(custom_h)) if custom_h is not None else 172
        bw = max(200, min(1920, bw))
        bh = max(60, min(1080, bh))

        if custom_x is not None and custom_y is not None:
            cap_box_x = int(float(custom_x))
            cap_box_y = int(float(custom_y))
        elif custom_y is not None:
            cap_box_x = (1920 - bw) // 2
            cap_box_y = int(float(custom_y))
        else:
            cap_box_x = (1920 - bw) // 2
            cap_box_y = 650

        cap_box_x = max(0, min(1920 - bw, cap_box_x))
        cap_box_y = max(0, min(1080 - bh, cap_box_y))

        bg_col = str(params.get("caption_bg_color", "#000000"))
        bg_op = float(params.get("caption_bg_opacity", 75)) / 100.0
        caption_bg_path = create_caption_bg_image(bw, bh, bg_col, bg_op, task_id=task_id, radius=14)

    # --- BUILD FFmpeg COMMAND ---
    cmd = [ffmpeg_bin, "-y", "-hide_banner", "-threads", "0"]

    # Input 0: Twitch Background (stream looped, muted, start-trimmed)
    if twitch_start > 0.05:
        cmd.extend(["-ss", f"{twitch_start:.2f}"])
    cmd.extend(["-stream_loop", "-1", "-i", twitch_path])

    # Input 1: YouTube Main (duration driver, in-trimmed)
    if yt_start > 0.05:
        cmd.extend(["-ss", f"{yt_start:.2f}"])
    cmd.extend(["-t", f"{render_duration:.2f}", "-i", youtube_path])

    # Dynamic Inputs Index Tracker
    next_input_idx = 2

    # Input (Avatar with Outer Glow)
    has_avatar = enable_avatar
    avatar_input_idx = None
    if has_avatar:
        processed_avatar = apply_avatar_outer_glow(avatar_path, avatar_glow, task_id)
        avatar_input_idx = next_input_idx
        cmd.extend(["-loop", "1", "-i", processed_avatar])
        next_input_idx += 1

    # Input (Caption Background Box Image)
    has_cap_bg = bool(caption_bg_path and Path(caption_bg_path).exists())
    cap_bg_input_idx = None
    if has_cap_bg:
        cap_bg_input_idx = next_input_idx
        cmd.extend(["-loop", "1", "-i", caption_bg_path])
        next_input_idx += 1

    # Input (Ambient BGM)
    has_bgm = bool(bgm_path and Path(bgm_path).exists())
    bgm_input_idx = None
    if has_bgm:
        bgm_input_idx = next_input_idx
        cmd.extend(["-stream_loop", "-1", "-i", bgm_path])
        next_input_idx += 1

    # --- FILTER_COMPLEX GRAPH ---
    filter_chains = []

    # 1. Layer 1: Twitch BG (1080p crop + optional Gaussian Blur)
    bg_blur_filter = f",gblur=sigma={bg_blur}" if bg_blur > 0 else ""
    filter_chains.append(
        f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080{bg_blur_filter}[bg_clean]"
    )

    # 2. Layer 2: YouTube Main Video (Gaussian Blur, Opacity, Speed setpts, optional micro-crop shield)
    yt_blur_filter = f"gblur=sigma={yt_blur}," if yt_blur > 0 else ""
    shield_filter = "crop=in_w-4:in_h-4,vignette=PI/5," if copyright_shield else ""
    pts_expr = f"setpts=PTS/{speed:.3f}," if abs(speed - 1.0) > 0.02 else ""
    filter_chains.append(
        f"[1:v]{shield_filter}scale=1920:1080,{pts_expr}{yt_blur_filter}format=yuva420p,colorchannelmixer=aa={yt_opacity:.2f}[yt_main]"
    )

    # Overlay YouTube onto Twitch BG
    filter_chains.append("[bg_clean][yt_main]overlay=0:0[layer_base]")
    current_v = "[layer_base]"

    # 3. Layer 3: Host Avatar (Custom Drag Position or Anchor, Edge Crop, Slow-Motion Sway & Bounce)
    if has_avatar and avatar_input_idx is not None:
        crop_l = max(0, min(50, float(params.get("avatar_crop_left", 0.0) or 0.0)))
        crop_r = max(0, min(50, float(params.get("avatar_crop_right", 0.0) or 0.0)))
        crop_t = max(0, min(50, float(params.get("avatar_crop_top", 0.0) or 0.0)))
        crop_b = max(0, min(50, float(params.get("avatar_crop_bottom", 0.0) or 0.0)))

        crop_mod = ""
        if crop_l > 0 or crop_r > 0 or crop_t > 0 or crop_b > 0:
            crop_mod = f"crop=w='in_w*(1-({crop_l}+{crop_r})/100)':h='in_h*(1-({crop_t}+{crop_b})/100)':x='in_w*{crop_l}/100':y='in_h*{crop_t}/100',"

        flip_mod = "hflip," if avatar_flip else ""
        scale_mod = f"scale={avatar_size}:-2"
        filter_chains.append(f"[{avatar_input_idx}:v]{crop_mod}{flip_mod}{scale_mod},format=yuva420p,colorchannelmixer=aa={avatar_opacity:.2f}[av_layer]")

        # Dynamic vertical bounce & breathing motion in overlay
        bounce_mod = "+(sin(t*5.5)*10)" if avatar_bounce else ""

        if avatar_x_custom is not None and avatar_y_custom is not None:
            ax = int(float(avatar_x_custom))
            ay = int(float(avatar_y_custom))
            if avatar_sway:
                x_expr = f"'{ax}+(sin(t*{avatar_sway_speed})*14)'"
                y_expr = f"'{ay}+(cos(t*{avatar_sway_speed*1.3})*8){bounce_mod}'"
            else:
                x_expr = f"'{ax}'"
                y_expr = f"'{ay}{bounce_mod}'"
        else:
            if avatar_anchor == "left":
                base_x = "W*0.06"
            elif avatar_anchor == "center":
                base_x = "(W-w)/2"
            else:
                base_x = "W*0.80"

            if avatar_sway:
                x_expr = f"'({base_x})+(sin(t*{avatar_sway_speed})*(W*0.03))'"
            else:
                x_expr = f"'{base_x}'"
            y_expr = f"'H-h-35{bounce_mod}'"

        filter_chains.append(f"{current_v}[av_layer]overlay=x={x_expr}:y={y_expr}[layer_av]")
        current_v = "[layer_av]"

    # 4a. Layer 4a: Optional Caption Background Box (Backdrop behind subtitles)
    if has_cap_bg and cap_bg_input_idx is not None:
        filter_chains.append(f"[{cap_bg_input_idx}:v]format=yuva420p[cap_bg_layer]")
        filter_chains.append(f"{current_v}[cap_bg_layer]overlay=x={cap_box_x}:y={cap_box_y}[layer_cap_bg]")
        current_v = "[layer_cap_bg]"

    # 4b. Layer 4b: Optional Subtitles with Custom Fonts & Glow
    ass_path = params.get("ass_subtitles_path")
    if ass_path and Path(ass_path).exists():
        escaped_ass = escape_ffmpeg_path(str(Path(ass_path).resolve()))
        fonts_dir_esc = escape_ffmpeg_path(str(FONTS_DIR.resolve()))
        filter_chains.append(f"{current_v}ass=filename='{escaped_ass}':fontsdir='{fonts_dir_esc}'[v_final]")
    else:
        filter_chains.append(f"{current_v}null[v_final]")

    # --- AUDIO GRAPH ---
    has_audio = yt_info.get("has_audio", True)
    if has_audio:
        yt_audio_filters = build_audio_filter_chain(
            pitch_semitones=pitch,
            speed=speed,
            copyright_shield=copyright_shield,
            volume=1.0
        )
        filter_chains.append(f"[1:a]{yt_audio_filters}[yt_audio]")
    else:
        filter_chains.append(f"anullsrc=channel_layout=stereo:sample_rate=48000,atrim=0:{render_duration}[yt_audio]")

    if has_bgm and bgm_input_idx is not None:
        filter_chains.append(f"[{bgm_input_idx}:a]volume={bgm_volume:.3f}[bgm_audio]")
        filter_chains.append("[yt_audio][bgm_audio]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[a_final]")
        current_a = "[a_final]"
    else:
        current_a = "[yt_audio]"

    # Finalize filter complex
    filter_complex_str = ";".join(filter_chains)
    cmd.extend(["-filter_complex", filter_complex_str])
    cmd.extend(["-map", "[v_final]", "-map", current_a])

    # Hardware GPU Encoder Selection & Speedup Tuning
    if encoder == "h264_nvenc":
        nv_preset = "p1" if is_30s_preview else "p3"
        nv_tune = "ll" if is_30s_preview else "hq"
        cmd.extend([
            "-c:v", "h264_nvenc",
            "-preset", nv_preset,
            "-tune", nv_tune,
            "-b:v", bitrate,
            "-maxrate", "9500k",
            "-bufsize", "14000k"
        ])
    elif encoder == "h264_qsv":
        qsv_preset = "veryfast" if is_30s_preview else "faster"
        cmd.extend([
            "-c:v", "h264_qsv",
            "-preset", qsv_preset,
            "-b:v", bitrate
        ])
    elif encoder == "h264_amf":
        cmd.extend([
            "-c:v", "h264_amf",
            "-quality", "speed",
            "-b:v", bitrate
        ])
    else:
        cpu_preset = "ultrafast" if is_30s_preview else "veryfast"
        cmd.extend([
            "-c:v", "libx264",
            "-preset", cpu_preset,
            "-crf", "22"
        ])

    cmd.extend([
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", f"{render_duration:.2f}",
        "-progress", "pipe:1",
        str(output_path)
    ])

    # Execute FFmpeg subprocess with live progress parsing
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    )

    fps_val = 0
    start_time = time.time()

    def parse_progress():
        nonlocal fps_val
        for line in process.stdout:
            parts = line.strip().split("=")
            if len(parts) == 2:
                key, val = parts[0].strip(), parts[1].strip()
                if key == "fps":
                    try:
                        fps_val = int(float(val))
                    except Exception:
                        pass
                elif key == "out_time_us":
                    try:
                        us = int(val)
                        cur_sec = us / 1_000_000.0
                        pct = min(99.0, (cur_sec / render_duration) * 100.0)
                        elapsed = time.time() - start_time
                        if pct > 1.0:
                            total_est = (elapsed / pct) * 100.0
                            remain = max(0, int(total_est - elapsed))
                            m, s = divmod(remain, 60)
                            eta_str = f"{m:02d}:{s:02d}"
                        else:
                            eta_str = "--:--"
                        if progress_callback:
                            progress_callback(pct, fps_val, eta_str)
                    except Exception:
                        pass

    monitor_thread = threading.Thread(target=parse_progress, daemon=True)
    monitor_thread.start()

    stderr_output = process.communicate()[1]
    monitor_thread.join()

    if process.returncode != 0:
        err_msg = f"FFmpeg render failed with exit code {process.returncode}.\nStderr: {stderr_output[-1200:]}\nCommand: {' '.join(cmd[:15])}..."
        log_error("turbo_renderer", err_msg, task_id=task_id)
        raise RuntimeError(f"StreamMix FFmpeg render failed (code {process.returncode}): {stderr_output[-400:]}")

    if progress_callback:
        progress_callback(100.0, fps_val, "00:00")

    # Auto-open in Windows Explorer
    if not is_30s_preview and settings.get("auto_open_folder", True) and os.name == "nt":
        try:
            if hasattr(os, "startfile"):
                os.startfile(str(output_path.resolve().parent))
            else:
                os.system(f'explorer /select,"{str(output_path.resolve())}"')
        except Exception:
            pass

    return str(output_path.resolve())
