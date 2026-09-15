from __future__ import annotations

import argparse
import asyncio
import logging
import sys


def _configure_stdio() -> None:
    """Best-effort UTF-8 stdout/stderr (Windows cp1252 can't print Darija)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()


from bchkito.audio.capture import record_until
from bchkito.config import get_settings
from bchkito.logging_setup import setup_logging
from bchkito.ui.ptt_gpio import PushToTalk, make_ptt_predicate
from bchkito.voice.pipeline import VoicePipeline, VoiceState

logger = logging.getLogger(__name__)


async def run_text_repl() -> int:
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_dir)
    pipeline = VoicePipeline(settings)
    safe_print("Bchkito text mode. Type Darija (or 'خروج' to quit).")
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(
                None, lambda: input("text> ").strip()
            )
        except (EOFError, KeyboardInterrupt):
            safe_print("\nبسلامة!")
            return 0
        if not line:
            continue
        if line.lower() in {"quit", "exit", "خروج"}:
            safe_print("بسلامة!")
            return 0
        result = await pipeline.handle_transcript(line, speak=False)
        safe_print(f"[{result.intent.value}] {result.reply}")
        safe_print(
            f"  latency={result.latency_s:.2f}s cloud_llm={result.used_cloud_llm} "
            f"tts={result.tts_tier}"
        )


async def run_ptt_loop() -> int:
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_dir)
    pipeline = VoicePipeline(settings)
    ptt = PushToTalk(settings)
    ptt.start()
    safe_print("Bchkito PTT mode. Hold the button / toggle SPACE, speak Darija.")
    try:
        while True:
            pipeline.state = VoiceState.LISTENING
            safe_print("Waiting for PTT...")
            await asyncio.to_thread(ptt.wait_press)
            if ptt._stop.is_set():
                break
            safe_print("Listening...")
            audio = await asyncio.to_thread(
                record_until, make_ptt_predicate(ptt), settings, 30.0
            )
            await asyncio.to_thread(ptt.wait_release)
            if audio.size == 0:
                continue
            result = await pipeline.handle_audio(audio, speak=True)
            safe_print(f"Heard: {result.transcript}")
            safe_print(
                f"[{result.intent.value}] {result.reply} ({result.latency_s:.1f}s)"
            )
    except KeyboardInterrupt:
        safe_print("\nبسلامة!")
    finally:
        ptt.stop()
    return 0


async def run_once(text: str, *, speak: bool = False) -> int:
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_dir)
    pipeline = VoicePipeline(settings)
    result = await pipeline.handle_transcript(text, speak=speak)
    safe_print(result.reply)
    safe_print(
        f"# intent={result.intent.value} latency={result.latency_s:.2f}s "
        f"cloud={result.used_cloud_llm}"
    )
    return 0


def doctor() -> int:
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_dir)
    checks = {
        "default_city": settings.default_city,
        "whisper_model": settings.whisper_model,
        "ollama_host": settings.ollama_host,
        "cloud_llm": (
            settings.cloud_llm_provider if settings.cloud_llm_configured else "disabled"
        ),
        "openweather": "yes" if settings.openweather_api_key else "stub",
        "whatsapp": (
            "yes"
            if (settings.whatsapp_token and settings.whatsapp_phone_number_id)
            else "missing"
        ),
        "tts_default": settings.tts_default_tier,
        "rss_feeds": len(settings.rss_feed_list),
        "daughter_phone": "set" if settings.daughter_wa_phone else "missing",
    }
    for key, value in checks.items():
        safe_print(f"{key}: {value}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bchkito", description="Darija companion")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Interactive companion loop")
    run_p.add_argument(
        "--ptt",
        action="store_true",
        help="Use microphone push-to-talk instead of text REPL",
    )

    once = sub.add_parser("once", help="Single text turn")
    once.add_argument("text", nargs="+", help="Utterance in Darija")
    once.add_argument("--speak", action="store_true", help="Also run TTS/playback")

    sub.add_parser("doctor", help="Print config / dependency health")
    return parser


def main(argv: list[str] | None = None) -> None:
    _configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "once":
        raise SystemExit(asyncio.run(run_once(" ".join(args.text), speak=args.speak)))
    if args.command == "doctor":
        raise SystemExit(doctor())
    if args.command == "run" and getattr(args, "ptt", False):
        raise SystemExit(asyncio.run(run_ptt_loop()))
    raise SystemExit(asyncio.run(run_text_repl()))


if __name__ == "__main__":
    main()
