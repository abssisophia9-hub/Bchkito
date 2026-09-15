from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import httpx

from bchkito.config import Settings

logger = logging.getLogger(__name__)


class CloudTTS:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def synthesize(
        self,
        text: str,
        *,
        tier: str = "azure",
        out_path: Path | None = None,
    ) -> Path | None:
        out_path = out_path or Path(tempfile.gettempdir()) / "bchkito_cloud_tts.wav"
        if tier == "elevenlabs":
            return await self._elevenlabs(text, out_path)
        return await self._azure(text, out_path)

    async def _azure(self, text: str, out_path: Path) -> Path | None:
        key = self.settings.azure_speech_key
        region = self.settings.azure_speech_region
        if not key:
            logger.warning("Azure Speech key missing")
            return None
        url = (
            f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        )
        ssml = (
            "<speak version='1.0' xml:lang='ar-MA'>"
            f"<voice name='{self.settings.azure_speech_voice}'>{_xml_escape(text)}</voice>"
            "</speak>"
        )
        headers = {
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, content=ssml.encode("utf-8"), headers=headers)
                resp.raise_for_status()
                out_path.write_bytes(resp.content)
                logger.info("TTS via Azure -> %s", out_path)
                return out_path
        except Exception as exc:
            logger.warning("Azure TTS failed: %s", exc)
            return None

    async def _elevenlabs(self, text: str, out_path: Path) -> Path | None:
        key = self.settings.elevenlabs_api_key
        voice = self.settings.elevenlabs_voice_id
        if not key or not voice:
            logger.warning("ElevenLabs credentials missing")
            return None
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
        headers = {
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
        }
        # Store as mp3; WhatsApp path can convert or upload as audio
        mp3_path = out_path.with_suffix(".mp3")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                mp3_path.write_bytes(resp.content)
                logger.info("TTS via ElevenLabs -> %s", mp3_path)
                return mp3_path
        except Exception as exc:
            logger.warning("ElevenLabs TTS failed: %s", exc)
            return None


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
