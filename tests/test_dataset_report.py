import json
import unittest
from contextlib import redirect_stdout
from io import StringIO

from src.supplychain_tlm.dataset_report import main, report


class DatasetReportTests(unittest.TestCase):
    def test_extended_fixture_reports_coverage_and_disjoint_split_sizes(self):
        payload = report("examples/training_tasks_extended.jsonl")
        self.assertEqual(payload["total"], 12)
        self.assertEqual(payload["safety_labels"]["answer"], 3)
        self.assertEqual(sum(payload["splits"].values()), 12)

    def test_json_cli_output(self):
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["examples/training_tasks_extended.jsonl", "--json"]), 0)
        self.assertEqual(json.loads(output.getvalue())["total"], 12)


if __name__ == "__main__":
    unittest.main()
