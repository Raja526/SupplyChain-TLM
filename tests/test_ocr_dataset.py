import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.supplychain_tlm.ocr_dataset import load_manifest


class OCRDatasetTests(unittest.TestCase):
    def test_manifest_validates_files_and_annotations(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "invoice.txt").write_text("Invoice # INV-1", encoding="utf-8")
            manifest = root / "manifest.jsonl"
            manifest.write_text(json.dumps({"item_id": "i-1", "path": "invoice.txt", "document_type": "invoice", "split": "train", "fields": {"document_id": "INV-1"}}) + "\n", encoding="utf-8")
            items = load_manifest(manifest)
            self.assertEqual(items[0].document_type, "invoice")

    def test_missing_document_is_rejected(self):
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.jsonl"
            manifest.write_text(json.dumps({"item_id": "i-1", "path": "missing.pdf", "document_type": "invoice", "split": "train"}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "file not found"):
                load_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
