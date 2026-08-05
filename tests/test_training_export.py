import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.supplychain_tlm.dataset import load_jsonl
from src.supplychain_tlm.training_export import export_jsonl, to_chat_record


class TrainingExportTests(unittest.TestCase):
    def test_record_preserves_safety_metadata(self):
        example = load_jsonl("examples/training_tasks.jsonl")[0]
        record = to_chat_record(example)
        self.assertEqual(record["metadata"]["safety_label"], example.safety_label)
        self.assertEqual(record["messages"][-1]["content"], example.target)

    def test_export_writes_chat_jsonl(self):
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "train.jsonl"
            self.assertEqual(export_jsonl("examples/training_tasks.jsonl", destination), 3)
            records = [json.loads(line) for line in destination.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 3)
            self.assertEqual([message["role"] for message in records[0]["messages"]], ["system", "user", "assistant"])


if __name__ == "__main__":
    unittest.main()
