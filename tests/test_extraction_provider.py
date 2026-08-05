import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.supplychain_tlm.extraction import OCRPage, OCRDocument, TesseractProvider


class ExtractionProviderTests(unittest.TestCase):
    def test_tesseract_command_returns_ocr_document(self):
        completed = type("Completed", (), {"returncode": 0, "stdout": "Invoice # INV-1", "stderr": ""})()
        with patch("src.supplychain_tlm.extraction.subprocess.run", return_value=completed) as run:
            result = TesseractProvider().extract(Path("invoice.png"))
        run.assert_called_once_with(("tesseract", "invoice.png", "stdout", "-l", "eng"), capture_output=True, text=True, timeout=120.0, check=False)
        self.assertEqual(result.pages, (OCRPage(1, "Invoice # INV-1"),))

    def test_tesseract_failure_is_reported(self):
        completed = type("Completed", (), {"returncode": 1, "stdout": "", "stderr": "bad image"})()
        with patch("src.supplychain_tlm.extraction.subprocess.run", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "bad image"):
                TesseractProvider().extract("invoice.png")


if __name__ == "__main__":
    unittest.main()
