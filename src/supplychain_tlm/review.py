"""Durable human-review queue for uncertain documents and decisions."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
import uuid

from .text_extract import ExtractionResult


@dataclass(frozen=True)
class ReviewItem:
    item_id: str
    source: str
    reason: str
    status: str = "open"
    reviewer: str = ""
    decision: str = ""


class ReviewQueue:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _write(self, item: ReviewItem) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(item), sort_keys=True) + "\n")

    def _latest(self) -> dict[str, ReviewItem]:
        latest: dict[str, ReviewItem] = {}
        if not self.path.exists():
            return latest
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = ReviewItem(**json.loads(line))
                latest[item.item_id] = item
        return latest

    def enqueue(self, source: str, reason: str) -> ReviewItem:
        for existing in self._latest().values():
            if existing.status == "open" and existing.source == source:
                return existing
        item = ReviewItem(str(uuid.uuid4()), source, reason)
        self._write(item)
        return item

    def enqueue_extraction(self, source: str, result: ExtractionResult) -> ReviewItem | None:
        if not result.needs_human_review:
            return None
        reason = "; ".join(result.warnings) or "low-confidence extraction"
        return self.enqueue(source, reason)

    def resolve(self, item_id: str, reviewer: str, decision: str) -> ReviewItem:
        item = self._latest().get(item_id)
        if item is None:
            raise KeyError(f"review item not found: {item_id}")
        resolved = ReviewItem(item.item_id, item.source, item.reason, "resolved", reviewer, decision)
        self._write(resolved)
        return resolved

    def open_items(self) -> tuple[ReviewItem, ...]:
        return tuple(item for item in self._latest().values() if item.status == "open")
