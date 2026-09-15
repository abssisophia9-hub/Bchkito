# Bchkito

Tiny, cute **AI-powered robotic companion** for elderly Moroccan speakers of **Darija**, designed to run on a **Raspberry Pi** with Python, open APIs, and a mostly-local voice stack.

## Core features (MVP)

1. **Darija Voice OS** — local `faster-whisper` STT → skill router → Ollama (local) / Groq|Together (cloud) → tiered TTS (Piper / Azure / ElevenLabs)
2. **Localized Info Hub** — OpenWeatherMap + Moroccan RSS, spoken as caring Darija updates
3. **Family Bridge** — WhatsApp Cloud API; dictate in Darija, confirm, send text or voice note

## Quick start (dev machine)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
bchkito doctor
bchkito once "كيفاش الجو فإفران"
bchkito run
```

On the Pi, install STT extras and models:

```bash
pip install -e ".[stt,dev]"
bash scripts/download_models.sh
bchkito run --ptt
python scripts/spike_eval.py
```

See [docs/RUNBOOK.md](docs/RUNBOOK.md) and [docs/FIELD_TEST.md](docs/FIELD_TEST.md).

## Architecture

```
Mic → VAD → Whisper → Router → Skills (chat / weather / news / WhatsApp)
                              ↓
                     Local or cloud LLM
                              ↓
                     Local or cloud TTS → Speaker
```

Push-to-talk (GPIO button or keyboard) avoids wake-word complexity for v1.

## Configuration

All settings use the `BCHKITO_` prefix. Copy [.env.example](.env.example).

| Area | Keys |
|------|------|
| Device | `DEFAULT_CITY`, `DAUGHTER_WA_PHONE`, `PTT_MODE` |
| STT | `WHISPER_MODEL`, `WHISPER_DEVICE` |
| LLM | `OLLAMA_*`, `GROQ_*` / `TOGETHER_*` |
| TTS | `TTS_DEFAULT_TIER`, `PIPER_*`, `AZURE_*`, `ELEVENLABS_*` |
| Hub | `OPENWEATHER_API_KEY`, `RSS_FEEDS` |
| WhatsApp | `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` |

## Tests

```bash
pytest -q
```

## License

MIT
