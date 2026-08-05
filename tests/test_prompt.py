import unittest

from src.supplychain_tlm.context import build_decision_context
from src.supplychain_tlm.ingest import load_bundle
from src.supplychain_tlm.prompt import format_prompt


class PromptTests(unittest.TestCase):
    def test_prompt_contains_context_and_safety_boundary(self):
        context = build_decision_context("Can this shipment be released?", load_bundle("examples/shipment_bundle.json"))
        prompt = format_prompt(context)
        self.assertIn("STATE: passed=true", prompt)
        self.assertIn("shipping.shipment_id = SHIP-100", prompt)
        self.assertIn("Never execute tools", prompt)
        self.assertIn("shipment-release", prompt)


if __name__ == "__main__":
    unittest.main()
