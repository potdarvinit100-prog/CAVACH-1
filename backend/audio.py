"""VoiceShield — upload validation + metadata + context assessment.

What this module does NOT do, by design:
- It does not claim synthetic-audio / voice-clone detection. No verified
  audio model is configured, so audio_authenticity is always
  "unavailable" with the reason stated. Any future model must be added
  here with its format limits and test results, not as a score in the UI.
- It never stores or transcribes audio by default. The caller supplies a
  call note (their own words) for context assessment; the file itself is
  validated for type/size and, for WAV, duration/channels/rate via stdlib.
"""
from __future__ import annotations

import wave
from pathlib import Path

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg"}
ALLOWED_MIME_PREFIXES = ("audio/",)
MAX_BYTES = 25 * 1024 * 1024
MAGIC = {b"RIFF": ".wav", b"ID3": ".mp3", b"\xff\xfb": ".mp3", b"OggS": ".ogg"}


def validate_audio(path: str) -> dict:
    p = Path(path)
    errors = []
    if not p.exists():
        errors.append("File does not exist.")
        return {"valid": False, "errors": errors}
    ext = p.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        errors.append(f"Extension {ext} is not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}.")
    size = p.stat().st_size
    if size > MAX_BYTES:
        errors.append(f"File is {size} bytes; maximum is {MAX_BYTES} bytes.")
    head = p.read_bytes()[:12] if size >= 4 else b""
    magic_ext = None
    for prefix, e in MAGIC.items():
        if head.startswith(prefix):
            magic_ext = e
            break
    if magic_ext and magic_ext != ext and not (ext == ".mp3" and magic_ext == ".mp3"):
        errors.append(f"File header suggests {magic_ext} but extension is {ext}; refusing to trust the extension.")
    info: dict = {"name": p.name, "extension": ext, "size_bytes": size,
                  "duration_seconds": None, "channels": None, "sample_rate": None}
    if ext == ".wav" and not errors:
        try:
            with wave.open(str(p), "rb") as w:
                info["channels"] = w.getnchannels()
                info["sample_rate"] = w.getframerate()
                info["duration_seconds"] = round(w.getnframes() / w.getframerate(), 2)
        except Exception as e:
            errors.append(f"WAV could not be parsed: {e}")
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "metadata": info,
        "audio_authenticity": {
            "status": "unavailable",
            "reason": "No verified synthetic-audio model is configured. Context flags from the call note are not audio-forensic proof; verify by callback on a trusted number.",
        },
    }
