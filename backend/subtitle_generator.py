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

# ─── PRESET STYLES (100% 1:1 Palette Matching with Frontend Canvas) ────────────
# Colors stored in ASS BGR format: &H00BBGGRR&
PRESET_STYLES = {
    "capcut_yellow": {
        "name": "CapCut Viral Yellow",
        "font_name": "Montserrat",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H0000FFFF",   # #ffff00 Yellow BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H9900CCFF",   # #ffcc00 Yellow glow
        "outline_width": 3.8,
        "shadow_dist": 2.6,
        "glow_blur": 8,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "hormozi_green": {
        "name": "Hormozi Punch Green",
        "font_name": "Impact",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H0066FF00",   # #00ff66 Neon Green BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H9900DD44",   # #00dd44 Green glow
        "outline_width": 4.2,
        "shadow_dist": 3.0,
        "glow_blur": 10,
        "bold": 1, "uppercase": True, "margin_v": 125
    },
    "mrbeast_punch": {
        "name": "MrBeast Punchy Gold",
        "font_name": "Bangers",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H0024BFFB",   # #fbbf24 Gold BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H990677D9",   # #d97706 Gold glow
        "outline_width": 4.8,
        "shadow_dist": 3.2,
        "glow_blur": 10,
        "bold": 1, "uppercase": True, "margin_v": 130
    },
    "ali_abdaal": {
        "name": "Ali Abdaal Aesthetic",
        "font_name": "Poppins",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H00F8BD38",   # #38bdf8 Electric Sky Blue BGR
        "outline_color":   "&H001A1A1A",
        "shadow_color":    "&H99C78402",   # #0284c7 Blue glow
        "outline_width": 3.6,
        "shadow_dist": 2.4,
        "glow_blur": 8,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "iman_gadzhi": {
        "name": "Iman Gadzhi Luxury",
        "font_name": "Cinzel",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H0000D7FF",   # #ffd700 Gold BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H990B9EF5",   # #f59e0b Gold glow
        "outline_width": 3.6,
        "shadow_dist": 2.8,
        "glow_blur": 8,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "tiktok_violet": {
        "name": "TikTok Viral Violet",
        "font_name": "Archivo Black",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H00EF46D9",   # #d946ef Magenta/Violet BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H99F755A8",   # #a855f7 Violet glow
        "outline_width": 4.2,
        "shadow_dist": 3.2,
        "glow_blur": 10,
        "bold": 1, "uppercase": True, "margin_v": 125
    },
    "podcast_pill": {
        "name": "Vox / Podcast Box",
        "font_name": "Outfit",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H00FFE500",   # #00e5ff Cyan BGR
        "outline_color":   "&H00111111",
        "shadow_color":    "&H99D8B400",   # #00b4d8 Cyan glow
        "outline_width": 3.6,
        "shadow_dist": 2.6,
        "glow_blur": 8,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "streamer_lime": {
        "name": "Streamer High-Voltage",
        "font_name": "Luckiest Guy",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H0035E6A3",   # #a3e635 Lime BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H9916CC84",   # #84cc16 Lime glow
        "outline_width": 4.5,
        "shadow_dist": 3.2,
        "glow_blur": 10,
        "bold": 1, "uppercase": True, "margin_v": 130
    },
    "neon_cyber": {
        "name": "Neon Cyber Glow",
        "font_name": "Montserrat",
        "primary_color":   "&H00FFFF00",   # #00ffff Cyan base BGR
        "highlight_color": "&H00FF00FF",   # #ff00ff Magenta active BGR
        "outline_color":   "&H00401000",
        "shadow_color":    "&H99EC55BF",   # #bf55ec Purple glow
        "outline_width": 3.8,
        "shadow_dist": 3.2,
        "glow_blur": 12,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "red_fire": {
        "name": "Red Fire Accent",
        "font_name": "Impact",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H004433FF",   # #ff3344 Fire Red BGR
        "outline_color":   "&H00000000",
        "shadow_color":    "&H994444EF",   # #ef4444 Red glow
        "outline_width": 4.2,
        "shadow_dist": 2.8,
        "glow_blur": 8,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "dark_stoic": {
        "name": "Stoic Slate Wisdom",
        "font_name": "Oswald",
        "primary_color":   "&H00E1D5CB",   # #cbd5e1 Slate BGR
        "highlight_color": "&H00FFFFFF",   # #ffffff White active
        "outline_color":   "&H000F0F14",
        "shadow_color":    "&H99B8A394",   # #94a3b8 Slate glow
        "outline_width": 3.6,
        "shadow_dist": 2.4,
        "glow_blur": 0,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "clean_minimal": {
        "name": "Clean Minimalist",
        "font_name": "Inter",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H00FFFFFF",
        "outline_color":   "&H00151515",
        "shadow_color":    "&H99B8A394",
        "outline_width": 2.6,
        "shadow_dist": 2.0,
        "glow_blur": 0,
        "bold": 1, "uppercase": True, "margin_v": 115
    },
    "retro_vintage": {
        "name": "Retro Vintage 70s",
        "font_name": "Arial Black",
        "primary_color":   "&H003CA0FF",   # #ffa03c Orange BGR
        "highlight_color": "&H0000FFFF",   # #ffff00 Yellow BGR
        "outline_color":   "&H00101530",
        "shadow_color":    "&H990B9EF5",   # #f59e0b Gold glow
        "outline_width": 4.2,
        "shadow_dist": 2.8,
        "glow_blur": 8,
        "bold": 1, "uppercase": True, "margin_v": 125
    },
    "midnight_blue": {
        "name": "Midnight Blue Neon",
        "font_name": "Montserrat",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H00F8BD38",   # #38bdf8 Electric Sky Blue BGR
        "outline_color":   "&H004A150A",
        "shadow_color":    "&H99EB6325",   # #2563eb Royal Blue glow
        "outline_width": 3.8,
        "shadow_dist": 3.0,
        "glow_blur": 10,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "true_crime": {
        "name": "True Crime Cold",
        "font_name": "Courier New",
        "primary_color":   "&H00E0E0E0",
        "highlight_color": "&H004444EF",   # #ef4444 Blood Red BGR
        "outline_color":   "&H00050505",
        "shadow_color":    "&H992626DC",   # #dc2626 Red glow
        "outline_width": 3.6,
        "shadow_dist": 2.6,
        "glow_blur": 6,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "wealth_cash": {
        "name": "Wealth & Cash Mint",
        "font_name": "Impact",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H0070DF10",   # #10df70 Cash Green BGR
        "outline_color":   "&H0010300A",
        "shadow_color":    "&H99699605",   # #059669 Emerald glow
        "outline_width": 4.2,
        "shadow_dist": 3.0,
        "glow_blur": 10,
        "bold": 1, "uppercase": True, "margin_v": 125
    },
    "cosmic_violet": {
        "name": "Cosmic Deep Violet",
        "font_name": "Montserrat",
        "primary_color":   "&H00FFFFFF",
        "highlight_color": "&H00FC84C0",   # #c084fc Lavender BGR
        "outline_color":   "&H00350B40",
        "shadow_color":    "&H99EA3393",   # #9333ea Purple glow
        "outline_width": 3.8,
        "shadow_dist": 3.2,
        "glow_blur": 12,
        "bold": 1, "uppercase": True, "margin_v": 120
    },
    "cinematic_bronze": {
        "name": "Cinematic Bronze Gold",
        "font_name": "Cinzel",
        "primary_color":   "&H00F8F0E8",   # #e8f0f8 Soft White
        "highlight_color": "&H000B9EF5",   # #f59e0b Amber Gold BGR
        "outline_color":   "&H00081220",
        "shadow_color":    "&H990677D9",   # #d97706 Bronze glow
        "outline_width": 3.5,
        "shadow_dist": 2.8,
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
    Builds production 1080p ASS file with exact preview canvas parity.

    Key improvements:
    - 1:1 Color & Font match with frontend preview templates
    - Accurate visual font size (matches CSS 2.5vw = ~48-56px)
    - Dynamic multi-line wrapping (\\N) so words strictly stay inside the box
    - Neon glow via \\blur + colored shadow
    - Kinetic word bounce: \\fscx108\\fscy108\\b1 on active word
    - Centered bounding box positioning (custom_x/y/w/h from live canvas drag)
    - VG-style zero-overlap cue resolver
    """
    style = PRESET_STYLES.get(preset_key, PRESET_STYLES["capcut_yellow"])
    font_name = style["font_name"]

    # Font family override if selected by user
    if font_family and str(font_family).strip() and str(font_family).strip().lower() != "default":
        font_name = str(font_family).strip()

    # ── Font size: Exact scale parity with preview canvas (Large, Bold & Punchy) ──
    size_map = {"small": 72, "medium": 84, "large": 96, "huge": 115}
    base_fs = size_map.get(caption_size, 96)

    # Dynamic scaling based on custom bounding box (maintaining large readability)
    if custom_w is not None and custom_h is not None:
        box_w = float(custom_w)
        box_h = float(custom_h)
        # Allow 2-3 lines stacked with comfortable vertical line spacing
        max_fs_by_h = box_h / 2.2
        max_fs_by_w = box_w / 7.0
        capped_fs = min(max_fs_by_h, max_fs_by_w)
        ass_font_size = int(min(base_fs, max(68, capped_fs)))
    else:
        box_w = 1152.0
        box_h = 240.0
        ass_font_size = base_fs

    # ── Outline & Shadow (Proportional to 96px viral typography) ───────────
    ass_outline_w = round(max(4.2, style.get("outline_width", 3.8) * 1.2), 1)
    ass_shadow_d  = round(max(3.2, style.get("shadow_dist", 2.8) * 1.2), 1)
    glow_blur     = max(10, style.get("glow_blur", 8))

    primary_c   = style["primary_color"]
    highlight_c = style["highlight_color"]
    outline_c   = style.get("outline_color", "&H00000000")
    shadow_c    = style.get("shadow_color", "&H99000000")
    bold        = style.get("bold", 1)
    uppercase   = style.get("uppercase", True)

    # ── Position anchor from preview bounding box ─────────────────────────────
    if custom_x is not None and custom_y is not None:
        bw = float(custom_w or 1152)
        bh = float(custom_h or 240)
        center_x = int(float(custom_x) + (bw / 2.0))
        center_y = int(float(custom_y) + (bh / 2.0))
    elif custom_x is not None:
        bw = float(custom_w or 1152)
        center_x = int(float(custom_x) + (bw / 2.0))
        center_y = 760
    elif custom_y is not None:
        bh = float(custom_h or 240)
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

    # Calculate line wrapping limits based on box width and font size
    # In bold fonts, average char width is ~0.58 * font_size
    line_char_limit = max(8, int((box_w * 0.90) / (ass_font_size * 0.58)))
    max_words_per_line = 2 if box_w < 650 else (3 if box_w < 1000 else 4)

    # Build raw cues with intelligent multi-line \N wrapping
    raw_cues = []
    for chunk in chunks:
        chunk_start = float(chunk[0]["start"])

        # Determine line groupings for this chunk so text stays strictly inside the box
        chunk_lines = []
        cur_line = []
        cur_len = 0
        for idx, w in enumerate(chunk):
            w_txt = str(w.get("word", "")).strip()
            w_len = len(w_txt)
            if cur_line and (cur_len + 1 + w_len > line_char_limit or len(cur_line) >= max_words_per_line):
                chunk_lines.append(cur_line)
                cur_line = [idx]
                cur_len = w_len
            else:
                cur_line.append(idx)
                cur_len += (1 if cur_len > 0 else 0) + w_len
        if cur_line:
            chunk_lines.append(cur_line)

        for active_idx, active_word in enumerate(chunk):
            is_last = (active_idx == len(chunk) - 1)
            t_start = chunk_start if active_idx == 0 else float(active_word["start"])
            t_end   = float(active_word["end"]) if is_last else float(chunk[active_idx + 1]["start"])

            line_strings = []
            for line_indices in chunk_lines:
                line_words = []
                for idx in line_indices:
                    raw_w = str(chunk[idx].get("word", "")).strip().replace("{", "(").replace("}", ")")
                    if idx == active_idx:
                        # Kinetic pop: highlight color + punchy scale bounce + keep glow blur
                        line_words.append(
                            f"{{\\c{highlight_c}&{blur_tag}\\fscx122\\fscy122\\b1}}{raw_w}"
                            f"{{\\c{primary_c}&\\fscx100\\fscy100\\b{bold}}}"
                        )
                    else:
                        line_words.append(raw_w)
                line_strings.append(" ".join(line_words))

            # Multi-line text joined by \\N for native ASS centered multi-line rendering
            cues_text = "\\N".join(line_strings)

            raw_cues.append({
                "start": t_start,
                "end":   t_end,
                "text":  cues_text,
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
