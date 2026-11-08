# 🛡️ Scam Shield

A Telegram bot that listens to a suspicious voice note (or message), tells you whether it looks like a scam, explains the tactics, and **speaks the warning back in Hindi**. Built for the **Great Indian AI Internship Challenge** with Gnani AI's speech models.

`#GnaniAI` `#GreatIndianAIInternshipChallenge`

**Demo video:** [Watch on X](https://x.com/PaboluSpan99921/status/2119379207872827557)
**One-page pitch:** [PITCH.md](PITCH.md) ([PDF](PITCH.pdf))

## Why

Fake "police", "KYC" and courier calls that demand money or OTPs target families across India, especially parents and grandparents. Scam Shield gives a quick second opinion in their own language, by voice.

## Gnani models used

| Step | Model |
|---|---|
| Voice note to text | **Gnani Prisma** (speech to text), REST `POST /stt/v3` |
| Spoken verdict | **Gnani Timbre** (text to speech), REST `POST /api/v1/tts/inference` |

Both are called from `gnani.py`.

## Features

- **Scam check:** send a voice note or text. You get the transcript, a risk score (0 to 100), the tactics spotted (fake authority, arrest threats, urgency, secrecy, payment demands, OTP/KYC requests, prize bait), and a Hindi voice reply.
- **Family alert:** `/trust` creates a code, a family member sends `/join CODE`, and they are alerted automatically if a check scores high.
- **Training game:** `/simulate` runs a scripted "digital arrest" or fake-KYC call, clearly labelled as an AI training bot. You reply by voice or text and get a score.
- **Scam number list:** `/report NUMBER` and `/check NUMBER` keep a small community list.
- **Privacy:** transcripts are not stored unless you set `STORE_TRANSCRIPTS=1`.

## How it works

```
Telegram voice note -> ffmpeg (16 kHz WAV, 25 s chunks) -> Prisma (transcript)
        -> analyzer.py (rules, optional LLM) -> score + tactics
        -> Timbre (Hindi voice) -> Telegram reply (+ alert to trusted contacts)
```

The scam analysis uses a keyword rule engine in Hindi and English, so it runs without a GPU. Optionally, set `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL` (any OpenAI-compatible endpoint) and the LLM's verdict is combined with the rules, using the higher risk score.

## Setup

1. Install Python 3.10+ and ffmpeg (Windows: `winget install Gyan.FFmpeg`).
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your Gnani API key (from app.gnani.ai) and a Telegram bot token (from @BotFather).
4. Check the logic offline: `python test_offline.py`
5. Run: `python bot.py`, then message your bot on Telegram.

**Never commit your `.env` file.** It is listed in `.gitignore`.

## Files

| File | Purpose |
|---|---|
| `bot.py` | Telegram bot: commands, voice handling, alerts |
| `gnani.py` | Prisma and Timbre API clients |
| `analyzer.py` | Scam tactics, scoring, optional LLM |
| `simulator.py` | "Survive the scam call" game |
| `audio.py` | ffmpeg helpers |
| `db.py` | SQLite storage |
| `config.py` | Settings from `.env` |
| `test_offline.py` | Offline tests for the analyzer, game and database |

## Limitations

- The analysis is rule-based, so it can miss scams phrased in unusual ways or flag harmless messages. Treat the result as a guide, not proof. If in doubt, hang up and call your bank or 1930 (cyber crime helpline).
- Voice quality matters: very quiet or noisy recordings may be transcribed wrongly.
- The bot only runs while `bot.py` is running on the host machine.
- The demo's scam voice note is a scripted, AI-generated sample, not a real call.

## License

MIT, see `LICENSE`.
