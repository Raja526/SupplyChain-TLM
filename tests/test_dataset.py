import unittest
from tempfile import NamedTemporaryFile

from src.supplychain_tlm.dataset import example_from_dict, load_jsonl


class DatasetTests(unittest.TestCase):
    def test_sample_jsonl_loads(self):
        examples = load_jsonl("examples/training_tasks.jsonl")
        self.assertEqual(len(examples), 3)
        self.assertEqual(examples[2].safety_label, "refuse_action")

    def test_invalid_safety_label_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported safety label"):
            example_from_dict({"example_id": "x", "domain": "shipping", "instruction": "x", "context": {}, "target": "x", "safety_label": "execute"})

    def test_duplicate_ids_are_rejected(self):
        content = '{"example_id":"x","domain":"shipping","instruction":"a","context":{},"target":"a","safety_label":"answer"}\n' * 2
        with NamedTemporaryFile("w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            with self.assertRaisesRegex(ValueError, "duplicate example_id"):
                load_jsonl(stream.name)

    def test_empty_training_fields_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            example_from_dict({"example_id": "x", "domain": "shipping", "instruction": " ", "context": {}, "target": "x", "safety_label": "answer"})


if __name__ == "__main__":
    unittest.main()
