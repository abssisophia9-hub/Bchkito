from bchkito.skills.router import Intent, SkillRouter


def test_router_weather():
    r = SkillRouter()
    assert r.route("كيفاش الجو فإفران") == Intent.WEATHER
    assert r.route("شحال فالطقس") == Intent.WEATHER


def test_router_news_and_morning():
    r = SkillRouter()
    assert r.route("شنو فالأخبار") == Intent.NEWS
    assert r.route("صباح الخير") == Intent.MORNING


def test_router_whatsapp_and_confirm():
    r = SkillRouter()
    assert r.route("صيفط ل بنتي راني بخير") == Intent.WHATSAPP_SEND
    assert r.route("نعم", pending_whatsapp=True) == Intent.CONFIRM
    assert r.route("لا", pending_whatsapp=True) == Intent.CANCEL
    assert r.route("لا ما تصيفطش", pending_whatsapp=True) == Intent.CANCEL
    assert r.route("كيفاش الجو فإفران", pending_whatsapp=True) == Intent.WEATHER


def test_router_chat_fallback():
    r = SkillRouter()
    assert r.route("بغيت نشرب أتاي") == Intent.CHAT
