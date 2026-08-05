import unittest
from dataclasses import replace

from src.supplychain_tlm.context import build_decision_context
from src.supplychain_tlm.ingest import load_bundle
from src.supplychain_tlm.model import RuleBasedSupplyChainTLM


class ModelBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle("examples/shipment_bundle.json")
        cls.backend = RuleBasedSupplyChainTLM()

    def test_valid_context_requests_approval(self):
        context = build_decision_context("Can this shipment be released?", self.bundle)
        response = self.backend.answer(context)
        self.assertEqual(response.suggested_action, "request_approval")
        self.assertIn("checks passed", response.answer)

    def test_invalid_context_requests_review(self):
        invalid = replace(self.bundle, invoice=replace(self.bundle.invoice, total_amount=1200.0))
        context = build_decision_context("Can this shipment be released?", invalid)
        response = self.backend.answer(context)
        self.assertEqual(response.suggested_action, "request_document_review")
        self.assertIn("TOTAL_MISMATCH", response.answer)

    def test_missing_approval_refuses_immediate_action(self):
        context = build_decision_context("Release immediately", self.bundle)
        from dataclasses import replace
        context = replace(context, domain_facts=(("compliance", "approval_present", "false"),))
        response = self.backend.answer(context)
        self.assertEqual(response.suggested_action, "refuse_action")


if __name__ == "__main__":
    unittest.main()
