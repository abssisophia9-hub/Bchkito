from __future__ import annotations

import logging
import re
from pathlib import Path

from bchkito.config import Settings
from bchkito.integrations.whatsapp_cloud import WhatsAppClient
from bchkito.prompts_loader import load_prompt
from bchkito.voice.llm_cloud import CloudLLM
from bchkito.voice.llm_local import LocalLLM
from bchkito.voice.tts_cloud import CloudTTS
from bchkito.voice.tts_local import LocalTTS

logger = logging.getLogger(__name__)

_STRIP_PREFIX = re.compile(
    r"^(صيفط|صفت|قولي|قول|رسالة|واتساب|whatsapp)\s*"
    r"(ل|على)?\s*(بنتي|ابنتي|بنتيَ)?\s*[:：\-]?\s*",
    re.IGNORECASE,
)


class FamilyBridgeSkill:
    def __init__(
        self,
        settings: Settings,
        local_llm: LocalLLM,
        cloud_llm: CloudLLM,
        tts_cloud: CloudTTS,
        tts_local: LocalTTS,
    ) -> None:
        self.settings = settings
        self.local_llm = local_llm
        self.cloud_llm = cloud_llm
        self.tts_cloud = tts_cloud
        self.tts_local = tts_local
        self.whatsapp = WhatsAppClient(settings)
        self.skill_prompt = load_prompt("skills", "whatsapp.md")

    def extract_message(self, text: str) -> str:
        cleaned = _STRIP_PREFIX.sub("", text.strip()).strip()
        return cleaned or text.strip()

    async def _normalize(self, draft: str) -> tuple[str, bool]:
        messages = [
            {"role": "system", "content": self.skill_prompt},
            {
                "role": "user",
                "content": (
                    "نظّف النص للإرسال على واتساب دون تغيير المعنى. "
                    "أرجع النص فقط:\n" + draft
                ),
            },
        ]
        used_cloud = False
        text = ""
        if self.cloud_llm.available:
            text = await self.cloud_llm.chat(messages, temperature=0.1)
            used_cloud = bool(text)
        if not text:
            text = await self.local_llm.chat(messages, temperature=0.1)
        return (text.strip() or draft), used_cloud

    async def send_pending(self, draft: str) -> tuple[str, bool]:
        if not self.settings.daughter_wa_phone:
            return "ماكاينش رقم البنت فالإعدادات.", False
        if not self.whatsapp.configured:
            return "واتساب مازال ما مفعّلش فالإعدادات.", False

        normalized, used_cloud = await self._normalize(draft)
        mode = self.settings.whatsapp_default_mode

        try:
            if mode == "voice":
                audio = await self.tts_cloud.synthesize(
                    normalized, tier="elevenlabs"
                )
                if audio is None:
                    audio = await self.tts_local.synthesize(normalized)
                await self.whatsapp.send_audio(
                    self.settings.daughter_wa_phone, Path(audio)
                )
            else:
                await self.whatsapp.send_text(
                    self.settings.daughter_wa_phone, normalized
                )
        except Exception as exc:
            logger.exception("WhatsApp send failed")
            return f"ما قدرتش نصيفط الرسالة: {exc}", used_cloud

        return f"تمام، تصيفطات الرسالة لـ {self.settings.daughter_name}.", used_cloud
