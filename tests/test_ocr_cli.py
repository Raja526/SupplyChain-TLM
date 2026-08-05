import unittest
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


if __name__ == "__main__":
    unittest.main()
