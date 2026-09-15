from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import feedparser
import httpx

from bchkito.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    title: str
    summary: str
    link: str
    guid: str
    source: str


class MoroccanRSS:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cache_path = settings.cache_dir / "news_cache.json"

    def _read_cache(self) -> list[NewsItem] | None:
        if not self.cache_path.exists():
            return None
        try:
            raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
            age_min = (time.time() - float(raw.get("ts", 0))) / 60.0
            if age_min > self.settings.news_cache_minutes:
                return None
            return [NewsItem(**item) for item in raw.get("items", [])]
        except Exception:
            return None

    def _write_cache(self, items: list[NewsItem]) -> None:
        payload = {
            "ts": time.time(),
            "items": [asdict(i) for i in items],
        }
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    async def latest(self, limit: int = 5) -> list[NewsItem]:
        cached = self._read_cache()
        if cached is not None:
            return cached[:limit]

        seen: set[str] = set()
        items: list[NewsItem] = []
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            for url in self.settings.rss_feed_list:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    feed = feedparser.parse(resp.text)
                except Exception as exc:
                    logger.warning("RSS fetch failed for %s: %s", url, exc)
                    continue
                source = feed.feed.get("title") or url
                for entry in feed.entries:
                    guid = str(
                        entry.get("id")
                        or entry.get("link")
                        or entry.get("title")
                        or ""
                    )
                    if not guid or guid in seen:
                        continue
                    seen.add(guid)
                    items.append(
                        NewsItem(
                            title=str(entry.get("title") or "").strip(),
                            summary=str(
                                entry.get("summary") or entry.get("description") or ""
                            ).strip(),
                            link=str(entry.get("link") or ""),
                            guid=guid,
                            source=str(source),
                        )
                    )
                    if len(items) >= max(limit * 3, 10):
                        break

        if items:
            self._write_cache(items)
        else:
            # Stale cache if any
            if self.cache_path.exists():
                try:
                    raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
                    return [NewsItem(**item) for item in raw.get("items", [])][:limit]
                except Exception:
                    pass
        return items[:limit]
