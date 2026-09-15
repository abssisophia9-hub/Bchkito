from __future__ import annotations

from bchkito.config import Settings
from bchkito.prompts_loader import load_prompt
from bchkito.voice.llm_cloud import CloudLLM
from bchkito.voice.llm_local import LocalLLM


class ChatSkill:
    def __init__(
        self,
        settings: Settings,
        local_llm: LocalLLM,
        cloud_llm: CloudLLM,
    ) -> None:
        self.settings = settings
        self.local_llm = local_llm
        self.cloud_llm = cloud_llm
        self.skill_prompt = load_prompt("skills", "chat.md")

    async def reply(
        self,
        user_text: str,
        *,
        system_prompt: str,
        prefer_cloud: bool = False,
    ) -> tuple[str, bool]:
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n{self.skill_prompt}"},
            {"role": "user", "content": user_text},
        ]
        used_cloud = False
        text = ""
        if prefer_cloud and self.cloud_llm.available:
            text = await self.cloud_llm.chat(messages)
            used_cloud = bool(text)
        if not text:
            text = await self.local_llm.chat(messages)
        if not text and self.cloud_llm.available:
            text = await self.cloud_llm.chat(messages)
            used_cloud = bool(text)
        return text.strip(), used_cloud
