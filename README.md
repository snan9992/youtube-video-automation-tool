# YouTube Automation Studio

A simple, easy-to-use app for creating automated YouTube videos with:
- AI-generated scripts
- Voiceover generation
- Auto-generated visual scenes
- Captions and lower thirds
- Optional YouTube upload

This repo is intended as a practical starter project for creators who want to automate Shorts, fact videos, documentary-style videos, and simple narrative content.

## Features

- Script generation using OpenAI (or a fallback script if no key is provided)
- Voiceover creation using ElevenLabs or gTTS
- Simple video generation from text scenes
- Captions built into the scenes
- YouTube upload support when credentials are configured

## Quick start

1. Clone the repo.
2. Create a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and fill in the keys you want to use:

```bash
cp .env.example .env
```

5. Run the app:

```bash
streamlit run app.py
```

## Recommended usage

- Topic: Use a strong hook like `Top 5 little-known facts about...`
- Tone: Try `Educational`, `News-style`, or `Storytelling`
- Style: Use `Shorts` for 30-60s clips or `Documentary` for longer text scenes
- Voice: `female`, `male`, or `neutral`

## Notes

- The included video generation is a starter workflow that creates fast visual scenes for script-based videos.
- For polished character animation or advanced motion graphics, you can connect this tool to Canva, CapCut templates, or a professional editing pipeline.
- For YouTube upload, configure your API credentials before enabling auto upload.

## Folder structure

- `app.py` — Streamlit UI entry point
- `services/ai_service.py` — script generation + voice generation
- `services/video_service.py` — scene generation and final render
- `services/youtube_service.py` — upload logic

## Future improvements

- Add real stock footage selection
- Add text-to-video AI integrations
- Add subtitle file export `.srt`
- Add script templates by niche
- Add scheduling and multi-video batch generation
