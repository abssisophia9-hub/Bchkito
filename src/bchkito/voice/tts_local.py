from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path

import numpy as np

from bchkito.audio.playback import write_wav
from bchkito.config import Settings

logger = logging.getLogger(__name__)


class LocalTTS:
    """Piper primary, eSpeak-ng fallback, synthetic beep last resort."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def synthesize(self, text: str, out_path: Path | None = None) -> Path:
        out_path = out_path or Path(tempfile.gettempdir()) / "bchkito_tts.wav"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if await self._try_piper(text, out_path):
            return out_path
        if await self._try_espeak(text, out_path):
            return out_path

        logger.warning("No local TTS engine found; writing silent placeholder")
        silence = np.zeros(int(self.settings.sample_rate * 0.4), dtype=np.float32)
        write_wav(out_path, silence, self.settings.sample_rate)
        return out_path

    async def _try_piper(self, text: str, out_path: Path) -> bool:
        binary = shutil.which(self.settings.piper_binary)
        model = self.settings.piper_model_path
        if not binary or not model.exists():
            return False
        cmd = [
            binary,
            "--model",
            str(model),
            "--output_file",
            str(out_path),
            "--speaker",
            str(self.settings.piper_speaker),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, stderr = await proc.communicate(text.encode("utf-8"))
        if proc.returncode != 0:
            logger.warning("Piper failed: %s", stderr.decode(errors="ignore"))
            return False
        logger.info("TTS via Piper -> %s", out_path)
        return True

    async def _try_espeak(self, text: str, out_path: Path) -> bool:
        binary = shutil.which("espeak-ng") or shutil.which("espeak")
        if not binary:
            return False
        cmd = [
            binary,
            "-v",
            self.settings.espeak_voice,
            "-w",
            str(out_path),
            text,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning("eSpeak failed: %s", stderr.decode(errors="ignore"))
            return False
        logger.info("TTS via eSpeak -> %s", out_path)
        return True
