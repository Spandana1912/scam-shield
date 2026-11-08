"""Audio helpers. Needs ffmpeg for best results (Telegram voice notes are OGG/Opus,
and Prisma REST accepts 30 seconds per request)."""
import shutil
import subprocess
from pathlib import Path


def have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def to_wav_chunks(src: str, workdir: str, seg_seconds: int = 25) -> list:
    """Convert to 16 kHz mono WAV and split into chunks under Prisma's 30 s limit."""
    if not have_ffmpeg():
        return [src]
    pattern = str(Path(workdir) / "chunk_%03d.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", "16000", "-ac", "1",
         "-f", "segment", "-segment_time", str(seg_seconds), "-reset_timestamps", "1", pattern],
        check=True,
    )
    return sorted(str(p) for p in Path(workdir).glob("chunk_*.wav"))


def wav_to_ogg(wav: str, ogg: str) -> str:
    """Telegram voice messages must be OGG/Opus."""
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libopus", "-b:a", "32k", ogg],
        check=True,
    )
    return ogg
