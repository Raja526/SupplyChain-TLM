"""Interfaces for OCR and document extraction providers.

The project does not bundle an OCR engine. Providers can implement this small
interface around Tesseract, a service API, or a future local CPU model.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any, Protocol


@dataclass(frozen=True)
class OCRPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class OCRDocument:
    source_path: str
    pages: tuple[OCRPage, ...]

    @property
    def text(self) -> str:
        return "\n".join(page.text for page in self.pages)


class OCRProvider(Protocol):
    def extract(self, path: str | Path) -> OCRDocument:
        """Return OCR text with page provenance for one source document."""


class PlainTextProvider:
    """Development provider for already-extracted text files."""

    def extract(self, path: str | Path) -> OCRDocument:
        source = Path(path)
        text = source.read_text(encoding="utf-8")
        return OCRDocument(str(source), (OCRPage(1, text),))


@dataclass(frozen=True)
class TesseractProvider:
    """Optional Tesseract adapter; requires the `tesseract` executable."""

    executable: str = "tesseract"
    language: str = "eng"
    timeout_seconds: float = 120.0

    def extract(self, path: str | Path) -> OCRDocument:
        source = Path(path)
        command = (self.executable, str(source), "stdout", "-l", self.language)
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=self.timeout_seconds, check=False)
        except FileNotFoundError as error:
            raise RuntimeError("Tesseract is not installed or is not on PATH") from error
        except subprocess.TimeoutExpired as error:
            raise TimeoutError(f"OCR timed out after {self.timeout_seconds}s") from error
        if completed.returncode != 0:
            detail = completed.stderr.strip() or f"exit code {completed.returncode}"
            raise RuntimeError(f"Tesseract OCR failed: {detail}")
        return OCRDocument(str(source), (OCRPage(1, completed.stdout),))


@dataclass
class PaddleOCRProvider:
    """Optional local PaddleOCR adapter using the current ``predict`` API.

    PaddleOCR is imported lazily so the core project remains installable
    without the large OCR runtime. A test double can be supplied through
    ``ocr``; production callers normally leave it as ``None``.
    """

    ocr: Any | None = None
    language: str = "en"

    def _engine(self) -> Any:
        if self.ocr is not None:
            return self.ocr
        try:
            from paddleocr import PaddleOCR
        except ImportError as error:
            raise RuntimeError("PaddleOCR is not installed; install it to use PaddleOCRProvider") from error
        self.ocr = PaddleOCR(
            lang=self.language,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        return self.ocr

    @staticmethod
    def _payload(result: Any) -> Any:
        value = getattr(result, "json", None)
        if callable(value):
            value = value()
        if value is None:
            value = result
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {"text": value}
        return value

    @classmethod
    def _text(cls, result: Any) -> str:
        payload = cls._payload(result)
        if isinstance(payload, dict) and isinstance(payload.get("res"), dict):
            payload = payload["res"]
        if isinstance(payload, dict):
            for key in ("rec_texts", "texts", "text"):
                value = payload.get(key)
                if isinstance(value, (list, tuple)):
                    return "\n".join(str(item) for item in value if str(item).strip())
                if isinstance(value, str):
                    return value
        return str(payload) if isinstance(payload, str) else ""

    def extract(self, path: str | Path) -> OCRDocument:
        source = Path(path)
        results = self._engine().predict(str(source))
        pages = tuple(OCRPage(index, self._text(result)) for index, result in enumerate(results, start=1))
        return OCRDocument(str(source), pages)
