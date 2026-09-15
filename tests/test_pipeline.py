import pytest

from bchkito.config import Settings
from bchkito.prompts_loader import load_prompt
from bchkito.voice.pipeline import VoicePipeline


def test_prompts_load():
    text = load_prompt("darija_system.md")
    assert "Bchkito" in text
    assert "دارجة" in text or "Darija" in text
    assert load_prompt("skills", "weather.md")


@pytest.mark.asyncio
async def test_pipeline_weather_without_keys(tmp_path):
    settings = Settings(
        openweather_api_key="",
        cache_dir=tmp_path,
        log_dir=tmp_path / "logs",
        cloud_llm_provider="none",
    )
    pipeline = VoicePipeline(settings)
    result = await pipeline.handle_transcript("كيفاش الجو فإفران", speak=False)
    assert result.intent.value == "weather"
    assert "إفران" in result.reply or "درجة" in result.reply


@pytest.mark.asyncio
async def test_pipeline_whatsapp_confirm_flow(tmp_path):
    settings = Settings(
        cache_dir=tmp_path,
        log_dir=tmp_path / "logs",
        daughter_wa_phone="",
        cloud_llm_provider="none",
    )
    pipeline = VoicePipeline(settings)
    draft = await pipeline.handle_transcript("صيفط ل بنتي راني بخير", speak=False)
    assert draft.intent.value == "whatsapp_send"
    assert "راني بخير" in draft.reply
    confirm = await pipeline.handle_transcript("نعم", speak=False)
    assert "الإعدادات" in confirm.reply or "ماكاف" in confirm.reply or "واتساب" in confirm.reply
