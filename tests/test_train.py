import unittest
from tempfile import NamedTemporaryFile

from src.supplychain_tlm.dataset import load_jsonl
from src.supplychain_tlm.train import training_text, validate_inputs


class TrainingTests(unittest.TestCase):
    def test_training_text_contains_safety_boundary_and_target(self):
        text = training_text(load_jsonl("examples/training_tasks.jsonl")[0])
        self.assertIn("Never execute tools", text)
        self.assertIn("ASSISTANT:", text)
        self.assertIn("Request authorized procurement approval", text)

    def test_empty_dataset_is_rejected_before_training(self):
        with NamedTemporaryFile("w", encoding="utf-8") as dataset:
            with self.assertRaisesRegex(ValueError, "empty"):
                validate_inputs("/does/not/exist", dataset.name)


if __name__ == "__main__":
    unittest.main()
