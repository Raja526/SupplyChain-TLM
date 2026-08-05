"""Small localhost service boundary for orchestration integrations."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .erp import DryRunERPClient, ERPToolAdapter
from .context import build_decision_context
from .ingest import load_bundle
from .model import RuleBasedSupplyChainTLM
from .tools import ApprovalGate, JsonlAuditLog, ToolPolicy
from .workflow import ReleaseWorkflow


def answer_payload(bundle_path: str, request: str) -> dict[str, Any]:
    """Return a deterministic answer payload; no external tools are called."""
    context = build_decision_context(request, load_bundle(bundle_path))
    response = RuleBasedSupplyChainTLM().answer(context)
    return {
        "mode": "deterministic",
        "answer": response.answer,
        "confidence": response.confidence,
        "suggested_action": response.suggested_action,
        "references": list(response.references),
    }


def release_payload(bundle_path: str, approver: str | None = None, audit_path: str = "audit/service.jsonl") -> dict[str, Any]:
    """Prepare or execute a safe dry-run release through the approval gate."""
    audit = JsonlAuditLog(audit_path)
    erp = ERPToolAdapter(DryRunERPClient())
    policy = ToolPolicy(frozenset({erp.name}), frozenset({"release_shipment"}), "procurement_manager")
    workflow = ReleaseWorkflow(ApprovalGate(audit=audit, policy=policy), erp)
    bundle = load_bundle(bundle_path)
    if not approver:
        result = workflow.prepare(bundle)
        return {"mode": "review_only", "validation_passed": result.plan.validation_passed, "proposal": asdict(result.plan.proposals[0]), "audit": audit_path}
    result = workflow.approve_and_execute(bundle, approver)
    return {"mode": "approved_dry_run" if result.tool_result else "blocked", "validation_passed": result.plan.validation_passed, "tool_result": result.tool_result, "audit": audit_path}


def handle_json(payload: str) -> str:
    """Handle one newline-delimited JSON request for embedding in a service."""
    request = json.loads(payload)
    if request.get("operation") == "answer":
        result = answer_payload(str(request["bundle"]), str(request["request"]))
    elif request.get("operation") == "release":
        result = release_payload(str(request["bundle"]), request.get("approver"), str(request.get("audit", "audit/service.jsonl")))
    else:
        raise ValueError("operation must be answer or release")
    return json.dumps(result, sort_keys=True)
