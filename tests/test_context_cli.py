import unittest
from contextlib import redirect_stdout
from io import StringIO
import json

from src.supplychain_tlm.context_cli import main


class ContextCLITests(unittest.TestCase):
    def test_prints_valid_json_context(self):
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["examples/shipment_bundle.json", "Can this shipment be released?"]), 0)
        context = json.loads(output.getvalue())
        self.assertTrue(context["validation_passed"])
        self.assertIn("shipping", context["capabilities"])


if __name__ == "__main__":
    unittest.main()
