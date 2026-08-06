import unittest

from src.supplychain_tlm.ingest import load_bundle
from src.supplychain_tlm.tinyagentos_plugin import SupplyChainTLMPlugin, answer_request, build_agent, plan_release


class TinyAgentOSPluginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle("examples/shipment_bundle.json")
        cls.bundle_dict = {
            "invoice": {"document_id": "INV-9", "po_number": "PO-100", "currency": "USD", "total_amount": 1000, "lines": [{"sku": "SKU-1", "quantity": 10}]},
            "purchase_order": {"document_id": "PO-100", "po_number": "PO-100", "currency": "USD", "total_amount": 1000, "lines": [{"sku": "SKU-1", "quantity": 10}]},
            "packing_list": {"document_id": "PK-1", "shipment_id": "SHIP-1", "lines": [{"sku": "SKU-1", "quantity": 10}]},
            "bill_of_lading": {"document_id": "BOL-1", "shipment_id": "SHIP-1", "container_numbers": ["MSCU1234567"]},
        }

    def test_answer_is_json_safe_and_approval_aware(self):
        result = answer_request("Can this shipment be released?", self.bundle_dict, approved=False)
        self.assertEqual(result["suggested_action"], "refuse_action")
        self.assertTrue(result["validation_passed"])

    def test_planner_blocks_invalid_bundle_without_execution(self):
        invalid = dict(self.bundle_dict)
        invalid["invoice"] = dict(invalid["invoice"], total_amount=1200)
        result = plan_release(invalid)
        self.assertFalse(result["validation_passed"])
        self.assertEqual(result["proposals"][0]["status"], "blocked")
        self.assertIn("TOTAL_MISMATCH", result["proposals"][0]["reason"])

    def test_plugin_registers_domain_services_and_gated_tool(self):
        from tinyagentos import TinyAgent
        from tinyagentos.tools import ToolPermissionError

        agent = TinyAgent(plugins=[SupplyChainTLMPlugin()])
        registry = agent.runtime.kernel.registry
        self.assertTrue(registry.exists("supplychain.tlm"))
        tools = registry.get("supplychain.tools")
        with self.assertRaises(ToolPermissionError):
            tools.execute("release_shipment", {"shipment_id": "SHIP-1"})
        self.assertEqual(
            tools.execute("release_shipment", {"shipment_id": "SHIP-1"}, approved=True, approver="procurement_manager", idempotency_key="SHIP-1-release"),
            "dry-run:release:SHIP-1",
        )

    def test_domain_answer_runs_inside_tinyagentos_pipeline(self):
        agent = build_agent("Can this shipment be released?", self.bundle_dict, approved=False)
        result = agent.run("evaluate shipment")
        self.assertEqual(result.output["answer"]["suggested_action"], "refuse_action")
        self.assertEqual(result.output["plan"]["proposals"][0]["status"], "proposed")

    def test_optional_model_is_advisory_only(self):
        class FakeModel:
            def generate(self, context):
                return "model suggestion: release"

        agent = build_agent("Can this shipment be released?", self.bundle_dict, model=FakeModel())
        result = agent.run("evaluate shipment")
        self.assertEqual(result.output["model_explanation"], "model suggestion: release")
        self.assertEqual(result.output["plan"]["proposals"][0]["required_approval"], "procurement_manager")


if __name__ == "__main__":
    unittest.main()
