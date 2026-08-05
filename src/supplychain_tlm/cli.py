"""Command-line entry point for the local release workflow."""

from __future__ import annotations

import argparse

from .ingest import load_bundle
from .tools import ApprovalGate, FakeERPTool, JsonlAuditLog, ToolPolicy
from .workflow import ReleaseWorkflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review or approve a local shipment release proposal")
    parser.add_argument("bundle", help="path to an extracted shipment JSON bundle")
    parser.add_argument("--approve-as", help="explicit approver role; omit for review-only mode")
    parser.add_argument("--audit", default="audit/workflow.jsonl", help="append-only JSONL audit path")
    args = parser.parse_args(argv)

    bundle = load_bundle(args.bundle)
    audit = JsonlAuditLog(args.audit)
    policy = ToolPolicy(frozenset({"fake_erp"}), frozenset({"release_shipment"}), "procurement_manager")
    workflow = ReleaseWorkflow(ApprovalGate(audit=audit, policy=policy), FakeERPTool())

    if not args.approve_as:
        result = workflow.prepare(bundle)
        proposal = result.plan.proposals[0]
        print(f"validation_passed: {result.plan.validation_passed}")
        print(f"proposal: {proposal.action} status={proposal.status}")
        print(f"reason: {proposal.reason}")
        print("review-only: no tool call executed")
        return 0 if result.plan.validation_passed else 1

    result = workflow.approve_and_execute(bundle, args.approve_as)
    if result.tool_result is None:
        print(f"blocked: {result.plan.proposals[0].reason}")
        return 1
    print(f"approved_by: {result.approval.approver}")
    print(f"tool_result: {result.tool_result}")
    print(f"audit: {args.audit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
