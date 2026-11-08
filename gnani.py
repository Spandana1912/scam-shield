"""Thin clients for Gnani Prisma (STT) and Timbre (TTS), based on the Gnani quick start docs."""
import mimetypes
import os

import requests

import config


class GnaniError(Exception):
    pass


def _headers():
    if not config.GNANI_API_KEY:
        raise GnaniError("GNANI_API_KEY is not set (see .env.example)")
    return {"X-API-Key-ID": config.GNANI_API_KEY}


def transcribe(audio_path: str) -> dict:
    """Prisma REST STT. Audio must be 30 seconds or less. Returns the JSON response
    (keys include 'transcript' and, for Prisma v3.0, 'detected_language_code')."""
    mime = mimetypes.guess_type(audio_path)[0] or "audio/wav"
    data = {"language_code": config.STT_LANGUAGE}
    if config.STT_MODEL:
        data["model"] = config.STT_MODEL
    with open(audio_path, "rb") as f:
        r = requests.post(
            f"{config.GNANI_BASE_URL}/stt/v3",
            headers=_headers(),
            files={"audio_file": (os.path.basename(audio_path), f, mime)},
            data=data,
            timeout=60,
        )
    if r.status_code != 200:
        raise GnaniError(f"STT failed ({r.status_code}): {r.text[:300]}")
    j = r.json()
    if not j.get("success"):
        raise GnaniError(f"STT error: {j}")
    return j


def synthesize(text: str, out_path: str, voice: str = None, language: str = None) -> str:
    """Timbre REST TTS. Writes a WAV file and returns its path."""
    body = {
        "text": text,
        "voice": voice or config.TTS_VOICE,
        "model": config.TTS_MODEL,
        "language": language or config.TTS_LANGUAGE,
        "speed": 1.0,
        "audio_config": {
            "sample_rate": 48000,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "wav",
        },
    }
    r = requests.post(
        f"{config.GNANI_BASE_URL}/api/v1/tts/inference",
        headers={**_headers(), "Content-Type": "application/json"},
        json=body,
        timeout=60,
    )
    if r.status_code != 200:
        raise GnaniError(f"TTS failed ({r.status_code}): {r.text[:300]}")
    with open(out_path, "wb") as f:
        f.write(r.content)
    return out_path
