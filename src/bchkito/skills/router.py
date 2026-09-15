from __future__ import annotations

import re
from enum import Enum


class Intent(str, Enum):
    CHAT = "chat"
    WEATHER = "weather"
    NEWS = "news"
    MORNING = "morning"
    WHATSAPP_SEND = "whatsapp_send"
    CONFIRM = "confirm"
    CANCEL = "cancel"


_WEATHER = re.compile(
    r"(الجو|الطقس|شتا|برد|سخون|شحال\s*ف|درجة|مطر|رياح|غيم)",
    re.IGNORECASE,
)
_NEWS = re.compile(r"(الأخبار|الاخبار|شنو\s*جديد|عنوان|الجريدة)", re.IGNORECASE)
_MORNING = re.compile(r"(صباح\s*الخير|صباح\s*النور|فطور|اليوم\s*كيفاش)", re.IGNORECASE)
_WHATSAPP = re.compile(
    r"(واتساب|whatsapp|صيفط|صفت|رسالة|كلم|قولي\s*ل|قول\s*ل|بنتي|ابنتي)",
    re.IGNORECASE,
)
_CONFIRM = re.compile(r"^(نعم|اه|آه|أيه|اييه|واخا|واخا|موافق|صيفط|صفت|ok|yes)\b", re.IGNORECASE)
_CANCEL = re.compile(r"^(لا|ماشي|بطلو|الغي|cancel|no)\b", re.IGNORECASE)


class SkillRouter:
    def route(self, text: str, *, pending_whatsapp: bool = False) -> Intent:
        cleaned = (text or "").strip()
        if not cleaned:
            return Intent.CHAT

        if pending_whatsapp:
            if _CANCEL.search(cleaned) or "ما تصيفط" in cleaned or "ماصيفط" in cleaned:
                return Intent.CANCEL
            if _CONFIRM.search(cleaned) or cleaned in {"نعم", "واخا", "أيه", "اه", "اييه"}:
                return Intent.CONFIRM
            # Escape hatch: clear intent switch if they clearly ask something else
            if _MORNING.search(cleaned):
                return Intent.MORNING
            if _WEATHER.search(cleaned):
                return Intent.WEATHER
            if _NEWS.search(cleaned):
                return Intent.NEWS
            # Otherwise treat as message correction / new draft
            return Intent.WHATSAPP_SEND

        if _MORNING.search(cleaned):
            return Intent.MORNING
        if _WHATSAPP.search(cleaned):
            return Intent.WHATSAPP_SEND
        if _WEATHER.search(cleaned):
            return Intent.WEATHER
        if _NEWS.search(cleaned):
            return Intent.NEWS
        return Intent.CHAT
