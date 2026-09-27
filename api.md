# 🔑 API Keys & Services Configuration Guide

This file provides reference information for configuring API keys in the **Settings / API Keys** panel of the video engine or via `data/api_keys.json`.

---

## 1. 🎙️ Groq Whisper API (Speech-to-Text & Word Timestamps)
Used by `backend/subtitle_generator.py` for ultra-fast audio transcription with word-by-word micro timestamps.

* **Format**: `gsk_...`
* **Get Free Key**: https://console.groq.com/keys
* **Endpoint**: `https://api.groq.com/openai/v1/audio/transcriptions`
* **Model**: `whisper-large-v3`

---

## 2. 📽️ Stock Footage & Image APIs (Optional)

* **Pexels API**: https://www.pexels.com/api/
* **Pixabay API**: https://pixabay.com/api/docs/
* **Google Gemini API**: https://aistudio.google.com/app/apikey

---

## 📋 JSON Format (For Direct `data/api_keys.json` Setup)

To configure your API keys locally without using the UI, populate `data/api_keys.json`:

```json
{
  "active_key_index": 0,
  "keys": [
    {
      "id": "key_01",
      "label": "Groq Key 1 (Primary)",
      "key": "YOUR_GROQ_API_KEY_HERE",
      "status": "HEALTHY",
      "latency_ms": 0,
      "total_transcriptions": 0,
      "last_used": null
    }
  ]
}
```
