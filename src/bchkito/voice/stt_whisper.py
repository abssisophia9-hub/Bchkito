from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from bchkito.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class Transcript:
    text: str
    language: str | None = None
    avg_logprob: float | None = None
    no_speech_prob: float | None = None

    @property
    def low_confidence(self) -> bool:
        if self.avg_logprob is not None and self.avg_logprob < -1.0:
            return True
        if self.no_speech_prob is not None and self.no_speech_prob > 0.6:
            return True
        return len(self.text.strip()) < 2


class WhisperSTT:
    """Local faster-whisper STT with a mock fallback for development."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model = None
        self._mock = False

    def _load(self) -> None:
        if self._model is not None or self._mock:
            return
        try:
            from faster_whisper import WhisperModel

            logger.info(
                "Loading Whisper model=%s device=%s compute=%s",
                self.settings.whisper_model,
                self.settings.whisper_device,
                self.settings.whisper_compute_type,
            )
            self._model = WhisperModel(
                self.settings.whisper_model,
                device=self.settings.whisper_device,
                compute_type=self.settings.whisper_compute_type,
            )
        except Exception as exc:
            logger.warning(
                "faster-whisper unavailable (%s); using mock STT", exc
            )
            self._mock = True

    def transcribe(self, audio: np.ndarray) -> Transcript:
        self._load()
        if self._mock or audio.size == 0:
            text = "" if audio.size == 0 else "مرحبا بشكيتو"
            return Transcript(text=text, language="ar", avg_logprob=-0.2)

        assert self._model is not None
        segments, info = self._model.transcribe(
            audio,
            language=self.settings.whisper_language,
            initial_prompt=self.settings.whisper_initial_prompt,
            vad_filter=False,
            beam_size=1,
        )
        parts: list[str] = []
        logprobs: list[float] = []
        no_speech: list[float] = []
        for seg in segments:
            parts.append(seg.text.strip())
            if seg.avg_logprob is not None:
                logprobs.append(float(seg.avg_logprob))
            if seg.no_speech_prob is not None:
                no_speech.append(float(seg.no_speech_prob))

        text = " ".join(p for p in parts if p).strip()
        logger.info("STT: %s", text)
        return Transcript(
            text=text,
            language=getattr(info, "language", self.settings.whisper_language),
            avg_logprob=(sum(logprobs) / len(logprobs)) if logprobs else None,
            no_speech_prob=(sum(no_speech) / len(no_speech)) if no_speech else None,
        )
