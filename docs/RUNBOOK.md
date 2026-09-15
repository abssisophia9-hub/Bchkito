# Bchkito runbook (Raspberry Pi)

## Install (Pi OS Bookworm, 64-bit)

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip portaudio19-dev espeak-ng git curl
# Optional: piper binary on PATH; Ollama from https://ollama.com
cd ~
git clone <your-repo-url> Bchkito
cd Bchkito
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[stt,dev]"
# Optional GPIO: pip install -e ".[gpio]"
cp .env.example .env
# edit .env
bash scripts/download_models.sh
```

## Service

```bash
sudo cp deploy/systemd/bchkito.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bchkito
journalctl -u bchkito -f
```

## Offline behaviour
- STT + local LLM + local TTS continue without internet.
- Weather uses stub or last failure phrase.
- News serves cache if younger than `BCHKITO_NEWS_CACHE_MINUTES`, else “ما قدرتش نجيب الأخبار دابا.”
- WhatsApp / cloud LLM / Azure / ElevenLabs require network; spoken error if missing.

## Latency tips
- Prefer Pi 5 8GB.
- Start with `BCHKITO_WHISPER_MODEL=small` (or `tiny` if slow).
- Keep Ollama model at 3B class for interactive chat; escalate news/WhatsApp cleanup to Groq/Together.

## WhatsApp Meta setup
1. Create Meta app → WhatsApp product → add test number.
2. Set `BCHKITO_WHATSAPP_TOKEN` and `BCHKITO_WHATSAPP_PHONE_NUMBER_ID`.
3. Add daughter phone to allow-list in test mode.
4. Smoke test: `python scripts/whatsapp_hello.py سلام`
5. MVP is **outbound-only**; inbound webhooks optional later.
