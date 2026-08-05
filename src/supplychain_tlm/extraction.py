"""Interfaces for OCR and document extraction providers.

The project does not bundle an OCR engine. Providers can implement this small
interface around Tesseract, a service API, or a future local CPU model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Protocol


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
