import unittest
import json
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from src.supplychain_tlm.extraction import OCRDocument, OCRPage
from src.supplychain_tlm.ocr_cli import main


class OCRCLITests(unittest.TestCase):
    def test_ocr_cli_reports_extracted_fields(self):
        fake = OCRDocument("invoice.png", (OCRPage(1, "Invoice # INV-1\nInvoice Total: USD 100"),))
        output = StringIO()
        with patch("src.supplychain_tlm.ocr_cli.TesseractProvider.extract", return_value=fake):
            with redirect_stdout(output):
                self.assertEqual(main(["invoice.png"]), 0)
        self.assertIn("document_type: invoice", output.getvalue())
        self.assertIn("needs_human_review: False", output.getvalue())

    def test_ocr_cli_json_includes_quality(self):
        fake = OCRDocument("invoice.png", (OCRPage(1, "Invoice # INV-1"),))
        output = StringIO()
        with patch("src.supplychain_tlm.ocr_cli.TesseractProvider.extract", return_value=fake):
            with redirect_stdout(output):
                self.assertEqual(main(["invoice.png", "--json"]), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["quality"]["pages"], 1)

    def test_strict_mode_blocks_uncertain_extraction(self):
        fake = OCRDocument("scan.png", (OCRPage(1, "unreadable"),))
        with patch("src.supplychain_tlm.ocr_cli.TesseractProvider.extract", return_value=fake):
            self.assertEqual(main(["scan.png", "--strict"]), 1)


if __name__ == "__main__":
    unittest.main()
