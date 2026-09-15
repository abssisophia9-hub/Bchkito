from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


def trim_silence(
    audio: np.ndarray,
    sample_rate: int,
    threshold: float = 0.015,
    pad_ms: int = 200,
) -> np.ndarray:
    """Energy-based VAD trim (no heavy deps). Keeps padding around speech."""
    if audio.size == 0:
        return audio

    frame = max(1, int(sample_rate * 0.02))
    energies = []
    for i in range(0, len(audio), frame):
        chunk = audio[i : i + frame]
        energies.append(float(np.sqrt(np.mean(chunk**2) + 1e-12)))

    speech = [e > threshold for e in energies]
    if not any(speech):
        logger.warning("VAD: no speech detected; returning original audio")
        return audio

    first = speech.index(True)
    last = len(speech) - 1 - speech[::-1].index(True)
    pad = int((pad_ms / 1000.0) * sample_rate)
    start = max(0, first * frame - pad)
    end = min(len(audio), (last + 1) * frame + pad)
    trimmed = audio[start:end]
    logger.debug("VAD trimmed %s -> %s samples", len(audio), len(trimmed))
    return trimmed
