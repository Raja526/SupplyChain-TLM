import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.supplychain_tlm.extraction import OCRDocument, OCRPage
from src.supplychain_tlm.ingestion_pipeline import ingest_document
from src.supplychain_tlm.review import ReviewQueue


class FakeProvider:
    def __init__(self, text):
        self.text = text

    def extract(self, path):
        return OCRDocument(str(path), (OCRPage(1, self.text),))


class IngestionPipelineTests(unittest.TestCase):
    def test_confident_document_does_not_enter_review(self):
        with TemporaryDirectory() as directory:
            result = ingest_document("invoice.png", FakeProvider("Invoice # INV-1\nInvoice Total: USD 100"), ReviewQueue(Path(directory) / "review.jsonl"))
            self.assertEqual(result.extraction.document_type, "invoice")
            self.assertIsNone(result.review_item)

    def test_uncertain_document_enters_review(self):
        with TemporaryDirectory() as directory:
            queue = ReviewQueue(Path(directory) / "review.jsonl")
            result = ingest_document("unknown.png", FakeProvider("unreadable text"), queue)
            self.assertIsNotNone(result.review_item)
            self.assertEqual(len(queue.open_items()), 1)


if __name__ == "__main__":
    unittest.main()
