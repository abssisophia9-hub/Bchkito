from __future__ import annotations

from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid4().hex[:10]}"


class DoseStatus(str, Enum):
    PENDING = "pending"
    REMINDED = "reminded"
    TAKEN = "taken"
    MISSED = "missed"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


class AlertType(str, Enum):
    MISSED_DOSE = "missed_dose"
    SOS = "sos"
    NO_RESPONSE = "no_response"
    LOW_BATTERY = "low_battery"
    OFFLINE = "offline"
    GLUCOSE_DUE = "glucose_due"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Medication(BaseModel):
    id: str = Field(default_factory=lambda: new_id("med_"))
    name: str
    dose_label: str = ""
    route: Literal["oral", "insulin", "other"] = "oral"
    times: list[str] = Field(default_factory=list)  # "HH:MM" local
    notes: str = ""
    active: bool = True


class DoseEvent(BaseModel):
    id: str = Field(default_factory=lambda: new_id("dose_"))
    medication_id: str
    medication_name: str
    scheduled_at: datetime
    status: DoseStatus = DoseStatus.PENDING
    reminded_at: datetime | None = None
    responded_at: datetime | None = None
    source: Literal["voice", "caregiver", "timeout", "system"] = "system"
    note: str = ""


class GlucoseLog(BaseModel):
    id: str = Field(default_factory=lambda: new_id("glu_"))
    at: datetime = Field(default_factory=utcnow)
    value_mg_dl: float | None = None
    note: str = ""
    source: Literal["voice", "caregiver"] = "caregiver"


class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: new_id("apt_"))
    title: str
    at: datetime
    location: str = ""
    notes: str = ""


class Alert(BaseModel):
    id: str = Field(default_factory=lambda: new_id("al_"))
    type: AlertType
    severity: AlertSeverity = AlertSeverity.WARNING
    message: str
    message_darija: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    acked_at: datetime | None = None
    channel: Literal["whatsapp", "dashboard", "both"] = "both"
    related_dose_id: str | None = None


class ElderProfile(BaseModel):
    id: str = "elder_1"
    name: str = "لالة فاطمة"
    city: str = "Ifrane"
    timezone: str = "Africa/Casablanca"
    caregiver_name: str = "بنتي"
    caregiver_phone: str = ""
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"
    grace_minutes: int = 2
    pendant_battery: int = 86
    pendant_online: bool = True


class GameScore(BaseModel):
    id: str = Field(default_factory=lambda: new_id("game_"))
    at: datetime = Field(default_factory=utcnow)
    game: str
    correct: bool
    prompt: str
    answer: str = ""


class CareState(BaseModel):
    elder: ElderProfile = Field(default_factory=ElderProfile)
    medications: list[Medication] = Field(default_factory=list)
    doses: list[DoseEvent] = Field(default_factory=list)
    glucose: list[GlucoseLog] = Field(default_factory=list)
    appointments: list[Appointment] = Field(default_factory=list)
    alerts: list[Alert] = Field(default_factory=list)
    games: list[GameScore] = Field(default_factory=list)
    pending_dose_id: str | None = None
    pending_game_id: str | None = None
    pending_game_answer: str | None = None
    whatsapp_outbox: list[dict] = Field(default_factory=list)


def seed_demo_state() -> CareState:
    """Demo Moroccan Type-2 care scenario."""
    elder = ElderProfile(
        name="لالة فاطمة",
        city="Ifrane",
        caregiver_name="سارة",
        caregiver_phone="+212600000000",
    )
    meds = [
        Medication(
            id="med_metformin",
            name="ميتفورمين",
            dose_label="500 مغ",
            route="oral",
            times=["09:00", "21:00"],
            notes="بعد الأكل",
        ),
        Medication(
            id="med_insulin",
            name="إنسولين",
            dose_label="حسب وصفة الطبيب",
            route="insulin",
            times=["09:30", "19:30"],
            notes="تذكير فقط — الجرعة يقررها الطبيب/العائلة",
        ),
    ]
    today = date.today()
    doses: list[DoseEvent] = []
    # Seed today's schedule as pending/reminded samples
    for med in meds:
        for t in med.times:
            hh, mm = map(int, t.split(":"))
            scheduled = datetime.combine(today, time(hh, mm), tzinfo=timezone.utc)
            doses.append(
                DoseEvent(
                    medication_id=med.id,
                    medication_name=med.name,
                    scheduled_at=scheduled,
                    status=DoseStatus.PENDING,
                )
            )
    appts = [
        Appointment(
            title="موعد طبيب السكري",
            at=datetime.combine(today, time(11, 0), tzinfo=timezone.utc).replace(
                day=min(today.day + 3, 28)
            ),
            location="المستشفى الإقليمي",
            notes="جيبي دفتر السكر",
        )
    ]
    return CareState(elder=elder, medications=meds, doses=doses, appointments=appts)
