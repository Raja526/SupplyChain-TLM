import unittest

from src.supplychain_tlm.ingest import bundle_from_dict
from src.supplychain_tlm.tools import ApprovalGate, FakeERPTool
from src.supplychain_tlm.workflow import ReleaseWorkflow


def make_bundle(total=10):
    return bundle_from_dict({
        "invoice": {"document_id": "INV-1", "po_number": "PO-1", "currency": "USD", "total_amount": total, "lines": [{"sku": "A", "quantity": 1}]},
        "purchase_order": {"document_id": "PO-1", "po_number": "PO-1", "currency": "USD", "total_amount": 10, "lines": [{"sku": "A", "quantity": 1}]},
        "packing_list": {"document_id": "PK-1", "shipment_id": "S-1", "lines": [{"sku": "A", "quantity": 1}]},
        "bill_of_lading": {"document_id": "B-1", "shipment_id": "S-1", "container_numbers": ["CONT-1"]},
    })


class WorkflowTests(unittest.TestCase):
    def test_invalid_bundle_never_reaches_tool(self):
        gate = ApprovalGate()
        result = ReleaseWorkflow(gate, FakeERPTool()).approve_and_execute(make_bundle(11), "procurement_manager")
        self.assertFalse(result.plan.validation_passed)
        self.assertIsNone(result.tool_result)
        self.assertEqual(gate.audit.events, [])

    def test_valid_bundle_completes_local_workflow(self):
        gate = ApprovalGate()
        result = ReleaseWorkflow(gate, FakeERPTool()).approve_and_execute(make_bundle(), "procurement_manager")
        self.assertTrue(result.plan.validation_passed)
        self.assertEqual(result.approval.decision, "approved")
        self.assertEqual(result.tool_result, "released:S-1")
        self.assertEqual([event.event_type for event in gate.audit.events], ["approval", "tool_call_started", "tool_call_completed"])


if __name__ == "__main__":
    unittest.main()
