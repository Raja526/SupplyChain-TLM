import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from src.supplychain_tlm.review import ReviewQueue
from src.supplychain_tlm.text_extract import extract_fields


class ReviewQueueTests(unittest.TestCase):
    def test_uncertain_extraction_is_queued_and_resolved(self):
        with TemporaryDirectory() as directory:
            queue = ReviewQueue(Path(directory) / "review.jsonl")
            item = queue.enqueue_extraction("invoice-1.pdf", extract_fields("unreadable text"))
            self.assertIsNotNone(item)
            duplicate = queue.enqueue_extraction("invoice-1.pdf", extract_fields("unreadable text"))
            self.assertEqual(duplicate.item_id, item.item_id)
            self.assertEqual(len(queue.open_items()), 1)
            resolved = queue.resolve(item.item_id, "analyst-1", "corrected_fields")
            self.assertEqual(resolved.status, "resolved")
            self.assertEqual(queue.open_items(), ())

    def test_confident_extraction_needs_no_review(self):
        with TemporaryDirectory() as directory:
            queue = ReviewQueue(Path(directory) / "review.jsonl")
            item = queue.enqueue_extraction("bol-1.pdf", extract_fields("Bill of Lading\nShipment ID: SHIP-1\nContainer Number: MSCU1234567"))
            self.assertIsNone(item)


if __name__ == "__main__":
    unittest.main()
