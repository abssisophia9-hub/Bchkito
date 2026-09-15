# Bchkito — process log

How we went from an empty repo to a **care-pendant prototype**, and how to continue.

## Timeline (this project)

| Step | What we did | Outcome |
|------|-------------|---------|
| 1. Brief | Scoped a Darija companion for elderly Moroccans: Voice OS, Info Hub, WhatsApp Family Bridge; Python + open APIs + Raspberry Pi; &lt;90 days | Product constraints locked |
| 2. Architecture choices | Mostly-local on Pi + multicloud LLM/TTS when needed | Cost/privacy trade-off documented |
| 3. MVP v1 build | Scaffolded `src/bchkito/`: Whisper STT, Ollama/cloud LLM, tiered TTS, weather/RSS, WhatsApp client, PTT loop, tests | Runnable voice CLI + unit tests |
| 4. First prototype UI | `scripts/prototype_server.py` text chips demo | Browser demo without Pi hardware |
| 5. Product pivot | Elders don’t type; family manages; voice + WhatsApp; diabetes/meds; SOS; neck wearable; mind games | [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) |
| 6. Care prototype v2 | Care data store, med reminder/confirm, SOS alerts, caregiver dashboard + pendant simulator | Live at `/` and `/elder` |

## Design principles we locked

1. **Elder never configures tech** — family owns the dashboard.
2. **Voice is primary** — Darija spoken reminders and confirmations.
3. **WhatsApp is the family rail** — miss/SOS alerts where Moroccans already chat.
4. **Reminders + logs, not a medical device** — no insulin dosing advice.
5. **Pendant + hub + cloud** — don’t put a Pi around someone’s neck.

## Repository map

```
docs/
  ARCHITECTURE_V2.md   # system rethink (wearable, budget, flows)
  PROCESS.md           # this file
  RUNBOOK.md           # Pi install / systemd
  FIELD_TEST.md        # elderly field checklist
src/bchkito/
  care/                # meds, doses, glucose, alerts, games
  voice/               # STT → router → skills → TTS
  web/pages.py         # caregiver + elder HTML
  skills/              # router + chat/info/family
scripts/
  prototype_server.py  # dual UI prototype (port 8765/8766)
tests/                 # router, care, integrations, pipeline
```

## How to run the care prototype

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env

# optional if 8765 busy
$env:BCHKITO_PORT='8766'
python scripts/prototype_server.py
```

- Family: http://127.0.0.1:8766/
- Elder pendant simulator: http://127.0.0.1:8766/elder

### Demo script (5 minutes)

1. Dashboard → **محاكاة: حان وقت الدوا**
2. Elder UI → **خذيت الدوا** → compliance counter updates
3. Elder UI → **SOS** → critical alert + WhatsApp outbox stub
4. Elder UI → **نلعبو** → short mind-game turn
5. Dashboard → add medication / log glucose / mark dose manually

## Engineering process going forward

1. **Spike first** on real audio (ESP32-S3 mic/speaker + BLE) before PCB.
2. Keep **care logic in Python cloud/hub**; pendant stays thin.
3. Every health feature: caregiver-authored text only; escalate to family, never invent clinical advice.
4. Tests required for router intents + dose state machine before merging features.
5. Field test with 2–3 families using [FIELD_TEST.md](FIELD_TEST.md) before hardware freeze.

## Suggested next milestones

| Phase | Focus |
|-------|--------|
| P1 | Persist care store in Postgres; real WhatsApp delivery; grace-timer worker |
| P2 | Minimal React/RTL dashboard polish; auth for caregivers |
| P3 | ESP32 pendant firmware + BLE audio bridge to hub |
| P4 | Enclosure, battery life, 3-family pilot |

## Merge note

Care prototype work is intended to land on `main` as the current product direction (v2). Legacy v1 voice/Info Hub skills remain as companionship features behind the same router.
