from __future__ import annotations

import json
import threading
from pathlib import Path

from bchkito.care.models import CareState, seed_demo_state


class CareStore:
    """Simple JSON-backed store for the care prototype."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(seed_demo_state())

    def load(self) -> CareState:
        with self._lock:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return CareState.model_validate(raw)

    def save(self, state: CareState) -> None:
        with self._lock:
            self.path.write_text(
                state.model_dump_json(indent=2),
                encoding="utf-8",
            )

    def update(self, mutator) -> CareState:
        with self._lock:
            state = self.load()
            mutator(state)
            self.save(state)
            return state


_STORE: CareStore | None = None


def get_care_store(path: Path | None = None) -> CareStore:
    global _STORE
    if _STORE is None:
        _STORE = CareStore(path or Path("data/care_state.json"))
    return _STORE
