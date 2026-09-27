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

---

## 🗂️ Project File Structure

```
twitchyoutube/
├── 1_RUN_APP.bat                        # One-click Windows desktop runner
├── desktop_launcher.py                  # Borderless native MS Edge app mode launcher & port cleaner
├── requirements.txt                     # Python backend dependencies
├── README.md                            # Studio overview & documentation
├── api.md                               # REST API endpoints & payload specifications
├── v2 UI TWITCH_YOUTUBE_REMIX_ENGINE_MASTER_BLUEPRINT.md # Master architectural blueprint & roadmap
│
├── bin/                                 # Portable standalone multimedia binaries
│   ├── ffmpeg.exe                       # High-speed GPU-enabled FFmpeg executable
│   └── ffprobe.exe                      # Media stream & codec inspector
│
├── backend/                             # Modular Python Backend Engine
│   ├── __init__.py                      # Package initializer
│   ├── config.py                        # Path resolver, GPU encoder detection & error logging
│   ├── api_pool.py                      # Groq API pool manager with latency tests & auto-failover
│   ├── downloader.py                    # yt-dlp parallel slicer (anti-bot bypass) & media prober
│   ├── audio_engine.py                  # Pitch/tempo sync & anti-copyright acoustic filter chains
│   ├── subtitle_generator.py            # Word-level Groq Whisper transcriber & 18 ASS subtitle styles
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
    ├── avatars/                         # Host PNG cutout library
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
- **Python**: Python 3.10+ installed and added to system PATH.
- **Hardware Acceleration (Recommended)**: NVIDIA GPU with NVENC, AMD GPU with AMF, or Intel QuickSync.

### 2. Launching the Studio
Double-click `1_RUN_APP.bat` inside the project folder:
- Automatically resolves dependencies.
- Boots the FastAPI server on `http://localhost:8000`.
- Launches a sleek, borderless native desktop window.

### 3. Step-by-Step Production Workflow
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
