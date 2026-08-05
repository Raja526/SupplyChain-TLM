import unittest

from src.supplychain_tlm.dataset import load_jsonl
from src.supplychain_tlm.train import training_text


class TrainingTests(unittest.TestCase):
    def test_training_text_contains_safety_boundary_and_target(self):
        text = training_text(load_jsonl("examples/training_tasks.jsonl")[0])
        self.assertIn("Never execute tools", text)
        self.assertIn("ASSISTANT:", text)
        self.assertIn("Request authorized procurement approval", text)


if __name__ == "__main__":
    unittest.main()
