import unittest
from dataclasses import replace

from src.supplychain_tlm.context import build_decision_context
from src.supplychain_tlm.ingest import load_bundle
from src.supplychain_tlm.steps import build_release_plan


class WorkflowStepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle("examples/shipment_bundle.json")

    def test_valid_plan_requires_approval_before_execution(self):
        plan = build_release_plan(build_decision_context("Can this shipment be released?", self.bundle))
        states = {step.name: step.status for step in plan.steps}
        self.assertEqual(states["validate_documents"], "completed")
        self.assertEqual(states["request_procurement_approval"], "required")
        self.assertEqual(states["release_shipment"], "blocked_until_approval")

    def test_invalid_plan_requires_human_review(self):
        invalid = replace(self.bundle, invoice=replace(self.bundle.invoice, total_amount=1200.0))
        plan = build_release_plan(build_decision_context("Can this shipment be released?", invalid))
        states = {step.name: step.status for step in plan.steps}
        self.assertEqual(states["validate_documents"], "blocked")
        self.assertEqual(states["human_review"], "required")
        self.assertEqual(states["release_shipment"], "blocked")


if __name__ == "__main__":
    unittest.main()
