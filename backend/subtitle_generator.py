"""
StreamMix Studio — Subtitle Generator
VG-reference ASS engine with neon glow, kinetic word bounce, and exact preview parity.
"""
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import TEMP_DIR, log_error
from .api_pool import groq_pool

# ─── PRESET STYLES ────────────────────────────────────────────────────────────
# font_size  : slider units (22-28); multiplied by 4.2 → 1920x1080 ASS pixel size
# shadow_color: ASS BackColour (used as glow color by libass when blur > 0)
# glow_blur  : \blur value in override tags (0=off, 4-12=neon glow)
# outline_width / shadow_dist: pre-scaling values (×2.8 / ×2.4 for 16:9)
PRESET_STYLES = {
    "capcut_yellow": {
        "name": "CapCut Viral Yellow",
        "font_name": "Montserrat",
        "font_size": 24,
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H0010E0FF",   # Yellow (#FFE010) BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H990010E0",   # Yellow glow shadow
        "outline_width": 3.8,
        "shadow_dist": 3.0,
        "glow_blur": 8,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "hormozi_green": {
        "name": "Hormozi Punch Green",
        "font_name": "Impact",
        "font_size": 26,
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H0014FF39",   # Neon Green BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H9914FF39",   # Green glow
        "outline_width": 4.5,
        "shadow_dist": 3.5,
        "glow_blur": 10,
        "bold": 1, "uppercase": True, "margin_v": 125
    },
    "neon_cyber": {
        "name": "Neon Cyber Glow",
        "font_name": "Montserrat",
        "font_size": 24,
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H00FFFF00",   # Cyan BGR
        "outline_color":   "&H00401000",
        "shadow_color":    "&H99FFFF00",   # Cyan glow
        "outline_width": 3.5,
        "shadow_dist": 4.0,
        "glow_blur": 12,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "red_fire": {
        "name": "Red Fire Accent",
        "font_name": "Impact",
        "font_size": 24,
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H003333FF",   # Red BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H993333FF",   # Red glow
        "outline_width": 4.0,
        "shadow_dist": 3.0,
        "glow_blur": 8,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "clean_minimal": {
        "name": "Clean Minimalist",
        "font_name": "Inter",
        "font_size": 22,
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H00E0E0E0",
        "outline_color":   "&H00151515",
        "shadow_color":    "&H60000000",
        "outline_width": 2.0,
        "shadow_dist": 1.5,
        "glow_blur": 0,
        "bold": 1, "uppercase": False, "margin_v": 115
    },
    "mrbeast_punch": {
        "name": "MrBeast Punchy Gold",
        "font_name": "Bangers",
        "font_size": 28,
        "primary_color":   "&H0010E0FF",
        "highlight_color": "&H003333FF",   # Red BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H993333FF",   # Red glow
        "outline_width": 5.5,
        "shadow_dist": 3.5,
        "glow_blur": 10,
        "bold": 1, "uppercase": True, "margin_v": 130
    },
    "ali_abdaal": {
        "name": "Ali Abdaal Aesthetic",
        "font_name": "Poppins",
        "font_size": 22,
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H004DA9FF",   # Orange-amber BGR
        "outline_color":   "&H001A1A1A",
        "shadow_color":    "&H604DA9FF",   # Soft glow
        "outline_width": 2.5,
        "shadow_dist": 2.0,
        "glow_blur": 6,
        "bold": 1, "uppercase": False, "margin_v": 120
    },
    "iman_gadzhi": {
        "name": "Iman Gadzhi Luxury",
        "font_name": "Cinzel",
        "font_size": 23,
        "primary_color":   "&H00EAFEF4",
        "highlight_color": "&H0037AFD4",   # Gold BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H9937AFD4",   # Gold glow
        "outline_width": 3.5,
        "shadow_dist": 3.0,
        "glow_blur": 8,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "tiktok_violet": {
        "name": "TikTok Viral Violet",
        "font_name": "Archivo Black",
        "font_size": 25,
        "primary_color":   "&H00852AFF",
        "highlight_color": "&H00FF00BD",   # Violet BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H99FF00BD",   # Violet glow
        "outline_width": 4.5,
        "shadow_dist": 4.0,
        "glow_blur": 10,
        "bold": 1, "uppercase": True, "margin_v": 125
    },
    "podcast_pill": {
        "name": "Vox / Podcast Box",
        "font_name": "Outfit",
        "font_size": 22,
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H0000E6FF",   # Amber BGR
        "outline_color":   "&H00111111",
        "shadow_color":    "&H9900E6FF",   # Amber glow
        "outline_width": 3.0,
        "shadow_dist": 3.0,
        "glow_blur": 8,
        "bold": 1, "uppercase": False, "margin_v": 120
    },
    "streamer_lime": {
        "name": "Streamer High-Voltage",
        "font_name": "Luckiest Guy",
        "font_size": 26,
        "primary_color":   "&H0000FFA6",
        "highlight_color": "&H00FFF000",   # Lime BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H99FFF000",   # Lime glow
        "outline_width": 5.0,
        "shadow_dist": 4.0,
        "glow_blur": 12,
        "bold": 1, "uppercase": True, "margin_v": 130
    },
    "dark_stoic": {
        "name": "Stoic Slate Wisdom",
        "font_name": "Oswald",
        "font_size": 26,
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H00F88C81",
        "outline_color":   "&H000F0F14",
        "shadow_color":    "&H80000000",
        "outline_width": 4.0,
        "shadow_dist": 2.5,
        "glow_blur": 0,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "retro_vintage": {
        "name": "Retro Vintage 70s",
        "font_name": "Arial Black",
        "font_size": 25,
        "primary_color":   "&H003CA0FF",
        "highlight_color": "&H0000FFFF",   # Yellow BGR
        "outline_color":   "&H00101530",
        "shadow_color":    "&H9900FFFF",   # Yellow glow
        "outline_width": 4.5,
        "shadow_dist": 3.0,
        "glow_blur": 8,
        "bold": 1, "uppercase": True, "margin_v": 125
    },
    "midnight_blue": {
        "name": "Midnight Blue Neon",
        "font_name": "Montserrat",
        "font_size": 24,
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H00FF9000",   # Sky blue BGR
        "outline_color":   "&H004A150A",
        "shadow_color":    "&H99FF9000",   # Blue glow
        "outline_width": 4.0,
        "shadow_dist": 3.5,
        "glow_blur": 10,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "true_crime": {
        "name": "True Crime Cold",
        "font_name": "Impact",
        "font_size": 24,
        "primary_color":   "&H00E0E0E0",
        "highlight_color": "&H002020E0",   # Crimson BGR
        "outline_color":   "&H00050505",
        "shadow_color":    "&H802020E0",   # Red glow
        "outline_width": 4.0,
        "shadow_dist": 3.0,
        "glow_blur": 6,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "wealth_cash": {
        "name": "Wealth & Cash Mint",
        "font_name": "Impact",
        "font_size": 26,
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H0070DF10",   # Emerald BGR
        "outline_color":   "&H0010300A",
        "shadow_color":    "&H9970DF10",   # Emerald glow
        "outline_width": 4.5,
        "shadow_dist": 3.5,
        "glow_blur": 10,
        "bold": 1, "uppercase": True, "margin_v": 125
    },
    "cosmic_violet": {
        "name": "Cosmic Deep Violet",
        "font_name": "Montserrat",
        "font_size": 24,
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H00FC42B2",   # Violet BGR
        "outline_color":   "&H00350B40",
        "shadow_color":    "&H99FC42B2",   # Violet glow
        "outline_width": 4.0,
        "shadow_dist": 4.0,
        "glow_blur": 12,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "cinematic_bronze": {
        "name": "Cinematic Bronze Gold",
        "font_name": "Cinzel",
        "font_size": 23,
        "primary_color":   "&H00E8F0F8",
        "highlight_color": "&H00258BD4",   # Bronze gold BGR
        "outline_color":   "&H00081220",
        "shadow_color":    "&H99258BD4",   # Gold glow
        "outline_width": 3.5,
        "shadow_dist": 3.0,
        "glow_blur": 8,
        "bold": 1, "uppercase": True, "margin_v": 120
    }
}


def sec_to_ass_time(sec: float) -> str:
    """Formats seconds into ASS timestamp H:MM:SS.cs"""
    sec = max(0.0, sec)
    hrs = int(sec // 3600)
    mins = int((sec % 3600) // 60)
    secs = int(sec % 60)
    centis = int(round((sec - int(sec)) * 100))
    if centis >= 100:
        secs += 1
        centis = 0
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"


def transcribe_audio_words(audio_file_path: str) -> List[Dict[str, Any]]:
    """Transcribes audio file using Groq Whisper with word-level timestamps."""
    client, key_id = groq_pool.get_client()
    try:
        with open(audio_file_path, "rb") as af:
            resp = client.audio.transcriptions.create(
                file=af,
                model="whisper-large-v3",
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
        words = getattr(resp, "words", None)
        if not words and isinstance(resp, dict):
            words = resp.get("words", [])
        return words or []
    except Exception as e:
        log_error("subtitle_generator", f"Groq Whisper transcription failed: {e}", exc=e)
        return []


def generate_fallback_speech_words(duration_sec: float) -> List[Dict[str, Any]]:
    """Generates dynamic commentary words if audio was quiet or noise."""
    hooks = [
        "WAIT", "DID", "YOU", "SEE", "THAT?!",
        "NO", "WAY", "THIS", "ACTUALLY", "HAPPENED!",
        "WATCH", "CLOSELY", "RIGHT", "NOW!",
        "THIS", "IS", "ABSOLUTELY", "INSANE!",
        "LOOK", "AT", "THIS", "REACTION!",
        "UNBELIEVABLE", "MOMENT", "CAUGHT", "ON", "STREAM!"
    ]
    words = []
    t = 0.5
    idx = 0
    while t < max(3.0, duration_sec - 1.0):
        w = hooks[idx % len(hooks)]
        dur = 0.35 + (0.15 if len(w) > 5 else 0.0)
        words.append({"word": w, "start": round(t, 2), "end": round(t + dur, 2)})
        t += dur + 0.08
        idx += 1
    return words


def group_words_into_phrases(words: List[Dict[str, Any]], max_words: int = 5) -> List[List[Dict[str, Any]]]:
    """
    Groups spoken words into natural speech phrases.
    Breaks on terminal punctuation, spoken pauses (>=0.32s), commas, or max words.
    """
    phrases = []
    current_phrase = []

    for idx, w in enumerate(words):
        current_phrase.append(w)
        txt = str(w.get("word", "")).strip()

        has_terminal_punct = any(txt.endswith(p) for p in [".", "!", "?", "...", "…"])
        has_comma = any(txt.endswith(p) for p in [",", ";", ":"])

        is_pause = False
        if idx + 1 < len(words):
            gap = float(words[idx + 1].get("start", 0.0)) - float(w.get("end", 0.0))
            if gap >= 0.32:
                is_pause = True

        if has_terminal_punct or is_pause or (has_comma and len(current_phrase) >= 2) or len(current_phrase) >= max_words:
            phrases.append(current_phrase)
            current_phrase = []

    if current_phrase:
        phrases.append(current_phrase)

    return phrases


def create_ass_subtitles(
    words: List[Dict[str, Any]],
    preset_key: str = "capcut_yellow",
    caption_size: str = "large",
    font_family: Optional[str] = None,
    output_ass_path: Optional[str] = None,
    custom_y: Optional[Any] = None,
    custom_x: Optional[Any] = None,
    custom_w: Optional[Any] = None,
    custom_h: Optional[Any] = None,
    words_per_group: int = 5,
    start_offset: float = 0.0
) -> str:
    """
    Builds production 1080p ASS file matching VG reference engine output.

    Key features:
    - preset font_size (22-28) × 4.2 → pixel size for 1920x1080
    - Custom font_family override (if specified by user, retains template preset styling)
    - Colored neon glow via \\blur{N} + colored shadow_color in ASS override
    - Kinetic word bounce: \\fscx108\\fscy108\\b1 on active word
    - Exact canvas bounding box positioning (custom_x/y/w/h from drag)
    - VG-style zero-overlap cue resolver
    """
    style = PRESET_STYLES.get(preset_key, PRESET_STYLES["capcut_yellow"])
    font_name = style["font_name"]

    # Font family override if selected by user
    if font_family and str(font_family).strip() and str(font_family).strip().lower() != "default":
        font_name = str(font_family).strip()

    # ── Font size: VG engine approach (slider_unit × 4.2 × size_mult) ───────
    base_slider_fs = style.get("font_size", 24)
    size_multipliers = {"small": 0.85, "medium": 1.00, "large": 1.18, "huge": 1.38}
    size_mult = size_multipliers.get(caption_size, 1.18)
    ass_font_size = round(base_slider_fs * 4.2 * size_mult)

    # Blend with box-derived size if caption box was manually resized
    if custom_w is not None and custom_h is not None:
        box_w = float(custom_w)
        box_h = float(custom_h)
        fs_by_h = box_h * 0.42 * size_mult
        fs_by_w = box_w / 6.2 * size_mult
        derived_fs = int(min(fs_by_h, fs_by_w))
        ass_font_size = int(derived_fs * 0.55 + ass_font_size * 0.45)

    ass_font_size = max(72, min(190, ass_font_size))

    # ── Outline & Shadow (VG: ×2.8 / ×2.4 for 16:9) ─────────────────────────
    ass_outline_w = round(style.get("outline_width", 3.8) * 2.8, 1)
    ass_shadow_d  = round(style.get("shadow_dist", 3.0) * 2.4, 1)
    glow_blur     = style.get("glow_blur", 8)

    primary_c   = style["primary_color"]
    highlight_c = style["highlight_color"]
    outline_c   = style.get("outline_color", "&H00000000")
    shadow_c    = style.get("shadow_color", "&H80000000")
    bold        = style.get("bold", 1)
    uppercase   = style.get("uppercase", True)

    # ── Position anchor from preview bounding box ─────────────────────────────
    if custom_x is not None and custom_y is not None:
        bw = float(custom_w or 1152)
        bh = float(custom_h or 280)
        center_x = int(float(custom_x) + (bw / 2.0))
        center_y = int(float(custom_y) + (bh / 2.0))
    elif custom_x is not None:
        bw = float(custom_w or 1152)
        center_x = int(float(custom_x) + (bw / 2.0))
        center_y = 760
    elif custom_y is not None:
        bh = float(custom_h or 280)
        center_x = 960
        center_y = int(float(custom_y) + (bh / 2.0))
    else:
        center_x = 960
        center_y = 760

    center_x = max(80, min(1840, center_x))
    center_y = max(60, min(1020, center_y))

    # Base glow tag: apply blur to make outline/shadow spread as neon glow
    blur_tag = f"\\blur{glow_blur}" if glow_blur > 0 else ""

    header = f"""[Script Info]
Title: StreamMix Studio Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{ass_font_size},{primary_c},&H000000FF,{outline_c},{shadow_c},{bold},0,0,0,100,100,1.2,0,1,{ass_outline_w:.1f},{ass_shadow_d:.1f},2,50,50,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    # Shift words by start_offset
    shifted_words = []
    for w in words:
        st = float(w.get("start", 0.0)) - start_offset
        et = float(w.get("end", 0.0)) - start_offset
        txt = str(w.get("word", "")).strip()
        if et > 0 and txt:
            shifted_words.append({
                "start": max(0.0, st),
                "end":   max(0.05, et),
                "word":  txt.upper() if uppercase else txt
            })

    chunks = group_words_into_phrases(shifted_words, max_words=words_per_group or 5)

    # Build raw cues — one line per active-word highlight slot (VG style)
    raw_cues = []
    for chunk in chunks:
        chunk_start = float(chunk[0]["start"])

        for active_idx, active_word in enumerate(chunk):
            is_last = (active_idx == len(chunk) - 1)
            t_start = chunk_start if active_idx == 0 else float(active_word["start"])
            t_end   = float(active_word["end"]) if is_last else float(chunk[active_idx + 1]["start"])

            line_parts = []
            for idx, w in enumerate(chunk):
                raw_w = str(w.get("word", "")).strip().replace("{", "(").replace("}", ")")
                if idx == active_idx:
                    # Kinetic pop: highlight color + scale bounce + keep glow blur
                    line_parts.append(
                        f"{{\\c{highlight_c}&{blur_tag}\\fscx108\\fscy108\\b1}}{raw_w}"
                        f"{{\\c{primary_c}&\\fscx100\\fscy100\\b{bold}}}"
                    )
                else:
                    line_parts.append(raw_w)

            raw_cues.append({
                "start": t_start,
                "end":   t_end,
                "text":  " ".join(line_parts),
                "is_chunk_boundary": is_last
            })

    raw_cues.sort(key=lambda c: (c["start"], c["end"]))

    # VG Zero-Overlap Resolver
    total_cues = len(raw_cues)
    for i in range(total_cues):
        c_start = raw_cues[i]["start"]
        c_end   = raw_cues[i]["end"]
        is_boundary = raw_cues[i]["is_chunk_boundary"]

        if i < total_cues - 1:
            if raw_cues[i + 1]["start"] < c_start + 0.04:
                raw_cues[i + 1]["start"] = round(c_start + 0.04, 3)
            next_start = raw_cues[i + 1]["start"]

            if is_boundary:
                gap = next_start - c_end
                if gap > 0.08:
                    c_end = min(c_end + 0.28, next_start - 0.04)
                else:
                    c_end = max(c_start + 0.04, next_start - 0.04)
            else:
                if c_end > next_start or (next_start - c_end) <= 0.25:
                    c_end = next_start
                else:
                    c_end = min(c_end + 0.25, next_start - 0.02)
        else:
            c_end = max(c_end, c_start + 0.6)

        if c_end <= c_start:
            c_end = round(c_start + 0.04, 3)

        raw_cues[i]["start"] = round(c_start, 3)
        raw_cues[i]["end"]   = round(c_end, 3)

        w_start = sec_to_ass_time(c_start)
        w_end   = sec_to_ass_time(c_end)

        # Base position + glow on non-active words too (\\blur applies to outline glow)
        base_tags = f"\\an5\\pos({center_x},{center_y}){blur_tag}"
        events.append(
            f"Dialogue: 0,{w_start},{w_end},Default,,0,0,0,,{{{base_tags}}}{raw_cues[i]['text']}"
        )

    full_ass = header + "\n".join(events) + "\n"

    if not output_ass_path:
        output_ass_path = str(TEMP_DIR / f"subtitles_{int(time.time()*1000)}.ass")

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(full_ass)

    return str(Path(output_ass_path).resolve())
