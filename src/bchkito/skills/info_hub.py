from __future__ import annotations

import logging

from bchkito.config import Settings
from bchkito.integrations.openweather import OpenWeatherClient, WeatherSnapshot
from bchkito.integrations.rss_morocco import MoroccanRSS
from bchkito.prompts_loader import load_prompt
from bchkito.voice.llm_cloud import CloudLLM
from bchkito.voice.llm_local import LocalLLM

logger = logging.getLogger(__name__)

_CITY_HINTS = {
    "إفران": "Ifrane",
    "افران": "Ifrane",
    "الرباط": "Rabat",
    "الدار البيضاء": "Casablanca",
    "كازا": "Casablanca",
    "فاس": "Fes",
    "مراكش": "Marrakech",
    "طنجة": "Tangier",
    "أغادير": "Agadir",
    "اكادير": "Agadir",
    "مكناس": "Meknes",
    "وجدة": "Oujda",
}


class InfoHubSkill:
    def __init__(
        self,
        settings: Settings,
        local_llm: LocalLLM,
        cloud_llm: CloudLLM,
    ) -> None:
        self.settings = settings
        self.local_llm = local_llm
        self.cloud_llm = cloud_llm
        self.weather_client = OpenWeatherClient(settings)
        self.rss = MoroccanRSS(settings)
        self.weather_prompt = load_prompt("skills", "weather.md")
        self.news_prompt = load_prompt("skills", "news.md")

    def _detect_city(self, text: str) -> str:
        for ar, en in _CITY_HINTS.items():
            if ar in text:
                return en
        return self.settings.default_city

    def render_weather_template(self, snap: WeatherSnapshot) -> str:
        city_ar = {
            "Ifrane": "إفران",
            "Rabat": "الرباط",
            "Casablanca": "الدار البيضاء",
            "Fes": "فاس",
            "Marrakech": "مراكش",
            "Tangier": "طنجة",
            "Agadir": "أكادير",
            "Meknes": "مكناس",
            "Oujda": "وجدة",
        }.get(snap.city, snap.city)

        temp = snap.temp_c
        parts: list[str] = []
        if temp <= self.settings.weather_cold_c:
            parts.append(
                f"بارد اليوم فـ {city_ar}، الحرارة حوالي {temp:.0f} درجة، البس شي جاكيت."
            )
        elif temp >= self.settings.weather_hot_c:
            parts.append(
                f"سخون اليوم فـ {city_ar}، حوالي {temp:.0f} درجة، اشرب الما وبرّد راسك."
            )
        else:
            parts.append(
                f"الجو معقول فـ {city_ar} اليوم، حوالي {temp:.0f} درجة."
            )

        if snap.wind_ms >= self.settings.weather_wind_ms:
            parts.append("الريح شوية قوية، خرجي بالحيطة.")
        if "rain" in snap.description.lower() or snap.weather_code in {500, 501, 502, 520}:
            parts.append("يمكن تمطر، خدّي معاك شي مظلة.")
        elif "cloud" in snap.description.lower():
            parts.append("السما مغيمة شوية.")

        return " ".join(parts[:3])

    async def weather(self, user_text: str) -> tuple[str, bool]:
        city = self._detect_city(user_text)
        try:
            snap = await self.weather_client.current(city)
        except Exception as exc:
            logger.warning("Weather fetch failed: %s", exc)
            return "ما قدرتش نجيب الجو دابا، جربي من بعد شوية.", False

        base = self.render_weather_template(snap)
        # Optional light paraphrase via LLM (non-blocking if fails)
        messages = [
            {"role": "system", "content": self.weather_prompt},
            {
                "role": "user",
                "content": (
                    f"أعد صياغة قصيرة بالدارجة دون تغيير المعنى:\n{base}"
                ),
            },
        ]
        paraphrased = await self.local_llm.chat(messages, temperature=0.2)
        if paraphrased and len(paraphrased) < 220:
            return paraphrased, False
        return base, False

    async def news(
        self,
        *,
        prefer_cloud: bool = True,
        max_items: int = 2,
    ) -> tuple[str, bool]:
        try:
            items = await self.rss.latest(limit=max_items)
        except Exception as exc:
            logger.warning("RSS failed: %s", exc)
            return "ما قدرتش نجيب الأخبار دابا.", False

        if not items:
            return "ما لقيتاش أخبار جديدة دابا.", False

        bullets = "\n".join(f"- {it.title}" for it in items)
        messages = [
            {"role": "system", "content": self.news_prompt},
            {
                "role": "user",
                "content": (
                    "لخّص هاد العناوين بالدارجة للمسنين، جملتين على الأكثر:\n"
                    f"{bullets}"
                ),
            },
        ]
        used_cloud = False
        text = ""
        if prefer_cloud and self.cloud_llm.available:
            text = await self.cloud_llm.chat(messages)
            used_cloud = bool(text)
        if not text:
            text = await self.local_llm.chat(messages)
        if not text and self.cloud_llm.available:
            text = await self.cloud_llm.chat(messages)
            used_cloud = bool(text)
        if not text:
            # Offline / no-LLM fallback: read first title
            first = items[0].title
            text = f"من الأخبار: {first}."
        return text.strip(), used_cloud
