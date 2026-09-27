# ⚡ StreamMix Studio (Twitch + YouTube 1080p Remix Engine)

<p align="center">
  <img src="https://img.shields.io/badge/Resolution-1080p%2060fps-9146ff?style=for-the-badge&logo=twitch" alt="1080p 60fps" />
  <img src="https://img.shields.io/badge/Architecture-Single--Pass%20GPU-00f2fe?style=for-the-badge&logo=nvidia" alt="Single-Pass GPU" />
  <img src="https://img.shields.io/badge/AI%20Engine-Groq%20Llama--3-f59e0b?style=for-the-badge" alt="Groq Llama-3" />
  <img src="https://img.shields.io/badge/License-Proprietary-10b981?style=for-the-badge" alt="License" />
</p>

---

## 🚀 Overview

**StreamMix Studio** is a standalone, single-pass hardware-accelerated desktop workstation engineered for long-form reaction and commentary YouTube channels. It seamlessly transforms multi-hour Twitch VODs and YouTube streams into monetizable, transformative content in **5 to 7 minutes** via GPU acceleration (NVENC, QuickSync, or AMF).

---

## 🌟 Key Features

- **⚡ Single-Pass 60fps Turbo Compositor**: Overlays all 5 video/audio layers in a unified hardware-accelerated FFmpeg pipeline.
- **🛡️ Anti-Content-ID Spectral Shield**:
  - Acoustic pitch shifting (+0.6 semitones with time-stretch sync).
  - High/Low-pass filtration (45Hz – 16.5kHz) and 70% stereo widening.
  - Sub-audible micro-echo reflections to evade audio fingerprinters.
  - Micro-crop edge scaling to evade automated video hashing.
- **🎭 Harmonic Audio-Reactive Avatar**: Cutout avatar anchored on screen with continuous harmonic floating (`sin(t*0.4)`) and dynamic volume-reactive pulse bouncing.
- **🧠 Groq AI SEO & Metadata Suite**: Multi-key rotation pool with auto-failover to generate high-CTR titles, viral descriptions, chapters, and tags in < 2 seconds.
- **⚡ Quick 30-Second Test Slice**: Fast 15-second render slice to verify sync, avatar position, blur, and opacity before rendering long master videos.
- **📦 Floating Dual-Worker Dock**: Concurrency queue rendering up to 2 tasks in parallel with live real-time FPS, ETA, and progress metrics.

---

## 🗂️ Project File Structure

```
twitchyoutube/
├── 1_RUN_APP.bat              # One-click Windows desktop runner
├── desktop_launcher.py        # Native MS Edge app mode launcher & port cleaner
├── requirements.txt           # Python backend dependencies
├── README.md                  # Project overview & documentation
│
├── bin/                       # Portable standalone multimedia binaries
│   ├── ffmpeg.exe             # High-speed GPU-enabled FFmpeg
│   └── ffprobe.exe            # Media stream inspector
│
├── backend/                   # Modular Python Engine
│   ├── __init__.py
│   ├── config.py              # Path resolver & hardware encoder detection
│   ├── api_pool.py            # Groq API pool manager with auto-failover
│   ├── downloader.py          # yt-dlp stream grabber & ffprobe inspector
│   ├── audio_engine.py        # Pitch/tempo sync & anti-copyright shield
│   ├── groq_metadata.py       # Groq Llama-3 viral title & chapter generator
│   ├── turbo_renderer.py      # Master 5-layer single-pass FFmpeg compositor
│   ├── task_manager.py        # Dual-worker asyncio queue & progress tracker
│   └── server.py              # FastAPI REST endpoints & file router
│
├── frontend/                  # Zero-Dependency Obsidian-Dark Studio UI
│   ├── index.html             # Studio editor, live canvas, keys & settings
│   ├── styles.css             # Glassmorphism, animations & typography
│   ├── app.js                 # Reactive state controller & canvas animation
│   └── docs.html              # Comprehensive operator manual (Light/Dark)
│
└── data/                      # Local studio runtime directories
    ├── api_keys.json          # Encrypted local API key storage
    ├── settings.json          # Hardware & render preferences
    ├── avatars/               # Host PNG cutouts
    ├── bgm/                   # Ambient background audio tracks
    ├── downloads/             # Cached stream downloads
    ├── temp/                  # Transcoding scratchpad
    └── outputs/               # Finished 1080p 60fps MP4 master files
```

---

## ⚙️ Installation & Usage

1. **Prerequisites**: Python 3.10+ installed on Windows.
2. **Launch Studio**:
   - Double-click `1_RUN_APP.bat` inside `twitchyoutube/`.
   - The studio will launch in a clean, borderless native desktop window.
3. **Configure Settings**:
   - Input your Twitch VOD and YouTube URL or local files.
   - Adjust Gaussian blur (recommended: `18px`) and YouTube opacity (recommended: `50%`).
   - Run a **⚡ Quick 30s Slice Test** to preview your composition.
   - Click **START 1080P MASTER RENDER** to produce your finished video.

---

## 👨‍💻 Developed By

**Abid Ali** — Full-Stack AI & Video Systems Engineer

- 🌐 **Portfolio**: [abidalidev.com](https://abidalidev.com)
- 💼 **LinkedIn**: [linkedin.com/in/abidalidev](https://linkedin.com/in/abidalidev)
- 🐦 **X (Twitter)**: [@abidalidevv](https://x.com/abidalidevv)
- 📸 **Instagram**: [@abidalidevv](https://instagram.com/abidalidevv)
- 📘 **Facebook**: [facebook.com/abidalidevv](https://facebook.com/abidalidevv)

---
*StreamMix Studio © 2026. Engineered for peak creator velocity.*
