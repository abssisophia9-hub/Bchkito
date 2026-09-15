import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from bchkito.config import Settings
from bchkito.integrations.rss_morocco import MoroccanRSS
from bchkito.integrations.whatsapp_cloud import WhatsAppClient
from bchkito.skills.family_bridge import FamilyBridgeSkill
from bchkito.voice.llm_cloud import CloudLLM
from bchkito.voice.llm_local import LocalLLM
from bchkito.voice.tts_cloud import CloudTTS
from bchkito.voice.tts_local import LocalTTS


def test_extract_whatsapp_message():
    settings = Settings()
    skill = FamilyBridgeSkill(
        settings,
        LocalLLM(settings),
        CloudLLM(settings),
        CloudTTS(settings),
        LocalTTS(settings),
    )
    assert skill.extract_message("صيفط ل بنتي راني بخير") == "راني بخير"


@pytest.mark.asyncio
@respx.mock
async def test_whatsapp_send_text(tmp_path: Path):
    settings = Settings(
        whatsapp_token="token",
        whatsapp_phone_number_id="123",
        whatsapp_api_version="v21.0",
        daughter_wa_phone="+212612345678",
        cache_dir=tmp_path,
    )
    route = respx.post(
        "https://graph.facebook.com/v21.0/123/messages"
    ).mock(return_value=Response(200, json={"messages": [{"id": "wamid.TEST"}]}))
    client = WhatsAppClient(settings)
    data = await client.send_text(settings.daughter_wa_phone, "سلام")
    assert route.called
    assert data["messages"][0]["id"] == "wamid.TEST"


@pytest.mark.asyncio
@respx.mock
async def test_rss_parse_and_cache(tmp_path: Path):
    feed_xml = """<?xml version='1.0'?>
    <rss version='2.0'><channel>
      <title>Test</title>
      <item><title>عنوان تجريبي</title><link>https://example.com/1</link><guid>g1</guid></item>
      <item><title>خبر ثاني</title><link>https://example.com/2</link><guid>g2</guid></item>
    </channel></rss>
    """
    settings = Settings(
        rss_feeds="https://example.com/feed",
        news_cache_minutes=30,
        cache_dir=tmp_path,
    )
    respx.get("https://example.com/feed").mock(
        return_value=Response(200, text=feed_xml)
    )
    rss = MoroccanRSS(settings)
    items = await rss.latest(limit=2)
    assert len(items) == 2
    assert items[0].title == "عنوان تجريبي"
    assert (tmp_path / "news_cache.json").exists()
    cached = json.loads((tmp_path / "news_cache.json").read_text(encoding="utf-8"))
    assert len(cached["items"]) == 2
