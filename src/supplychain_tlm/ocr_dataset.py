"""Manifest validation for annotated OCR training and evaluation documents."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


DOCUMENT_TYPES = frozenset({"invoice", "purchase_order", "packing_list", "bill_of_lading"})
SPLITS = frozenset({"train", "validation", "test"})


@dataclass(frozen=True)
class OCRDatasetItem:
    item_id: str
    path: str
    document_type: str
    split: str
    fields: dict[str, Any]


def load_manifest(path: str | Path, *, root: str | Path | None = None) -> tuple[OCRDatasetItem, ...]:
    manifest = Path(path)
    base = Path(root) if root else manifest.parent
    items: list[OCRDatasetItem] = []
    seen: set[str] = set()
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            item_id = str(data["item_id"]).strip()
            relative_path = str(data["path"]).strip()
            document_type = str(data["document_type"]).strip()
            split = str(data["split"]).strip()
            fields = data.get("fields", {})
            if not item_id or not relative_path:
                raise ValueError("item_id and path cannot be empty")
            if item_id in seen:
                raise ValueError(f"duplicate item_id: {item_id}")
            if document_type not in DOCUMENT_TYPES:
                raise ValueError(f"unsupported document_type: {document_type}")
            if split not in SPLITS:
                raise ValueError(f"unsupported split: {split}")
            if not isinstance(fields, dict):
                raise ValueError("fields must be an object")
            resolved = (base / relative_path).resolve()
            if not resolved.is_file():
                raise ValueError(f"document file not found: {relative_path}")
        except (KeyError, json.JSONDecodeError, ValueError) as error:
            raise ValueError(f"invalid OCR manifest at line {line_number}: {error}") from error
        seen.add(item_id)
        items.append(OCRDatasetItem(item_id, relative_path, document_type, split, fields))
    if not items:
        raise ValueError("OCR manifest is empty")
    return tuple(items)
