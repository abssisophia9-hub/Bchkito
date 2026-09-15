from __future__ import annotations

import logging
from typing import Any

import httpx

from bchkito.config import Settings

logger = logging.getLogger(__name__)


class LocalLLM:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.4,
    ) -> str:
        url = f"{self.settings.ollama_host.rstrip('/')}/api/chat"
        payload: dict[str, Any] = {
            "model": self.settings.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.llm_timeout_seconds
            ) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                text = data.get("message", {}).get("content", "").strip()
                logger.info("Local LLM reply: %s", text[:120])
                return text
        except Exception as exc:
            logger.warning("Local LLM failed: %s", exc)
            return ""
