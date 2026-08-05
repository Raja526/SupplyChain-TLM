import unittest

from src.supplychain_tlm.extraction import OCRDocument, OCRPage
from src.supplychain_tlm.ocr_quality import assess_ocr
from src.supplychain_tlm.text_extract import extract_fields


class OCRQualityTests(unittest.TestCase):
    def test_nonempty_document_is_usable(self):
        document = OCRDocument("invoice.txt", (OCRPage(1, "Invoice # INV-1"),))
        report = assess_ocr(document, extract_fields(document.text))
        self.assertTrue(report.usable)
        self.assertFalse(report.needs_human_review)

    def test_empty_page_requires_review(self):
        document = OCRDocument("scan.pdf", (OCRPage(1, ""), OCRPage(2, "Invoice")))
        report = assess_ocr(document, extract_fields(document.text))
        self.assertEqual(report.empty_pages, 1)
        self.assertFalse(report.usable)
        self.assertTrue(report.needs_human_review)
        self.assertIn("empty pages", " ".join(report.warnings))


if __name__ == "__main__":
    unittest.main()
