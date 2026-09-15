from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BCHKITO_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    default_city: str = "Ifrane"
    second_city: str = ""
    daughter_name: str = "بنتي"
    daughter_wa_phone: str = ""

    ptt_mode: Literal["keyboard", "gpio", "auto"] = "keyboard"
    ptt_gpio_pin: int = 17
    sample_rate: int = 16000
    log_level: str = "INFO"
    log_dir: Path = Path("logs")

    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_language: str = "ar"
    whisper_initial_prompt: str = (
        "مرحبا، الجو فإفران، الأخبار، بنتي، واتساب، صباح الخير"
    )

    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"
    llm_timeout_seconds: float = 45.0

    cloud_llm_provider: Literal["none", "groq", "together"] = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    together_api_key: str = ""
    together_model: str = "Qwen/Qwen2.5-7B-Instruct-Turbo"

    tts_default_tier: Literal["local", "azure", "elevenlabs"] = "local"
    piper_binary: str = "piper"
    piper_model_path: Path = Path("models/piper/ar_JO-kareem-medium.onnx")
    piper_speaker: int = 0
    espeak_voice: str = "ar"
    azure_speech_key: str = ""
    azure_speech_region: str = "westeurope"
    azure_speech_voice: str = "ar-EG-SalmaNeural"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    openweather_api_key: str = ""
    openweather_units: str = "metric"
    weather_cold_c: float = 12.0
    weather_hot_c: float = 30.0
    weather_wind_ms: float = 8.0

    rss_feeds: str = (
        "https://www.hespress.com/feed,"
        "https://www.medi1tv.com/ar/rss,"
        "https://www.yabiladi.com/rss/news.xml"
    )
    news_cache_minutes: int = 20
    cache_dir: Path = Path("data/cache")

    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_api_version: str = "v21.0"
    whatsapp_default_mode: Literal["text", "voice"] = "text"

    @field_validator("rss_feeds", mode="before")
    @classmethod
    def _strip_feeds(cls, value: object) -> object:
        return value

    @property
    def rss_feed_list(self) -> list[str]:
        return [u.strip() for u in self.rss_feeds.split(",") if u.strip()]

    @property
    def cloud_llm_configured(self) -> bool:
        if self.cloud_llm_provider == "groq":
            return bool(self.groq_api_key)
        if self.cloud_llm_provider == "together":
            return bool(self.together_api_key)
        return False


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    return settings
