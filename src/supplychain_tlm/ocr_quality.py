"""Quality metrics for OCR output and downstream field extraction."""

from __future__ import annotations

from dataclasses import dataclass

from .extraction import OCRDocument
from .text_extract import ExtractionResult


@dataclass(frozen=True)
class OCRQualityReport:
    source_path: str
    pages: int
    empty_pages: int
    character_count: int
    extraction_confidence: float
    needs_human_review: bool
    warnings: tuple[str, ...]

    @property
    def usable(self) -> bool:
        return self.pages > 0 and self.character_count > 0 and not self.empty_pages


def assess_ocr(document: OCRDocument, extraction: ExtractionResult) -> OCRQualityReport:
    page_lengths = tuple(len(page.text.strip()) for page in document.pages)
    warnings = list(extraction.warnings)
    if not document.pages:
        warnings.append("OCR returned no pages")
    if any(length == 0 for length in page_lengths):
        warnings.append("OCR returned one or more empty pages")
    return OCRQualityReport(
        source_path=document.source_path,
        pages=len(document.pages),
        empty_pages=sum(length == 0 for length in page_lengths),
        character_count=sum(page_lengths),
        extraction_confidence=extraction.confidence,
        needs_human_review=extraction.needs_human_review or bool(warnings),
        warnings=tuple(dict.fromkeys(warnings)),
    )
