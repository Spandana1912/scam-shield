# Scam Shield (Gnani AI Internship Challenge)

Telegram bot built on Gnani **Prisma** (speech to text) and **Timbre** (text to speech).

- Send a voice note or paste text: transcript, scam score, tactics, and a spoken Hindi verdict.
- High risk: trusted contacts are alerted automatically (`/trust`, `/join CODE`).
- `/simulate`: "survive the scam call" training game with a clearly labelled AI bot.
- `/report` and `/check`: community scam-number list.

## Setup (Windows)

1. Install Python 3.10+ from python.org (tick "Add to PATH").
2. Install ffmpeg: open PowerShell and run `winget install Gyan.FFmpeg`, then reopen the terminal.
   (Needed to convert Telegram voice notes and to send voice replies.)
3. In this folder: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`. Fill in `GNANI_API_KEY` (from app.gnani.ai) and `TELEGRAM_TOKEN`
   (message @BotFather on Telegram, send `/newbot`).
5. Check the logic offline: `python test_offline.py`
6. Run the bot: `python bot.py`, then message your bot on Telegram.

## Notes

- Default language is Hindi/Hinglish (`indic-auto` for Prisma, `hi-IN` for Timbre). To change the
  reply voice or language, set `TTS_VOICE` and `TTS_LANGUAGE` using the Voice Catalog in the Gnani docs.
- Optional LLM step: set `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (any OpenAI-compatible endpoint,
  such as a hosted Evon). Without it the built-in rule engine is used.
- Transcripts are not stored unless `STORE_TRANSCRIPTS=1`.
- Never share your `.env` file or post your API keys.
