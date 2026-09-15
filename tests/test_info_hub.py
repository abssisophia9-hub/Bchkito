from bchkito.config import Settings
from bchkito.integrations.openweather import WeatherSnapshot
from bchkito.skills.info_hub import InfoHubSkill
from bchkito.voice.llm_cloud import CloudLLM
from bchkito.voice.llm_local import LocalLLM


def test_weather_template_cold_jacket():
    settings = Settings(
        openweather_api_key="",
        weather_cold_c=12,
        weather_hot_c=30,
        weather_wind_ms=8,
    )
    skill = InfoHubSkill(settings, LocalLLM(settings), CloudLLM(settings))
    snap = WeatherSnapshot(
        city="Ifrane",
        temp_c=5.0,
        feels_like_c=2.0,
        wind_ms=3.0,
        humidity=70,
        description="clear sky",
        weather_code=800,
    )
    text = skill.render_weather_template(snap)
    assert "إفران" in text
    assert "جاكيت" in text


def test_weather_template_hot_and_wind():
    settings = Settings()
    skill = InfoHubSkill(settings, LocalLLM(settings), CloudLLM(settings))
    snap = WeatherSnapshot(
        city="Marrakech",
        temp_c=36.0,
        feels_like_c=38.0,
        wind_ms=12.0,
        humidity=20,
        description="clear sky",
        weather_code=800,
    )
    text = skill.render_weather_template(snap)
    assert "مراكش" in text
    assert "الما" in text
    assert "الريح" in text
