# ⚡ StreamMix Studio (Twitch + YouTube 1080p 60fps Remix Engine)

<p align="center">
  <img src="https://img.shields.io/badge/Resolution-1080p%2060fps-9146ff?style=for-the-badge&logo=twitch" alt="1080p 60fps" />
  <img src="https://img.shields.io/badge/Architecture-Single--Pass%20GPU-00f2fe?style=for-the-badge&logo=nvidia" alt="Single-Pass GPU" />
  <img src="https://img.shields.io/badge/Captions-18%20CapCut%20Presets-ec4899?style=for-the-badge" alt="18 Subtitle Presets" />
  <img src="https://img.shields.io/badge/AI%20Engine-Groq%20Llama--3%20%2B%20Whisper-f59e0b?style=for-the-badge" alt="Groq Llama-3 + Whisper" />
  <img src="https://img.shields.io/badge/License-Proprietary-10b981?style=for-the-badge" alt="License" />
</p>

---

## 🚀 Overview

**StreamMix Studio** is a standalone, single-pass hardware-accelerated desktop workstation engineered specifically for long-form reaction and commentary YouTube channels. It turns multi-hour Twitch VODs and YouTube videos into monetizable, transformative content in **5 to 7 minutes** via GPU acceleration (Nvidia NVENC, AMD AMF, Intel QuickSync, or CPU fallback).

---

## 🌟 Key Features

### 1. ⚡ Single-Pass 60fps Turbo Compositor
- Overlays up to 5 video/audio layers simultaneously in a unified hardware-accelerated FFmpeg pipeline:
  - **Layer 1: Background Gameplay** (Twitch/YouTube URL or Local MP4/MKV, 100% muted, looped, Gaussian blur).
  - **Layer 2: Reaction Master Track** (YouTube URL or Local File, duration anchor, variable opacity 10%–100%, blur, speed & pitch manipulation).
  - **Layer 3: Host Avatar Cutout** (PNGtuber live host with slow sway, audio-reactive bounce, mirror flip, and outer glow).
  - **Layer 4: Dynamic Subtitles** (18 viral CapCut styles, custom font family overrides, draggable/resizable bounding box, custom rounded backdrop box).
  - **Layer 5: Ambient Background Music** (Auto-ducked ambient soundtrack).

### 2. 🛡️ Anti-Content-ID Protection Shield (YouTube Cloak)
- 1-Click anti-copyright cloaking with zero human-perceptible degradation:
  - **Acoustic micro-pitch shift** (+0.6 semitones with time-stretch lip sync).
  - **Stereo widening** (70%) and **frequency band shaping** (45Hz – 16.5kHz) to disrupt automated acoustic fingerprints.
  - **Micro-echo reflections** cancelling phase-correlation matching.
  - **Micro-edge digital zoom / crop** defeating automated spatial frame hashes.

### 3. ✂️ Background Video Cut Controls
- Flexible quick-cut presets (`No Cut`, `5 min`, `10 min`, `15 min`, and `Custom duration`) to slice only what you need without downloading multi-gigabyte 3-hour VODs.

### 4. 🔤 18 Viral CapCut Subtitle Presets & Custom Backdrop
- Instant visual templates: *CapCut Yellow, Hormozi Green, MrBeast Gold, Ali Abdaal, Luxury Gold, TikTok Violet, Podcast Box, Streamer Lime, Neon Cyber, Red Fire, Stoic Slate, Clean Minimal, Retro 70s, Midnight Blue, Cyberpunk Yellow, Sunset Coral, Emerald Glow, Bubblegum Pink*.
- Live custom font family selector (*Montserrat, Poppins, Impact, Arial Black, Bangers, Luckiest Guy, Archivo Black, Cinzel, Oswald, Outfit, Inter, Courier New, Trebuchet MS*).
- Optional rounded background backdrop box with live hex color picker and opacity slider.

### 5. 🎭 Interactive 16:9 Canvas Stage & Drag-and-Drop
- Live visual canvas preview with draggable, resizable bounding boxes for both the **Host Avatar** and **Subtitles Box**.
- 1-Click Preset Alignments (`Left`, `Center`, `Right` for Avatar; `Bottom Area`, `Center Screen` for Subtitles).
- "Reset Position" button for restoring safe lower-third margins.

### 6. ⚡ Quick 30-Second Fast Slice Preview
- Instant 4–5 second test render of a 30-second slice to verify positioning, colors, glow, audio pitch, and typography before starting the full 1-hour export.
- Minimizable floating test player with quick playback controls and error log inspector.

### 7. 📦 Minimizable Floating Dual-Worker Dock
- Concurrency queue capable of rendering **up to 2 tasks in parallel**.
- Real-time live statistics: active stage, progress bar, current FPS, and accurate ETA.

### 8. 🧠 Groq AI API Pool & Viral Metadata Generator
- Multi-key rotation pool with auto-failover on HTTP 429 rate limits.
- Sub-second Whisper transcription + Llama-3 AI title generator, SEO descriptions, formatted YouTube chapters, and viral tags.

### 9. 🖥️ Native Desktop Window (Zero Browser Dependency)
- Runs as a true native desktop application via Microsoft Edge WebView2 (`pywebview`).
- **No Chrome Launched:** Eliminates background browser overhead and memory bloat.
- **No Address Bar:** Clean, professional borderless UI with zero `127.0.0.1` localhost URLs.
- **Low RAM Profile:** Slashes RAM consumption from 1.5GB+ down to ~150MB, prioritizing GPU VRAM and CPU cores for encoding.

### 10. 📊 Tri-Bar Real-Time Progress Monitoring
- Eliminates guesswork with 3 distinct color-coded live progress monitors:
  - 🟣 **Twitch Stream Download Bar (Purple):** Real-time chunk transfer and stream speed.
  - 🔴 **YouTube Reaction Download Bar (Red):** Direct media download and audio demux tracking.
  - 🔷 **GPU Hardware Compositing Bar (Cyan):** Live rendering percentage, encoding FPS, elapsed time, and ETA.

### 11. ⏱️ 1-Hour+ Long Video Audio Chunking & Whisper Resilience
- Bypasses Groq Whisper's 25MB file size ceiling via automatic **10-minute smart audio chunking**.
- Dispatches chunks in parallel across your multi-key pool, transcribing 1-hour audio in **8–12 seconds**.
- Automatic timestamp offset stitching ensures zero subtitle drift across 60+ minute productions.
- Exponential backoff retry logic handles HTTP 429 rate limits smoothly.

### 12. 🧹 One-Click Storage Cache & Scratchpad Cleaner
- Integrated disk usage inspector analyzing `data/temp/`, `data/downloads/`, and `data/outputs/`.
- 1-Click safe garbage collection purges intermediate downloads and scratch audio chunks while keeping finished master exports safe.

### 13. 🛡️ Master 14 Optimization Engine & Microsecond Lipsync Lock
- **Microsecond Lipsync Lock**: Injected `aresample=async=1000` eliminates all audio-to-video drift across 1-hour timelines.
- **Packet Buffer Overflow Prevention**: `-max_muxing_queue_size 1024` prevents high-complexity compositing crashes.
- **4-Tier Hardware Cascade**: NVENC ➔ QSV ➔ AMF ➔ Windows MediaFoundation (`h264_mf`) ➔ CPU fallback.
- **Zero-Latency In-Memory Probe Cache**: Instant 0ms media probing without repetitive ffprobe disk calls.
- **LibASS Syntax Sanitizer**: Strips curly brackets and backslashes from Whisper output to prevent caption engine crashes.

### 14. 🌐 100% Machine-Independent Portability & In-Window Modal Docs
- **Zero Hardcoded Paths**: Dynamic relative pathing (`BASE_DIR / "data"`) ensures seamless sharing across any PC or drive letter.
- **In-Window Documentation**: Clicking "Docs Manual" opens the complete operator manual directly inside a sleek in-window modal popup — no browser tabs, no address bars.

---

## 🗂️ Project File Structure

```
twitchyoutube/
├── 1_RUN_APP.bat                        # One-click Windows desktop runner (dev mode)
├── BUILD_INSTALLER.bat                  # One-click Windows Setup Installer builder (Setup.exe)
├── BUILD_EXE.bat                        # One-click standalone executable packager (PyInstaller)
├── desktop_launcher.py                  # Native WebView2 desktop launcher & port cleaner
├── installer.iss                        # Inno Setup compiler definition script
├── requirements.txt                     # Python backend dependencies
├── README.md                            # Studio overview & quickstart guide
├── BRAIN.md                             # Comprehensive master architecture blueprint & system brain
├── extra/                               # Test scripts, benchmarks & archived development files
│
├── tools/                               # Distribution & packaging utilities
│   ├── create_installer.py              # Zero-dependency setup compiler & portable zip bundler
│   └── installer_gui.py                 # Modern standalone Tkinter Windows Setup Wizard
│
├── bin/                                 # Portable standalone multimedia binaries
│   ├── ffmpeg.exe                       # High-speed GPU-enabled FFmpeg executable
│   └── ffprobe.exe                      # Media stream & codec inspector
│
├── backend/                             # Modular Python Backend Engine
│   ├── __init__.py                      # Package initializer
│   ├── config.py                        # Path resolver, GPU encoder detection & error logging
│   ├── api_pool.py                      # Groq API pool manager with latency tests & auto-failover
│   ├── downloader.py                    # yt-dlp parallel slicer (anti-bot bypass) & 2s fast prober
│   ├── audio_engine.py                  # Pitch/tempo sync & anti-copyright acoustic filter chains
│   ├── subtitle_generator.py            # Multilingual Whisper transcriber & 18 ASS subtitle styles
│   ├── groq_metadata.py                 # Groq Llama-3 viral title, chapter & tag generator
│   ├── turbo_renderer.py                # Master 5-layer single-pass FFmpeg hardware compositor
│   ├── task_manager.py                  # Dual-worker asyncio queue, progress tracking & events
│   └── server.py                        # FastAPI REST endpoints, static files & Explorer launcher
│
├── frontend/                            # Zero-Dependency Obsidian-Dark Studio UI
│   ├── index.html                       # Studio editor, live canvas, keys pool & settings panels
│   ├── styles.css                       # Glassmorphism, CSS grid, 50/50 cards & responsive canvas
│   ├── app.js                           # State controller, live stage sync, dragging & task polling
│   └── docs.html                        # Comprehensive operator manual (Flowcharts, shortcuts & FAQs)
│
└── data/                                # Local studio runtime directories
    ├── api_keys.json                    # Local encrypted API key storage
    ├── settings.json                    # Hardware, audio & render preferences
    ├── avatars/                         # Host PNG cutout library (includes default_avatar.png)
    ├── bgm/                             # Ambient background music library
    ├── downloads/                       # Sliced stream cache
    ├── temp/                            # Transcoding scratchpad & ASS subtitles
    ├── outputs/                         # Finished 1080p 60fps MP4 master videos
    └── logs/                            # Real-time system & error logs (error.log)
```

---

## ⚙️ Installation & Usage

### 1. Prerequisites
- **Operating System**: Windows 10 or 11 (64-bit).
- **Python**: Python 3.10+ installed and added to system PATH (for developer source runs).
- **Hardware Acceleration (Recommended)**: NVIDIA GPU with NVENC, AMD GPU with AMF, or Intel QuickSync.

### 2. Launching the Studio (Development Mode)
Double-click `1_RUN_APP.bat` inside the project folder:
- Automatically verifies dependencies.
- Boots the FastAPI server on `http://127.0.0.1:8899`.
- Launches a sleek, hardware-accelerated native desktop window (WebView2).

### 3. Creating a 1-Click Windows Setup Installer
Double-click `BUILD_INSTALLER.bat` in the root folder:
- Packages the complete suite into a standalone Windows installer wizard: `dist/StreamMixStudio_Setup.exe`.
- Also creates a standalone portable archive: `dist/StreamMixStudio_Portable.zip`.
- Send `StreamMixStudio_Setup.exe` to anyone; they can double-click and install with 1 click without installing Python or Git! Creates Desktop and Start Menu shortcuts automatically.

### 4. Creating a Standalone Binary Folder
Double-click `BUILD_EXE.bat` in the root folder:
- Bundles Python, Uvicorn, FastAPI, FFmpeg, and frontend assets via PyInstaller into `dist/StreamMixStudio/`.

### 5. Step-by-Step Production Workflow
1. **Layer 1: Background Gameplay**: Provide a Twitch stream/VOD URL, YouTube URL, or click **Local File** to pick a gameplay video. Set cut duration (`No Cut`, `5m`, `10m`, `15m`, or `Custom`).
2. **Layer 2: Reaction Master Track**: Provide a YouTube video URL or local file. Set Gaussian blur, opacity (default 75%), video speed, voice pitch, and verify that the **Anti-Content-ID Protection Shield** is active.
3. **Layer 3: Host Avatar Cutout**: Toggle avatar on/off, upload cutout PNG, choose outer glow (*Cyan, White, Gold, None*), and adjust slow-motion sway or audio bounce.
4. **Layer 4: Dynamic Subtitles**: Pick from the 18 viral CapCut styles, choose a font family, or enable a custom rounded backdrop box.
5. **Stage Canvas Scrubber**: Drag and reposition avatar or subtitles directly on the 16:9 canvas. Click "Reset Position" if you wish to restore safe lower-third alignments.
6. **⚡ 30s Quick Slice Test**: Click to verify your render in 4 seconds.
7. **Start 1080p Master Render**: Click the master export button. Once complete, Windows Explorer will automatically highlight your finished MP4!

---

## 🔮 Roadmap & Future Horizons (v2.3+)

- **Multi-Source Layer 1 Backgrounds**:
  - **B-Roll Local Folder Mode**: Auto-stitch and randomize clips from a user-specified folder.
  - **Stock Video API Integration**: Connect to Pexels, Pixabay, and Mixkit APIs to auto-fetch dynamic gameplay/ambient background clips.
- **Enhanced Caption Typography Controls**:
  - Dedicated Bold (`<b>`) and Italic (`<i>`) toggles.
  - Custom Primary Text Color Picker & Multi-color gradient word highlights.
  - Fine-grained Stroke/Outline thickness (0–10px) and Drop Shadow X/Y offset sliders.
- **Vertical 9:16 Auto-Stack Mode**:
  - 1-Click re-frame export for YouTube Shorts, TikTok, and Instagram Reels (Reaction video on top, Subtitles in center, Gameplay at bottom).
- **AI Silence & Dead-Air Remover**:
  - Automatically detect and jump-cut silent pauses (> 1.2s) in reaction audio for ultra-high audience retention.

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
