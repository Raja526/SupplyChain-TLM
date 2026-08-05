import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from src.supplychain_tlm.split_cli import materialize


class SplitCliTests(unittest.TestCase):
    def test_materialize_writes_disjoint_jsonl_files(self):
        with TemporaryDirectory() as directory:
            counts = materialize("examples/training_tasks_extended.jsonl", directory)
            self.assertEqual(sum(counts.values()), 12)
            ids = []
            for name in ("train", "validation", "test"):
                path = Path(directory) / f"{name}.jsonl"
                self.assertTrue(path.exists())
                ids.extend(line.split('"example_id": "', 1)[1].split('"', 1)[0] for line in path.read_text().splitlines())
            self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
