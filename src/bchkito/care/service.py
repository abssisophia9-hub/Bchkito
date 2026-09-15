from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from bchkito.care.alerts import AlertService
from bchkito.care.models import (
    AlertSeverity,
    AlertType,
    Appointment,
    CareState,
    DoseEvent,
    DoseStatus,
    GlucoseLog,
    Medication,
    utcnow,
)
from bchkito.care.store import CareStore
from bchkito.config import Settings

logger = logging.getLogger(__name__)

_TAKEN = re.compile(
    r"(خذيت|خديت|خدّيت|اخدت|أخذت|دريت|دارت|تم|واخا\s*خذيت|صافي)",
    re.IGNORECASE,
)
_SKIP = re.compile(r"(ماخذيتش|ما\s*خذيتش|نسيّت|نسيت|سكيپ|skip)", re.IGNORECASE)
_SOS = re.compile(
    r"(عيطي|عيّطي|نجدة|ساعدني|ما\s*بخير|طحت|سقطت|sos|مساعدة|بنتي\s*دغيا)",
    re.IGNORECASE,
)
_GLUCOSE = re.compile(r"(السكر|سكر|غلوكوز|glucose)", re.IGNORECASE)
_MED = re.compile(r"(الدوا|الدواء|إنسولين|انسولين|ميتفورمين|وجّه|وجبه)", re.IGNORECASE)


class CareService:
    def __init__(self, store: CareStore, settings: Settings) -> None:
        self.store = store
        self.settings = settings
        self.alerts = AlertService(store, settings)

    def snapshot(self) -> CareState:
        state = self.store.load()
        self.alerts.mark_missed_if_overdue()
        return self.store.load()

    def start_reminder(self, dose_id: str | None = None) -> tuple[str, DoseEvent | None]:
        def mutate(state: CareState) -> DoseEvent | None:
            target: DoseEvent | None = None
            if dose_id:
                target = next((d for d in state.doses if d.id == dose_id), None)
            if target is None:
                candidates = [
                    d
                    for d in state.doses
                    if d.status in {DoseStatus.PENDING, DoseStatus.REMINDED}
                ]
                candidates.sort(key=lambda d: d.scheduled_at)
                # Prefer overdue or due soon; else next pending today
                now = utcnow()
                due = [d for d in candidates if d.scheduled_at <= now + timedelta(hours=2)]
                target = (due or candidates or [None])[0]
            if target is None:
                return None
            target.status = DoseStatus.REMINDED
            target.reminded_at = utcnow()
            state.pending_dose_id = target.id
            return target

        dose_box: dict[str, DoseEvent | None] = {"d": None}

        def _m(state: CareState) -> None:
            dose_box["d"] = mutate(state)

        self.store.update(_m)
        dose = dose_box["d"]
        if dose is None:
            return "ماكاينش دوا مبرمج دابا. ارتاحي.", None
        hh = dose.scheduled_at.strftime("%H:%M")
        route = ""
        state = self.store.load()
        med = next((m for m in state.medications if m.id == dose.medication_id), None)
        if med and med.route == "insulin":
            route = "الإنسولين"
        else:
            route = dose.medication_name
        reply = (
            f"السلام عليكم، دابا الوقت ديال {route}"
            f"{(' — ' + dose.medication_name) if route != dose.medication_name else ''}. "
            f"الساعة {hh}. إيوا، منين تاخديه قولي ليا: خذيت الدوا."
        )
        return reply, dose

    def handle_med_response(self, text: str) -> str:
        state = self.store.load()
        pending_id = state.pending_dose_id
        if not pending_id:
            # Try to attach to latest reminded
            reminded = [
                d for d in state.doses if d.status == DoseStatus.REMINDED
            ]
            if reminded:
                pending_id = sorted(reminded, key=lambda d: d.reminded_at or d.scheduled_at)[
                    -1
                ].id

        if not pending_id:
            return "ماكاينش تذكير دابا. إلا بغيتي، قولي «وقت الدوا»."

        if _SKIP.search(text):
            return self._set_dose(pending_id, DoseStatus.SKIPPED, text)

        if _TAKEN.search(text) or text.strip() in {"نعم", "واخا", "اه", "آه"}:
            return self._set_dose(pending_id, DoseStatus.TAKEN, text)

        return (
            "مافهمتش مزيان. قولي «خذيت الدوا» إلا خديتيه، "
            "ولا «ماخذيتش» إلا باقي."
        )

    def _set_dose(self, dose_id: str, status: DoseStatus, note: str) -> str:
        def mutate(state: CareState) -> None:
            dose = next((d for d in state.doses if d.id == dose_id), None)
            if not dose:
                return
            dose.status = status
            dose.responded_at = utcnow()
            dose.source = "voice"
            dose.note = note[:120]
            if state.pending_dose_id == dose_id:
                state.pending_dose_id = None
            if status == DoseStatus.SKIPPED:
                self.alerts.create_alert(
                    state,
                    type=AlertType.MISSED_DOSE,
                    severity=AlertSeverity.INFO,
                    message=f"Skipped: {dose.medication_name}",
                    message_darija=f"قالت ماما ماخذاتش {dose.medication_name}",
                    related_dose_id=dose.id,
                )

        self.store.update(mutate)
        if status == DoseStatus.TAKEN:
            return "بارك الله فيك، سجّلت أنك خذيتي الدوا. الله يعطيك الصحة."
        if status == DoseStatus.SKIPPED:
            return "واخا، سجّلت. غنقولو للعائلة باش يعاونوك."
        return "تم التسجيل."

    def trigger_sos(self, text: str = "") -> str:
        def mutate(state: CareState) -> None:
            self.alerts.create_alert(
                state,
                type=AlertType.SOS,
                severity=AlertSeverity.CRITICAL,
                message=f"SOS from {state.elder.name}. Utterance: {text or 'button'}",
                message_darija=(
                    f"🚨 نجدة: {state.elder.name} طلبات المساعدة. "
                    f"اتصلي بها دابا."
                ),
            )

        self.store.update(mutate)
        return "واخا، غنقولو لعائلتك دابا. بقى معايا، المساعدة غادية تجي."

    def log_glucose(self, value: float | None, note: str = "") -> str:
        def mutate(state: CareState) -> None:
            state.glucose.insert(
                0,
                GlucoseLog(value_mg_dl=value, note=note, source="voice"),
            )

        self.store.update(mutate)
        if value is not None:
            return f"سجّلت السكر: {value:.0f}. الله يعطيك الصحة."
        return "سجّلت أنك قستي السكر. إلا عندك الرقم، قوّليه ليا."

    def compliance_today(self) -> dict:
        state = self.snapshot()
        today = utcnow().date()
        todays = [d for d in state.doses if d.scheduled_at.date() == today]
        counts = {s.value: 0 for s in DoseStatus}
        for d in todays:
            counts[d.status.value] += 1
        return {
            "total": len(todays),
            "counts": counts,
            "doses": [d.model_dump(mode="json") for d in todays],
        }

    def upsert_medication(self, payload: dict) -> Medication:
        med = Medication.model_validate(payload)

        def mutate(state: CareState) -> None:
            existing = next((m for m in state.medications if m.id == med.id), None)
            if existing:
                idx = state.medications.index(existing)
                state.medications[idx] = med
            else:
                state.medications.append(med)

        self.store.update(mutate)
        return med

    def add_appointment(self, payload: dict) -> Appointment:
        apt = Appointment.model_validate(payload)

        def mutate(state: CareState) -> None:
            state.appointments.append(apt)

        self.store.update(mutate)
        return apt

    def caregiver_mark_dose(self, dose_id: str, status: str) -> DoseEvent | None:
        st = DoseStatus(status)
        box: dict[str, DoseEvent | None] = {"d": None}

        def mutate(state: CareState) -> None:
            dose = next((d for d in state.doses if d.id == dose_id), None)
            if not dose:
                return
            dose.status = st
            dose.responded_at = utcnow()
            dose.source = "caregiver"
            if state.pending_dose_id == dose_id:
                state.pending_dose_id = None
            box["d"] = dose

        self.store.update(mutate)
        return box["d"]

    def ack_alert(self, alert_id: str) -> None:
        def mutate(state: CareState) -> None:
            for a in state.alerts:
                if a.id == alert_id:
                    a.acked_at = utcnow()

        self.store.update(mutate)

    def force_due_for_demo(self) -> DoseEvent | None:
        """Mark nearest pending dose as due now (prototype button)."""
        box: dict[str, DoseEvent | None] = {"d": None}

        def mutate(state: CareState) -> None:
            pending = [d for d in state.doses if d.status == DoseStatus.PENDING]
            if not pending:
                # reset one taken/missed for demo
                for d in state.doses:
                    d.status = DoseStatus.PENDING
                    d.reminded_at = None
                    d.responded_at = None
                pending = list(state.doses)
            if not pending:
                return
            dose = sorted(pending, key=lambda d: d.scheduled_at)[0]
            dose.scheduled_at = utcnow() - timedelta(minutes=1)
            dose.status = DoseStatus.PENDING
            box["d"] = dose

        self.store.update(mutate)
        return box["d"]


def extract_glucose_value(text: str) -> float | None:
    m = re.search(r"(\d{2,3})", text)
    if not m:
        return None
    val = float(m.group(1))
    if 40 <= val <= 600:
        return val
    return None
