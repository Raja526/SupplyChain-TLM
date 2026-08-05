import unittest

from src.supplychain_tlm.context import build_decision_context
from src.supplychain_tlm.ingest import load_bundle


class ContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle("examples/shipment_bundle.json")

    def test_context_combines_capabilities_facts_and_references(self):
        context = build_decision_context("Can this shipment be released if the invoice is correct?", self.bundle)
        self.assertIn("shipping", context.capabilities)
        self.assertIn("financial", context.capabilities)
        self.assertTrue(any(key == "shipment_id" for _, key, _ in context.domain_facts))
        self.assertIn("shipment-release", context.references)
        self.assertTrue(context.validation_passed)

    def test_invalid_bundle_preserves_issue_codes(self):
        bundle = load_bundle("examples/shipment_bundle.json")
        from dataclasses import replace
        invalid_invoice = replace(bundle.invoice, total_amount=1200.0)
        invalid_bundle = replace(bundle, invoice=invalid_invoice)
        context = build_decision_context("Can this shipment be released?", invalid_bundle)
        self.assertFalse(context.validation_passed)
        self.assertIn("TOTAL_MISMATCH", context.validation_issue_codes)


if __name__ == "__main__":
    unittest.main()
