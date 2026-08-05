import unittest
import sys
import json
from contextlib import redirect_stdout
from io import StringIO

from src.supplychain_tlm.benchmark import benchmark
from src.supplychain_tlm.dataset import load_jsonl
from src.supplychain_tlm.evaluation import context_from_example
from src.supplychain_tlm.process_backend import ProcessTLMBackend


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_reports_all_samples(self):
        contexts = tuple(context_from_example(example) for example in load_jsonl("examples/training_tasks.jsonl"))
        result = benchmark(contexts)
        self.assertEqual(result.samples, 3)
        self.assertGreaterEqual(result.elapsed_seconds, 0.0)

    def test_benchmark_accepts_local_backend_command(self):
        contexts = tuple(context_from_example(example) for example in load_jsonl("examples/training_tasks.jsonl"))
        result = benchmark(contexts, ProcessTLMBackend((sys.executable, "-c", "import sys; print('ok')")))
        self.assertEqual(result.samples, 3)
        self.assertGreaterEqual(result.samples_per_second, 0.0)

    def test_benchmark_cli_json_output(self):
        from src.supplychain_tlm.benchmark import main
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["examples/training_tasks.jsonl", "--json"]), 0)
        self.assertEqual(json.loads(output.getvalue())["samples"], 3)


if __name__ == "__main__":
    unittest.main()
