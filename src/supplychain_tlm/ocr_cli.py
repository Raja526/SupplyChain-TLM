"""Run installed Tesseract and inspect extracted supply-chain fields."""

from __future__ import annotations

import argparse

from .extraction import TesseractProvider
from .text_extract import extract_fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OCR a supply-chain document and inspect extracted fields")
    parser.add_argument("path")
    parser.add_argument("--language", default="eng")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    ocr = TesseractProvider(language=args.language, timeout_seconds=args.timeout).extract(args.path)
    result = extract_fields(ocr.text)
    print(f"source: {ocr.source_path}")
    print(f"document_type: {result.document_type}")
    print(f"confidence: {result.confidence:.2f}")
    print(f"fields: {result.fields}")
    print(f"needs_human_review: {result.needs_human_review}")
    for warning in result.warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
