import math
from typing import List


def calculate_pitch_ratio(semitones: float) -> float:
    """Calculates frequency ratio for musical pitch shift by semitones."""
    return 2.0 ** (semitones / 12.0)


def build_audio_filter_chain(
    pitch_semitones: float = 0.0,
    speed: float = 1.0,
    copyright_shield: bool = True,
    volume: float = 1.0
) -> str:
    """
    Constructs an FFmpeg audio filter chain that:
    1. Shifts voice pitch without altering speech duration.
    2. Adjusts commentary playback tempo synchronously.
    3. Applies YouTube Content ID acoustic micro-cloaking (stereo widening + boundary shaping).
    """
    filters: List[str] = []

    # 1. Pitch shift using asetrate + atempo compensation
    if abs(pitch_semitones) > 0.05:
        ratio = calculate_pitch_ratio(pitch_semitones)
        sample_rate = int(44100 * ratio)
        comp_tempo = round(1.0 / ratio, 4)
        filters.append(f"asetrate={sample_rate}")
        filters.append(f"atempo={comp_tempo}")

    # 2. User Speed Control
    if abs(speed - 1.0) > 0.02:
        safe_speed = max(0.5, min(2.0, speed))
        filters.append(f"atempo={safe_speed:.3f}")

    # 3. 🛡️ YouTube Content ID Acoustic Shield Cloaking
    if copyright_shield:
        # Stereo widening gently widens acoustic soundstage
        filters.append("stereowiden=70")
        # Strips imperceptible subsonic and ultrasonic frequencies used by fingerprint algorithms
        filters.append("highpass=f=45")
        filters.append("lowpass=f=16500")
        # Microscopic 8ms phase detuning to defeat automated audio matching
        filters.append("aecho=0.8:0.8:8:0.15")

    # 4. Volume Gain
    if abs(volume - 1.0) > 0.02:
        filters.append(f"volume={volume:.2f}")

    return ",".join(filters) if filters else "anull"


def build_video_shield_filter() -> str:
    """
    Returns visual anti-copyright cloaking filters:
    0.5% digital micro-zoom (crops 2px per edge) + imperceptible vignette
    to disrupt spatial frame-hash matching without audience noticing.
    """
    return "crop=in_w-4:in_h-4,scale=1920:1080,vignette=PI/5"
