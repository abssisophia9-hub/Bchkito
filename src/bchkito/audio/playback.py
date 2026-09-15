from __future__ import annotations

import logging
import wave
from pathlib import Path

import numpy as np

from bchkito.config import Settings

logger = logging.getLogger(__name__)


def _import_sounddevice():
    try:
        import sounddevice as sd

        return sd
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("sounddevice is required for playback") from exc


def play_array(audio: np.ndarray, sample_rate: int) -> None:
    if audio.size == 0:
        return
    sd = _import_sounddevice()
    data = audio.astype(np.float32)
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    if peak > 1.0:
        data = data / peak
    logger.info("Playing %.2fs of audio", len(data) / sample_rate)
    sd.play(data, sample_rate)
    sd.wait()


def play_wav(path: Path) -> None:
    with wave.open(str(path), "rb") as wf:
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        width = wf.getsampwidth()
        channels = wf.getnchannels()

    if width == 2:
        pcm = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    elif width == 4:
        pcm = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        pcm = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
        pcm = (pcm - 128.0) / 128.0

    if channels > 1:
        pcm = pcm.reshape(-1, channels).mean(axis=1)
    play_array(pcm, rate)


def write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(audio, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return path


def play_earcon(settings: Settings, kind: str = "thinking") -> None:
    """Short beep so seniors know the robot is working."""
    sr = settings.sample_rate
    duration = 0.12
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    freq = 660.0 if kind == "thinking" else 880.0
    tone = 0.2 * np.sin(2 * np.pi * freq * t).astype(np.float32)
    try:
        play_array(tone, sr)
    except Exception:  # pragma: no cover
        logger.debug("Earcon playback skipped", exc_info=True)
