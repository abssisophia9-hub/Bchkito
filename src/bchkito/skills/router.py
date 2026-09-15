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
    MED_REMINDER = "med_reminder"
    MED_RESPONSE = "med_response"
    SOS = "sos"
    GAME = "game"
    GAME_ANSWER = "game_answer"
    GLUCOSE = "glucose"


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
_CONFIRM = re.compile(
    r"^(نعم|اه|آه|أيه|اييه|واخا|موافق|صيفط|صفت|ok|yes)\b", re.IGNORECASE
)
_CANCEL = re.compile(r"^(لا|ماشي|بطلو|الغي|cancel|no)\b", re.IGNORECASE)
_SOS = re.compile(
    r"(عيطي|عيّطي|نجدة|ساعدني|ما\s*بخير|طحت|سقطت|\bsos\b|مساعدة|بغيت\s*المساعدة)",
    re.IGNORECASE,
)
_MED_ASK = re.compile(
    r"(وقت\s*الدوا|الدوا|الدواء|الإنسولين|الانسولين|ميتفورمين|وجّه\s*الدوا)",
    re.IGNORECASE,
)
_MED_TAKEN = re.compile(
    r"(خذيت|خديت|خدّيت|ماخذيتش|ما\s*خذيتش|نسيت)",
    re.IGNORECASE,
)
_GAME = re.compile(r"(نلعبو|لعبة|اللعبة|تمرين|الذاكرة)", re.IGNORECASE)
_GLUCOSE = re.compile(r"(السكر|سكر|غلوكوز|قستي)", re.IGNORECASE)


class SkillRouter:
    def route(
        self,
        text: str,
        *,
        pending_whatsapp: bool = False,
        pending_dose: bool = False,
        pending_game: bool = False,
    ) -> Intent:
        cleaned = (text or "").strip()
        if not cleaned:
            return Intent.CHAT

        # Highest priority: SOS always
        if _SOS.search(cleaned):
            return Intent.SOS

        if pending_dose and (
            _MED_TAKEN.search(cleaned)
            or _CONFIRM.search(cleaned)
            or cleaned in {"نعم", "واخا", "اه"}
        ):
            return Intent.MED_RESPONSE

        if pending_game and not _GAME.search(cleaned):
            return Intent.GAME_ANSWER

        if pending_whatsapp:
            if _CANCEL.search(cleaned) or "ما تصيفط" in cleaned or "ماصيفط" in cleaned:
                return Intent.CANCEL
            if _CONFIRM.search(cleaned) or cleaned in {"نعم", "واخا", "أيه", "اه", "اييه"}:
                return Intent.CONFIRM
            if _MORNING.search(cleaned):
                return Intent.MORNING
            if _WEATHER.search(cleaned):
                return Intent.WEATHER
            if _NEWS.search(cleaned):
                return Intent.NEWS
            if _MED_ASK.search(cleaned):
                return Intent.MED_REMINDER
            return Intent.WHATSAPP_SEND

        if _GAME.search(cleaned):
            return Intent.GAME
        if _GLUCOSE.search(cleaned):
            return Intent.GLUCOSE
        if _MED_ASK.search(cleaned) or _MED_TAKEN.search(cleaned):
            if _MED_TAKEN.search(cleaned):
                return Intent.MED_RESPONSE
            return Intent.MED_REMINDER
        if _MORNING.search(cleaned):
            return Intent.MORNING
        if _WHATSAPP.search(cleaned):
            return Intent.WHATSAPP_SEND
        if _WEATHER.search(cleaned):
            return Intent.WEATHER
        if _NEWS.search(cleaned):
            return Intent.NEWS
        return Intent.CHAT
