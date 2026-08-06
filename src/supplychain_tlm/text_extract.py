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
    field_confidence: dict[str, float]
    warnings: tuple[str, ...] = ()

    @property
    def needs_human_review(self) -> bool:
        return (
            self.document_type == "unknown"
            or self.confidence < 0.6
            or bool(self.warnings)
            or any(value < 0.8 for value in self.field_confidence.values())
        )


_TYPE_TERMS = {
    "invoice": ("invoice", "amount due", "invoice total", "statement number"),
    "purchase_order": ("purchase order", "po number", "po no"),
    "packing_list": ("packing list", "package count", "carton"),
    "bill_of_lading": ("bill of lading", "b/l", "container number", "vessel"),
}
_TYPE_PRIORITY = {"invoice": 2, "purchase_order": 3, "packing_list": 4, "bill_of_lading": 5}
_TEMPLATE_MARKERS = ("[business name]", "[invoice number]", "[address]", "fill in", "page x of x", "company name")


def classify_document(text: str) -> tuple[str, float]:
    normalized = text.lower()
    scores = {kind: sum(term in normalized for term in terms) for kind, terms in _TYPE_TERMS.items()}
    document_type, score = max(scores.items(), key=lambda item: (item[1], _TYPE_PRIORITY[item[0]]))
    if score == 0:
        return "unknown", 0.0
    return document_type, min(0.99, 0.55 + 0.12 * (score - 1))


def _first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_fields(text: str, document_type: str | None = None) -> ExtractionResult:
    kind, confidence = classify_document(text) if document_type is None else (document_type, 1.0)
    fields: dict[str, str] = {}
    field_confidence: dict[str, float] = {}
    patterns = {
        "document_id": r"(?:invoice\s*(?:number|no\.?|#)|document\s*(?:number|no\.?|id)|bol\s*(?:number|no\.?)|b/l\s*(?:number|no\.?)|statement\s*number)\s*[:#-]?\s*([A-Z0-9][A-Z0-9-]+)",
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
            field_confidence[name] = 0.9
    if fields.get("document_id", "").lower() in {"page", "total", "invoice", "name"}:
        fields.pop("document_id", None)
        field_confidence.pop("document_id", None)
    if kind == "invoice":
        statement_number = _first(r"statement\s+number\s*[:#-]?\s*([A-Z0-9][A-Z0-9-]+)", text)
        if statement_number:
            fields["document_id"] = statement_number.replace(",", "")
            field_confidence["document_id"] = 0.95
        payable = _first(r"total\s+payable\s*[:#-]?\s*[₹$€£]?\s*([0-9][0-9,]*(?:\.\d{1,2})?)", text)
        if payable:
            fields["total_amount"] = payable.replace(",", "")
            field_confidence["total_amount"] = 0.95
    normalized = text.lower()
    warnings_list = [] if fields else ["no supported fields found"]
    if any(marker in normalized for marker in _TEMPLATE_MARKERS):
        warnings_list.append("document contains template placeholders")
    if kind == "unknown":
        warnings_list.append("document type could not be classified")
    warnings = tuple(dict.fromkeys(warnings_list))
    return ExtractionResult(kind, confidence, fields, field_confidence, warnings)
