from __future__ import annotations

import random
from dataclasses import dataclass

from bchkito.care.models import GameScore, utcnow
from bchkito.care.store import CareStore

GAMES = [
    {
        "id": "numbers",
        "prompt": "لعبة سريعة: عاودي ورايا هاد الأرقام: ثلاثة، سبعة، واحد.",
        "answer_hints": ["3", "7", "1", "ثلاثة", "سبعة", "واحد"],
    },
    {
        "id": "proverb",
        "prompt": "كمّلي المثل: «اللي بكري…»",
        "answer_hints": ["بكري", "الله", "يرزق"],
    },
    {
        "id": "memory",
        "prompt": "شنو لون سماء؟ جاوب بجملة قصيرة.",
        "answer_hints": ["زرق", "زرقا", "أزرق", "سما"],
    },
    {
        "id": "family",
        "prompt": "قولي ليا سمية بنت وحدة من العائلة باش ننشّط الذاكرة.",
        "answer_hints": [],  # any answer ok
    },
]


@dataclass
class GameTurn:
    prompt: str
    game_id: str
    expected_hints: list[str]


class MindGames:
    def __init__(self, store: CareStore) -> None:
        self.store = store

    def start(self) -> GameTurn:
        game = random.choice(GAMES)

        def mutate(state) -> None:
            state.pending_game_id = game["id"]
            state.pending_game_answer = ",".join(game["answer_hints"])

        self.store.update(mutate)
        return GameTurn(
            prompt=f"واخا نلعبو شوية باش الدماغ يبقى صاحي. {game['prompt']}",
            game_id=game["id"],
            expected_hints=list(game["answer_hints"]),
        )

    def answer(self, text: str) -> str:
        state = self.store.load()
        if not state.pending_game_id:
            return "مابديناش لعبة. قولي «نلعبو» باش نبداو."

        hints = [
            h for h in (state.pending_game_answer or "").split(",") if h
        ]
        correct = True if not hints else any(h in text for h in hints)

        def mutate(s) -> None:
            s.games.insert(
                0,
                GameScore(
                    at=utcnow(),
                    game=s.pending_game_id or "unknown",
                    correct=correct,
                    prompt="",
                    answer=text[:80],
                ),
            )
            s.pending_game_id = None
            s.pending_game_answer = None

        self.store.update(mutate)
        if correct:
            return "أحسنتي! الدماغ ديالك صاحي. نعاودو مرة أخرى من بعد."
        return "ماشي مشكيل، المهم جرّبتي. المرة الجاية غادي تكون أحسن."
