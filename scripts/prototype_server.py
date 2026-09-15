#!/usr/bin/env python3
"""
Bchkito Care Prototype — caregiver dashboard + elder pendant simulator.

  python scripts/prototype_server.py
  → http://127.0.0.1:8765/          caregiver dashboard
  → http://127.0.0.1:8765/elder     neck-pendant voice simulator
"""
from __future__ import annotations

import asyncio
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bchkito.care.models import Appointment, GlucoseLog, Medication, utcnow
from bchkito.care.service import CareService
from bchkito.care.store import get_care_store
from bchkito.config import get_settings
from bchkito.logging_setup import setup_logging
from bchkito.voice.pipeline import VoicePipeline
from bchkito.web.pages import CAREGIVER_HTML, ELDER_HTML

HOST = "127.0.0.1"
PORT = int(__import__("os").environ.get("BCHKITO_PORT", "8765"))

_loop = asyncio.new_event_loop()
_pipeline: VoicePipeline | None = None
_care: CareService | None = None
_lock = threading.Lock()


def _ensure() -> tuple[VoicePipeline, CareService]:
    global _pipeline, _care
    with _lock:
        if _pipeline is None:
            settings = get_settings()
            setup_logging(settings.log_level, settings.log_dir)
            store = get_care_store(Path("data/care_state.json"))
            _care = CareService(store, settings)
            _pipeline = VoicePipeline(settings)
            _pipeline.care = _care
        assert _pipeline is not None and _care is not None
        return _pipeline, _care


def _run_turn(text: str) -> dict:
    pipeline, care = _ensure()
    result = _loop.run_until_complete(pipeline.handle_transcript(text, speak=False))
    state = care.store.load()
    return {
        "transcript": result.transcript,
        "intent": result.intent.value,
        "reply": result.reply,
        "latency_s": round(result.latency_s, 2),
        "cloud_llm": result.used_cloud_llm,
        "tts_tier": result.tts_tier,
        "pending_whatsapp": bool(pipeline._pending_whatsapp),
        "pending_dose": bool(state.pending_dose_id),
        "pending_game": bool(state.pending_game_id),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict | list) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/index.html", "/dashboard"}:
            self._send(200, CAREGIVER_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path in {"/elder", "/pendant"}:
            self._send(200, ELDER_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/api/care/state":
            _, care = _ensure()
            state = care.snapshot()
            self._json(200, state.model_dump(mode="json"))
            return
        if path == "/api/care/compliance":
            _, care = _ensure()
            self._json(200, care.compliance_today())
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/turn":
                payload = self._read_json()
                text = str(payload.get("text", "")).strip()
                if not text:
                    raise ValueError("empty text")
                self._json(200, _run_turn(text))
                return

            _, care = _ensure()

            if path == "/api/care/demo/due":
                dose = care.force_due_for_demo()
                reply, _ = care.start_reminder(dose.id if dose else None)
                self._json(
                    200,
                    {
                        "ok": True,
                        "reminder": reply,
                        "dose": dose.model_dump(mode="json") if dose else None,
                    },
                )
                return

            if path == "/api/care/sos":
                reply = care.trigger_sos("button")
                self._json(200, {"ok": True, "reply": reply})
                return

            if path == "/api/care/medications":
                payload = self._read_json()
                med = care.upsert_medication(payload)
                self._json(200, med.model_dump(mode="json"))
                return

            if path == "/api/care/glucose":
                payload = self._read_json()

                def mutate(state) -> None:
                    state.glucose.insert(
                        0,
                        GlucoseLog(
                            value_mg_dl=payload.get("value_mg_dl"),
                            note=payload.get("note") or "",
                            source="caregiver",
                        ),
                    )

                care.store.update(mutate)
                self._json(200, {"ok": True})
                return

            if path == "/api/care/appointments":
                payload = self._read_json()
                apt = care.add_appointment(payload)
                self._json(200, apt.model_dump(mode="json"))
                return

            if path.startswith("/api/care/doses/") and path.count("/") == 4:
                dose_id = path.rsplit("/", 1)[-1]
                payload = self._read_json()
                dose = care.caregiver_mark_dose(dose_id, payload.get("status", "taken"))
                if not dose:
                    self._json(404, {"error": "dose not found"})
                    return
                self._json(200, dose.model_dump(mode="json"))
                return

            if path.endswith("/ack") and path.startswith("/api/care/alerts/"):
                alert_id = path.split("/")[4]
                care.ack_alert(alert_id)
                self._json(200, {"ok": True})
                return

            self._json(404, {"error": "not found"})
        except Exception as exc:
            self._json(500, {"error": str(exc)})


def main() -> int:
    asyncio.set_event_loop(_loop)
    _ensure()
    url = f"http://{HOST}:{PORT}"
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Bchkito Care prototype")
    print(f"  Caregiver dashboard → {url}/")
    print(f"  Elder pendant       → {url}/elder")
    print("Press Ctrl+C to stop.")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
