import unittest

from src.supplychain_tlm.dataset import load_jsonl
from src.supplychain_tlm.split import split_examples


class SplitTests(unittest.TestCase):
    def test_split_is_deterministic_and_disjoint(self):
        examples = load_jsonl("examples/training_tasks.jsonl")
        first = split_examples(examples, 0.6, 0.2)
        second = split_examples(examples, 0.6, 0.2)
        self.assertEqual(first, second)
        ids = [item.example_id for group in (first.train, first.validation, first.test) for item in group]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), len(examples))

    def test_invalid_ratios_are_rejected(self):
        with self.assertRaises(ValueError):
            split_examples((), 0.9, 0.2)


if __name__ == "__main__":
    unittest.main()
