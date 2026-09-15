from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np

from bchkito.audio.playback import play_earcon, play_wav
from bchkito.audio.vad import trim_silence
from bchkito.config import Settings
from bchkito.prompts_loader import load_prompt
from bchkito.skills.chat import ChatSkill
from bchkito.skills.family_bridge import FamilyBridgeSkill
from bchkito.skills.info_hub import InfoHubSkill
from bchkito.skills.router import Intent, SkillRouter
from bchkito.voice.llm_cloud import CloudLLM
from bchkito.voice.llm_local import LocalLLM
from bchkito.voice.stt_whisper import Transcript, WhisperSTT
from bchkito.voice.tts_cloud import CloudTTS
from bchkito.voice.tts_local import LocalTTS

logger = logging.getLogger(__name__)


class VoiceState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


@dataclass
class TurnResult:
    transcript: str
    intent: Intent
    reply: str
    audio_path: Path | None
    latency_s: float
    used_cloud_llm: bool
    tts_tier: str


class VoicePipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.state = VoiceState.IDLE
        self.stt = WhisperSTT(settings)
        self.local_llm = LocalLLM(settings)
        self.cloud_llm = CloudLLM(settings)
        self.tts_local = LocalTTS(settings)
        self.tts_cloud = CloudTTS(settings)
        self.router = SkillRouter()
        self.chat = ChatSkill(settings, self.local_llm, self.cloud_llm)
        self.info_hub = InfoHubSkill(settings, self.local_llm, self.cloud_llm)
        self.family = FamilyBridgeSkill(
            settings, self.local_llm, self.cloud_llm, self.tts_cloud, self.tts_local
        )
        self._pending_whatsapp: str | None = None
        self.system_prompt = load_prompt("darija_system.md")

    async def handle_audio(self, audio: np.ndarray, *, speak: bool = True) -> TurnResult:
        started = time.perf_counter()
        self.state = VoiceState.THINKING
        play_earcon(self.settings, "thinking")

        trimmed = trim_silence(audio, self.settings.sample_rate)
        transcript = self.stt.transcribe(trimmed)
        return await self.handle_transcript(transcript, speak=speak, started=started)

    async def handle_transcript(
        self,
        transcript: Transcript | str,
        *,
        speak: bool = True,
        started: float | None = None,
    ) -> TurnResult:
        started = started or time.perf_counter()
        self.state = VoiceState.THINKING
        if isinstance(transcript, str):
            transcript = Transcript(text=transcript)

        text = transcript.text.strip()
        intent = self.router.route(text, pending_whatsapp=bool(self._pending_whatsapp))
        logger.info("Intent=%s transcript=%s", intent.value, text)

        used_cloud = False
        reply = ""
        tts_tier = self.settings.tts_default_tier

        if not text:
            reply = "ماسمعتش مزيان، عاود من فضلك."
        elif intent == Intent.CONFIRM and self._pending_whatsapp:
            reply, used_cloud = await self.family.send_pending(self._pending_whatsapp)
            self._pending_whatsapp = None
            tts_tier = "elevenlabs" if self.settings.whatsapp_default_mode == "voice" else "azure"
        elif intent == Intent.CANCEL and self._pending_whatsapp:
            self._pending_whatsapp = None
            reply = "واخا، ماصيفطتش الرسالة."
        elif intent == Intent.WHATSAPP_SEND:
            draft = self.family.extract_message(text)
            self._pending_whatsapp = draft
            reply = (
                f"واخا، غنصيفط لـ {self.settings.daughter_name}: "
                f"«{draft}». إيوا، نقولو نعم؟"
            )
            tts_tier = "azure"
        elif intent in {Intent.WEATHER, Intent.NEWS, Intent.MORNING, Intent.CHAT}:
            # Drop stale WhatsApp draft if user switched topics
            self._pending_whatsapp = None
            if intent == Intent.WEATHER:
                reply, used_cloud = await self.info_hub.weather(text)
            elif intent == Intent.NEWS:
                reply, used_cloud = await self.info_hub.news(prefer_cloud=True)
            elif intent == Intent.MORNING:
                weather, _ = await self.info_hub.weather(text)
                news, news_cloud = await self.info_hub.news(
                    prefer_cloud=True, max_items=1
                )
                reply = f"{weather} {news}".strip()
                used_cloud = news_cloud
            else:
                prefer_cloud = transcript.low_confidence
                reply, used_cloud = await self.chat.reply(
                    text,
                    system_prompt=self.system_prompt,
                    prefer_cloud=prefer_cloud,
                )
                if not reply:
                    reply = "سمح ليا، ماقدرش نجاوب دابا. جرب مرة أخرى."
        else:
            reply = "سمح ليا، ماقدرتش نفهم. عاود من فضلك."

        if transcript.low_confidence and intent == Intent.CHAT and text:
            # Soft confirmation style for weak STT
            reply = f"فهمت: {text}. {reply}"

        audio_path = await self.speak(reply, tier=tts_tier) if speak else None
        self.state = VoiceState.IDLE
        latency = time.perf_counter() - started
        logger.info(
            "Turn done intent=%s latency=%.2fs cloud_llm=%s",
            intent.value,
            latency,
            used_cloud,
        )
        return TurnResult(
            transcript=text,
            intent=intent,
            reply=reply,
            audio_path=audio_path,
            latency_s=latency,
            used_cloud_llm=used_cloud,
            tts_tier=tts_tier,
        )

    async def speak(self, text: str, *, tier: str | None = None) -> Path | None:
        self.state = VoiceState.SPEAKING
        tier = tier or self.settings.tts_default_tier
        path: Path | None = None

        if tier in {"azure", "elevenlabs"}:
            path = await self.tts_cloud.synthesize(text, tier=tier)
        if path is None:
            path = await self.tts_local.synthesize(text)

        try:
            if path and path.suffix.lower() in {".wav", ".wave"}:
                play_wav(path)
            elif path:
                logger.info("Non-WAV audio ready at %s (playback skipped)", path)
        except Exception as exc:
            logger.warning("Playback failed: %s", exc)
        return path
