import unittest

from src.supplychain_tlm.benchmark import benchmark
from src.supplychain_tlm.dataset import load_jsonl
from src.supplychain_tlm.evaluation import context_from_example


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_reports_all_samples(self):
        contexts = tuple(context_from_example(example) for example in load_jsonl("examples/training_tasks.jsonl"))
        result = benchmark(contexts)
        self.assertEqual(result.samples, 3)
        self.assertGreaterEqual(result.elapsed_seconds, 0.0)
        self.assertGreaterEqual(result.samples_per_second, 0.0)


if __name__ == "__main__":
    unittest.main()
