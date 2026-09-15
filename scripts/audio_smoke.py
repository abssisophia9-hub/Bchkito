#!/usr/bin/env python3
"""Audio I/O smoke test: record 2s and play back (requires mic/speaker)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bchkito.audio.capture import record_seconds
from bchkito.audio.playback import play_array, write_wav
from bchkito.audio.vad import trim_silence
from bchkito.config import get_settings


def main() -> int:
    settings = get_settings()
    print(f"Recording 2s @ {settings.sample_rate} Hz...")
    audio = record_seconds(2.0, settings)
    trimmed = trim_silence(audio, settings.sample_rate)
    out = Path("data/cache/audio_smoke.wav")
    write_wav(out, trimmed, settings.sample_rate)
    print(f"Wrote {out} ({len(trimmed)} samples). Playing back...")
    play_array(trimmed, settings.sample_rate)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
