import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from src.supplychain_tlm.cli import main


class CLITests(unittest.TestCase):
    bundle = "examples/shipment_bundle.json"

    def test_default_mode_is_review_only(self):
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main([self.bundle]), 0)
        self.assertIn("review-only: no tool call executed", output.getvalue())

    def test_approval_mode_writes_audit(self):
        with TemporaryDirectory() as directory:
            audit = Path(directory) / "workflow.jsonl"
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main([self.bundle, "--approve-as", "procurement_manager", "--audit", str(audit)]), 0)
            self.assertIn("tool_result: dry-run:release:SHIP-100:PO-100", output.getvalue())
            self.assertEqual(len(audit.read_text(encoding="utf-8").splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
