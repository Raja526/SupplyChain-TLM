"""Small deterministic baseline for classifying and extracting OCR text.

This is a development aid. Production extraction should add layout awareness,
confidence calibration, provenance, and human review for uncertain fields.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ExtractionResult:
    document_type: str
    confidence: float
    fields: dict[str, str]
    warnings: tuple[str, ...] = ()


_TYPE_TERMS = {
    "invoice": ("invoice", "amount due", "invoice total"),
    "purchase_order": ("purchase order", "po number", "po no"),
    "packing_list": ("packing list", "package count", "carton"),
    "bill_of_lading": ("bill of lading", "b/l", "container number", "vessel"),
}


def classify_document(text: str) -> tuple[str, float]:
    normalized = text.lower()
    scores = {kind: sum(term in normalized for term in terms) for kind, terms in _TYPE_TERMS.items()}
    document_type, score = max(scores.items(), key=lambda item: (item[1], item[0]))
    if score == 0:
        return "unknown", 0.0
    return document_type, min(0.99, 0.55 + 0.12 * (score - 1))


def _first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_fields(text: str, document_type: str | None = None) -> ExtractionResult:
    kind, confidence = classify_document(text) if document_type is None else (document_type, 1.0)
    fields: dict[str, str] = {}
    patterns = {
        "document_id": r"(?:invoice|document|bol|b/l)\s*(?:number|no\.?|#|id)?\s*[:#-]?\s*([A-Z0-9][A-Z0-9-]+)",
        "po_number": r"(?:purchase order|po)\s*(?:number|no\.?|#)?\s*[:#-]?\s*(PO[-\s]?[A-Z0-9-]+)",
        "shipment_id": r"(?:shipment|booking)\s*(?:id|number|no\.?)?\s*[:#-]?\s*(SHIP[-\s]?[A-Z0-9-]+)",
        "currency": r"\b(USD|EUR|GBP|INR)\b",
        "total_amount": r"(?:total|amount due)\s*[:#-]?\s*[$€£₹]?\s*([0-9][0-9,]*(?:\.\d{1,2})?)",
        "container_number": r"(?:container number|container no\.?|container)\s*[:#-]?\s*([A-Z]{4}\d{7})",
    }
    for name, pattern in patterns.items():
        value = _first(pattern, text)
        if value:
            fields[name] = value.replace(",", "")
    warnings = () if fields else ("no supported fields found",)
    if kind == "unknown":
        warnings += ("document type could not be classified",)
    return ExtractionResult(kind, confidence, fields, warnings)
