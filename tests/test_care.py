from bchkito.care.models import DoseStatus
from bchkito.care.service import CareService, extract_glucose_value
from bchkito.care.store import CareStore
from bchkito.config import Settings
from bchkito.skills.router import Intent, SkillRouter


def test_router_care_intents():
    r = SkillRouter()
    assert r.route("عيطي لبنتي") == Intent.SOS
    assert r.route("وقت الدوا") == Intent.MED_REMINDER
    assert r.route("خذيت الدوا") == Intent.MED_RESPONSE
    assert r.route("نلعبو") == Intent.GAME
    assert r.route("قسيت السكر") == Intent.GLUCOSE
    assert r.route("ثلاثة سبعة", pending_game=True) == Intent.GAME_ANSWER


def test_med_taken_flow(tmp_path):
    settings = Settings(cache_dir=tmp_path, log_dir=tmp_path / "logs")
    store = CareStore(tmp_path / "care.json")
    care = CareService(store, settings)
    reply, dose = care.start_reminder()
    assert dose is not None
    assert "الدوا" in reply or "إنسولين" in reply or "ميتفورمين" in reply
    confirm = care.handle_med_response("خذيت الدوا")
    assert "سجّلت" in confirm
    state = store.load()
    updated = next(d for d in state.doses if d.id == dose.id)
    assert updated.status == DoseStatus.TAKEN


def test_sos_creates_whatsapp_outbox(tmp_path):
    settings = Settings(cache_dir=tmp_path, log_dir=tmp_path / "logs")
    store = CareStore(tmp_path / "care.json")
    care = CareService(store, settings)
    reply = care.trigger_sos("طحت")
    assert "عائلتك" in reply or "نقولو" in reply
    state = store.load()
    assert state.alerts
    assert state.alerts[0].type.value == "sos"
    assert state.whatsapp_outbox


def test_extract_glucose():
    assert extract_glucose_value("السكر 140") == 140.0
    assert extract_glucose_value("مرحبا") is None
