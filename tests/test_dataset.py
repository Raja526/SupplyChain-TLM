import unittest

from src.supplychain_tlm.dataset import example_from_dict, load_jsonl


class DatasetTests(unittest.TestCase):
    def test_sample_jsonl_loads(self):
        examples = load_jsonl("examples/training_tasks.jsonl")
        self.assertEqual(len(examples), 3)
        self.assertEqual(examples[2].safety_label, "refuse_action")

    def test_invalid_safety_label_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported safety label"):
            example_from_dict({"example_id": "x", "domain": "shipping", "instruction": "x", "context": {}, "target": "x", "safety_label": "execute"})


if __name__ == "__main__":
    unittest.main()
