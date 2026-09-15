from __future__ import annotations

import logging
from typing import Callable

import numpy as np

from bchkito.config import Settings

logger = logging.getLogger(__name__)


def _import_sounddevice():
    try:
        import sounddevice as sd

        return sd
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "sounddevice is required for microphone capture. "
            "Install project deps and ensure PortAudio is available."
        ) from exc


def record_until(
    should_continue: Callable[[], bool],
    settings: Settings,
    max_seconds: float = 30.0,
) -> np.ndarray:
    """Record mono float32 PCM while should_continue() is True."""
    sd = _import_sounddevice()
    sample_rate = settings.sample_rate
    frames: list[np.ndarray] = []
    chunk = int(sample_rate * 0.1)
    max_chunks = int(max_seconds / 0.1)

    logger.info("Recording (sample_rate=%s)...", sample_rate)
    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        blocksize=chunk,
    ) as stream:
        for _ in range(max_chunks):
            if not should_continue():
                break
            data, _overflowed = stream.read(chunk)
            frames.append(data.copy())

    if not frames:
        return np.zeros(0, dtype=np.float32)
    audio = np.concatenate(frames, axis=0).reshape(-1)
    logger.info("Recorded %.2fs of audio", len(audio) / sample_rate)
    return audio


def record_seconds(seconds: float, settings: Settings) -> np.ndarray:
    sd = _import_sounddevice()
    frames = int(seconds * settings.sample_rate)
    logger.info("Recording fixed %.1fs...", seconds)
    audio = sd.rec(
        frames,
        samplerate=settings.sample_rate,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    return audio.reshape(-1)
