import unittest

from src.supplychain_tlm.dataset import load_jsonl
from src.supplychain_tlm.evaluation import evaluate


class EvaluationTests(unittest.TestCase):
    def test_rule_baseline_passes_sample_safety_tasks(self):
        result = evaluate(load_jsonl("examples/training_tasks.jsonl"))
        self.assertEqual(result.passed, 3)
        self.assertEqual(result.accuracy, 1.0)


if __name__ == "__main__":
    unittest.main()
