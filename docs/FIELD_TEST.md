# Bchkito field-test checklist (elderly Moroccan users)

## Before the visit
- [ ] Pi boots to desktop/CLI and `systemctl status bchkito` is active
- [ ] Speaker volume set high enough for hard-of-hearing users
- [ ] Mic gain tested at ~1 meter
- [ ] `.env` has default city + daughter WhatsApp number
- [ ] Offline phrase works: spoken “ما قدرتش…” when Wi‑Fi unplugged (news/weather)

## Tasks with the senior (20–30 min)
1. Greeting: “صباح الخير” → warm short Darija reply
2. Weather: “كيفاش الجو فإفران” → jacket / heat advice, not raw °C dump
3. News: “شنو فالأخبار” → at most two calm headlines
4. Family Bridge:
   - “صيفط ل بنتي راني بخير”
   - Robot reads back and asks confirmation
   - Senior says “نعم” → daughter receives text/voice note
5. Cancel path: start a draft, say “لا” → nothing sent
6. Mishear path: mumble → robot asks to repeat

## Pass / fail notes
- Latency acceptable? (target under ~15s turn)
- TTS understandable?
- Any fear / confusion about confirmation?
- Preferred PTT button vs wake word later?

## After
- Copy `logs/bchkito.log` (no raw audio unless consented)
- Note Whisper model size used and any OOM / thermal throttling
