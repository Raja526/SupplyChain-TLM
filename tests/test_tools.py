import unittest

from src.supplychain_tlm.tools import ApprovalGate, FakeERPTool, ToolCall, ToolPolicy


class ToolBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.gate = ApprovalGate()
        self.tool = FakeERPTool()
        self.call = ToolCall("fake_erp", "release_shipment", {"shipment_id": "S-1"}, "release:S-1")

    def test_unapproved_call_is_blocked_and_audited(self):
        with self.assertRaises(PermissionError):
            self.gate.execute(self.tool, self.call)
        self.assertEqual(self.gate.audit.events[0].event_type, "blocked_tool_call")

    def test_approved_call_executes_and_is_audited(self):
        approval = self.gate.approve("proposal-1", "procurement_manager")
        self.assertEqual(self.gate.execute(self.tool, self.call, approval), "released:S-1")
        self.assertEqual([event.event_type for event in self.gate.audit.events], ["approval", "tool_call_started", "tool_call_completed"])

    def test_policy_rejects_wrong_approver(self):
        gate = ApprovalGate(policy=ToolPolicy(frozenset({"fake_erp"}), frozenset({"release_shipment"}), "procurement_manager"))
        approval = gate.approve("proposal-1", "warehouse_operator")
        with self.assertRaises(PermissionError):
            gate.execute(self.tool, self.call, approval)

    def test_idempotency_blocks_duplicate_execution(self):
        approval = self.gate.approve("proposal-1", "procurement_manager")
        self.gate.execute(self.tool, self.call, approval)
        with self.assertRaises(RuntimeError):
            self.gate.execute(self.tool, self.call, approval)
        self.assertEqual(self.gate.audit.events[-1].event_type, "duplicate_tool_call")


if __name__ == "__main__":
    unittest.main()
