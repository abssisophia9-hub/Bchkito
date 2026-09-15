#!/usr/bin/env python3
"""Send a one-off WhatsApp Cloud API test text (requires env credentials)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bchkito.config import get_settings
from bchkito.integrations.whatsapp_cloud import WhatsAppClient


async def main() -> int:
    settings = get_settings()
    client = WhatsAppClient(settings)
    if not client.configured:
        print("Missing BCHKITO_WHATSAPP_TOKEN / BCHKITO_WHATSAPP_PHONE_NUMBER_ID")
        return 1
    if not settings.daughter_wa_phone:
        print("Missing BCHKITO_DAUGHTER_WA_PHONE")
        return 1
    body = " ".join(sys.argv[1:]) or "سلام من بشكيتو 👋"
    data = await client.send_text(settings.daughter_wa_phone, body)
    print(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
