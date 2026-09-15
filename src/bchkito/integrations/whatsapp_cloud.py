from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

import httpx

from bchkito.config import Settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(
            self.settings.whatsapp_token
            and self.settings.whatsapp_phone_number_id
        )

    @property
    def _base(self) -> str:
        return (
            f"https://graph.facebook.com/{self.settings.whatsapp_api_version}/"
            f"{self.settings.whatsapp_phone_number_id}"
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.whatsapp_token}",
            "Content-Type": "application/json",
        }

    async def send_text(self, to_e164: str, body: str) -> dict:
        to = to_e164.replace(" ", "").replace("-", "")
        payload = {
            "messaging_product": "whatsapp",
            "to": to.lstrip("+"),
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base}/messages",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("WhatsApp text sent: %s", data)
            return data

    async def upload_media(self, path: Path) -> str:
        mime, _ = mimetypes.guess_type(str(path))
        mime = mime or "audio/ogg"
        headers = {
            "Authorization": f"Bearer {self.settings.whatsapp_token}",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            with path.open("rb") as fh:
                files = {
                    "file": (path.name, fh, mime),
                    "messaging_product": (None, "whatsapp"),
                    "type": (None, mime),
                }
                resp = await client.post(
                    f"{self._base}/media",
                    headers=headers,
                    files=files,
                )
            resp.raise_for_status()
            media_id = resp.json()["id"]
            logger.info("WhatsApp media uploaded id=%s", media_id)
            return media_id

    async def send_audio(self, to_e164: str, path: Path) -> dict:
        media_id = await self.upload_media(path)
        to = to_e164.replace(" ", "").replace("-", "")
        payload = {
            "messaging_product": "whatsapp",
            "to": to.lstrip("+"),
            "type": "audio",
            "audio": {"id": media_id},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base}/messages",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("WhatsApp audio sent: %s", data)
            return data
