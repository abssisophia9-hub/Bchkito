#!/usr/bin/env python3
"""Week 1–2 spike: measure pipeline + TTS latency on fixed Darija phrases."""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bchkito.config import get_settings
from bchkito.logging_setup import setup_logging
from bchkito.voice.llm_local import LocalLLM
from bchkito.voice.pipeline import VoicePipeline
from bchkito.voice.stt_whisper import WhisperSTT
from bchkito.voice.tts_local import LocalTTS

PHRASES = [
    "صباح الخير بشكيتو",
    "كيفاش الجو فإفران",
    "شنو فالأخبار",
    "صيفط ل بنتي راني بخير",
    "واخا صيفط",
    "بغيت نشرب أتاي",
    "شحال الساعة تقريبا",
    "البرد قوي اليوم",
    "عافاك عاود",
    "بسلامة",
    "فين كاينة مكناس",
    "قولي ل بنتي نسول عليها",
    "الجو ف الرباط",
    "شنو جديد اليوم",
    "لا ما تصيفطش",
    "أنا حسّيت براسي عيان شوية",
    "فتح الراديو",
    "شكرا بزاف",
    "كي دايرة بنتي",
    "صباح النور",
]


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_dir)
    out_dir = Path("data/cache")
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline = VoicePipeline(settings)
    stt = WhisperSTT(settings)
    tts = LocalTTS(settings)
    local = LocalLLM(settings)

    rows = []
    for phrase in PHRASES:
        t0 = time.perf_counter()
        turn = await pipeline.handle_transcript(phrase, speak=False)
        pipeline_ms = (time.perf_counter() - t0) * 1000
        t1 = time.perf_counter()
        path = await tts.synthesize(turn.reply or phrase)
        tts_ms = (time.perf_counter() - t1) * 1000
        rows.append(
            {
                "phrase": phrase,
                "intent": turn.intent.value,
                "reply": turn.reply,
                "pipeline_ms": round(pipeline_ms, 1),
                "tts_ms": round(tts_ms, 1),
                "tts_path": str(path),
                "cloud_llm": turn.used_cloud_llm,
            }
        )
        print(f"OK intent={turn.intent.value} pipeline_ms={pipeline_ms:.0f}")

    _ = stt.transcribe(np.zeros(0, dtype=np.float32))
    _ = await local.chat(
        [
            {"role": "system", "content": "جاوب بجملة قصيرة بالدارجة."},
            {"role": "user", "content": "صباح الخير"},
        ]
    )

    report = out_dir / "spike_report.json"
    report.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {report} ({len(rows)} phrases)")


if __name__ == "__main__":
    asyncio.run(main())
