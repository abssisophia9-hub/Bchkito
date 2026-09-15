from __future__ import annotations

import logging
from datetime import timedelta

from bchkito.care.models import (
    Alert,
    AlertSeverity,
    AlertType,
    CareState,
    DoseStatus,
    utcnow,
)
from bchkito.care.store import CareStore
from bchkito.config import Settings
from bchkito.integrations.whatsapp_cloud import WhatsAppClient

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self, store: CareStore, settings: Settings) -> None:
        self.store = store
        self.settings = settings
        self.whatsapp = WhatsAppClient(settings)

    def _push_whatsapp(self, state: CareState, body: str) -> dict:
        entry = {
            "at": utcnow().isoformat(),
            "to": state.elder.caregiver_phone or self.settings.daughter_wa_phone,
            "body": body,
            "delivered": False,
        }
        state.whatsapp_outbox.insert(0, entry)
        state.whatsapp_outbox = state.whatsapp_outbox[:50]
        phone = entry["to"]
        if self.whatsapp.configured and phone:
            try:
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    entry["note"] = "queued — deliver via async worker"
                else:
                    asyncio.run(self.whatsapp.send_text(phone, body))
                    entry["delivered"] = True
            except Exception as exc:
                logger.warning("WhatsApp send failed, keeping outbox: %s", exc)
                entry["error"] = str(exc)
        else:
            entry["note"] = "stub — configure WhatsApp keys to deliver"
        return entry

    def create_alert(
        self,
        state: CareState,
        *,
        type: AlertType,
        severity: AlertSeverity,
        message: str,
        message_darija: str = "",
        related_dose_id: str | None = None,
        notify_whatsapp: bool = True,
    ) -> Alert:
        alert = Alert(
            type=type,
            severity=severity,
            message=message,
            message_darija=message_darija,
            related_dose_id=related_dose_id,
        )
        state.alerts.insert(0, alert)
        if notify_whatsapp:
            wa_body = f"Bchkito — {state.elder.name}\n{message}"
            if message_darija:
                wa_body += f"\n{message_darija}"
            self._push_whatsapp(state, wa_body)
        return alert

    def mark_missed_if_overdue(self) -> CareState:
        def mutate(s: CareState) -> None:
            now = utcnow()
            grace = timedelta(minutes=s.elder.grace_minutes)
            for dose in s.doses:
                if dose.status != DoseStatus.REMINDED:
                    continue
                start = dose.reminded_at or dose.scheduled_at
                if now >= start + grace:
                    dose.status = DoseStatus.MISSED
                    dose.responded_at = now
                    dose.source = "timeout"
                    self.create_alert(
                        s,
                        type=AlertType.MISSED_DOSE,
                        severity=AlertSeverity.WARNING,
                        message=(
                            f"Missed dose: {dose.medication_name} "
                            f"scheduled {dose.scheduled_at.strftime('%H:%M')}"
                        ),
                        message_darija=(
                            f"ماما ماجاوبتش على دواء {dose.medication_name}"
                        ),
                        related_dose_id=dose.id,
                    )
                    if s.pending_dose_id == dose.id:
                        s.pending_dose_id = None

        return self.store.update(mutate)
