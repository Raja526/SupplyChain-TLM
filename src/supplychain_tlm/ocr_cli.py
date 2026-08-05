"""Run installed Tesseract and inspect extracted supply-chain fields."""

from __future__ import annotations

import argparse
import json

from .extraction import TesseractProvider
from .text_extract import extract_fields
from .ocr_quality import assess_ocr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OCR a supply-chain document and inspect extracted fields")
    parser.add_argument("path")
    parser.add_argument("--language", default="eng")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--strict", action="store_true", help="return failure when human review is required")
    args = parser.parse_args(argv)
    ocr = TesseractProvider(language=args.language, timeout_seconds=args.timeout).extract(args.path)
    result = extract_fields(ocr.text)
    quality = assess_ocr(ocr, result)
    if args.as_json:
        print(json.dumps({"source": ocr.source_path, "document_type": result.document_type, "confidence": result.confidence, "fields": result.fields, "quality": quality.__dict__}, sort_keys=True))
        return 1 if args.strict and quality.needs_human_review else 0
    print(f"source: {ocr.source_path}")
    print(f"document_type: {result.document_type}")
    print(f"confidence: {result.confidence:.2f}")
    print(f"fields: {result.fields}")
    print(f"needs_human_review: {result.needs_human_review}")
    print(f"ocr_pages: {quality.pages}")
    print(f"ocr_characters: {quality.character_count}")
    for warning in result.warnings:
        print(f"warning: {warning}")
    return 1 if args.strict and quality.needs_human_review else 0


if __name__ == "__main__":
    raise SystemExit(main())
