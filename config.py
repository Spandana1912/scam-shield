"""Settings, read from environment variables or a local .env file."""
import os
from pathlib import Path


def _load_env():
    p = Path(__file__).parent / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()

# Gnani (Prisma speech-to-text, Timbre text-to-speech)
GNANI_API_KEY = os.getenv("GNANI_API_KEY", "")
GNANI_BASE_URL = os.getenv("GNANI_BASE_URL", "https://api.vachana.ai")
STT_MODEL = os.getenv("STT_MODEL", "prisma-v3.0")
STT_LANGUAGE = os.getenv("STT_LANGUAGE", "indic-auto")  # or e.g. hi-IN
TTS_MODEL = os.getenv("TTS_MODEL", "timbre-v2.5")
TTS_VOICE = os.getenv("TTS_VOICE", "Nalini")  # check the Voice Catalog for your language
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "hi-IN")

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# Optional LLM for deeper scam analysis (any OpenAI-compatible endpoint, e.g. a hosted Evon).
# Leave empty to use the built-in rule engine only.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").rstrip("/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")

# Privacy: by default transcripts are NOT saved, only scores and tactics.
STORE_TRANSCRIPTS = os.getenv("STORE_TRANSCRIPTS", "0") == "1"

DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent / "scamshield.db"))
