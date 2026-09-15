#!/usr/bin/env bash
# Download / pull models used by Bchkito on Raspberry Pi.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p models/piper models/whisper data/cache logs

echo "==> Ollama model"
if command -v ollama >/dev/null 2>&1; then
  ollama pull "${BCHKITO_OLLAMA_MODEL:-qwen2.5:3b}"
else
  echo "ollama not installed — skip (install from https://ollama.com)"
fi

echo "==> faster-whisper will auto-download on first run (model=${BCHKITO_WHISPER_MODEL:-small})"

echo "==> Piper Arabic voice (optional)"
PIPER_URL="${PIPER_MODEL_URL:-https://huggingface.co/rhasspy/piper-voices/resolve/main/ar/ar_JO/kareem/medium/ar_JO-kareem-medium.onnx}"
PIPER_JSON_URL="${PIPER_JSON_URL:-https://huggingface.co/rhasspy/piper-voices/resolve/main/ar/ar_JO/kareem/medium/ar_JO-kareem-medium.onnx.json}"
if command -v curl >/dev/null 2>&1; then
  if [[ ! -f models/piper/ar_JO-kareem-medium.onnx ]]; then
    curl -L "$PIPER_URL" -o models/piper/ar_JO-kareem-medium.onnx || true
    curl -L "$PIPER_JSON_URL" -o models/piper/ar_JO-kareem-medium.onnx.json || true
  fi
else
  echo "curl missing — download Piper model manually into models/piper/"
fi

echo "Done. Copy .env.example -> .env and fill API keys as needed."
