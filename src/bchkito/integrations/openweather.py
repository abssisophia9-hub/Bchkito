from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from bchkito.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class WeatherSnapshot:
    city: str
    temp_c: float
    feels_like_c: float
    wind_ms: float
    humidity: int
    description: str
    weather_code: int


class OpenWeatherClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def current(self, city: str) -> WeatherSnapshot:
        if not self.settings.openweather_api_key:
            # Deterministic offline stub for local/dev without keys
            logger.warning("OPENWEATHER_API_KEY missing; using stub weather")
            return WeatherSnapshot(
                city=city,
                temp_c=8.0 if city.lower() == "ifrane" else 18.0,
                feels_like_c=6.0 if city.lower() == "ifrane" else 17.0,
                wind_ms=3.5,
                humidity=55,
                description="clear sky",
                weather_code=800,
            )

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": self.settings.openweather_api_key,
            "units": self.settings.openweather_units,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        weather0 = (data.get("weather") or [{}])[0]
        main = data.get("main") or {}
        wind = data.get("wind") or {}
        return WeatherSnapshot(
            city=data.get("name") or city,
            temp_c=float(main.get("temp", 0.0)),
            feels_like_c=float(main.get("feels_like", 0.0)),
            wind_ms=float(wind.get("speed", 0.0)),
            humidity=int(main.get("humidity", 0)),
            description=str(weather0.get("description", "")),
            weather_code=int(weather0.get("id", 0)),
        )
