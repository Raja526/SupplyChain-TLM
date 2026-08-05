"""Unified OCR → extraction → human-review ingestion pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .extraction import OCRDocument, OCRProvider
from .review import ReviewItem, ReviewQueue
from .text_extract import ExtractionResult, extract_fields


@dataclass(frozen=True)
class IngestionResult:
    source: str
    ocr: OCRDocument
    extraction: ExtractionResult
    review_item: ReviewItem | None = None


def ingest_document(path: str | Path, provider: OCRProvider, review_queue: ReviewQueue | None = None) -> IngestionResult:
    ocr = provider.extract(path)
    extraction = extract_fields(ocr.text)
    review_item = review_queue.enqueue_extraction(str(path), extraction) if review_queue else None
    return IngestionResult(str(path), ocr, extraction, review_item)
