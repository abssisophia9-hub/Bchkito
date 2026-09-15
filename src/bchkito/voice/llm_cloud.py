from __future__ import annotations

import logging
from typing import Any

import httpx

from bchkito.config import Settings

logger = logging.getLogger(__name__)


class CloudLLM:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def available(self) -> bool:
        return self.settings.cloud_llm_configured

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
    ) -> str:
        if not self.available:
            return ""

        provider = self.settings.cloud_llm_provider
        if provider == "groq":
            return await self._openai_compatible(
                base_url="https://api.groq.com/openai/v1",
                api_key=self.settings.groq_api_key,
                model=self.settings.groq_model,
                messages=messages,
                temperature=temperature,
            )
        if provider == "together":
            return await self._openai_compatible(
                base_url="https://api.together.xyz/v1",
                api_key=self.settings.together_api_key,
                model=self.settings.together_model,
                messages=messages,
                temperature=temperature,
            )
        return ""

    async def _openai_compatible(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
    ) -> str:
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.llm_timeout_seconds
            ) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                text = (
                    data["choices"][0]["message"]["content"].strip()
                    if data.get("choices")
                    else ""
                )
                logger.info("Cloud LLM (%s) reply: %s", model, text[:120])
                return text
        except Exception as exc:
            logger.warning("Cloud LLM failed: %s", exc)
            return ""
