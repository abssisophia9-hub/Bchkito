from __future__ import annotations

from importlib import resources
from pathlib import Path


def load_prompt(*parts: str) -> str:
    """Load a prompt markdown file packaged under bchkito/prompts."""
    try:
        package = resources.files("bchkito.prompts")
        target = package
        for part in parts:
            target = target / part
        return target.read_text(encoding="utf-8")
    except (FileNotFoundError, TypeError, AttributeError):
        # Fallback for editable / source-tree runs
        base = Path(__file__).resolve().parent / "prompts"
        return (base.joinpath(*parts)).read_text(encoding="utf-8")
