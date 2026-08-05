"""Explicit multi-step plans for autonomous supply-chain workflows."""

from __future__ import annotations

from dataclasses import dataclass

from .context import DecisionContext


@dataclass(frozen=True)
class WorkflowStep:
    name: str
    status: str
    reason: str


@dataclass(frozen=True)
class WorkflowPlan:
    goal: str
    steps: tuple[WorkflowStep, ...]


def build_release_plan(context: DecisionContext) -> WorkflowPlan:
    if context.validation_passed:
        validation = WorkflowStep("validate_documents", "completed", "All deterministic checks passed.")
        review = WorkflowStep("human_review", "not_required", "No validation or context review flag is active.")
        approval = WorkflowStep("request_procurement_approval", "required", "A procurement manager must approve release.")
        execute = WorkflowStep("release_shipment", "blocked_until_approval", "Execution remains outside the planner until approval.")
    else:
        codes = ", ".join(context.validation_issue_codes)
        validation = WorkflowStep("validate_documents", "blocked", f"Validation failed: {codes}")
        review = WorkflowStep("human_review", "required", "Resolve document discrepancies before continuing.")
        approval = WorkflowStep("request_procurement_approval", "blocked", "Approval cannot be requested for invalid documents.")
        execute = WorkflowStep("release_shipment", "blocked", "Execution is blocked by validation failure.")
    retrieval = WorkflowStep("retrieve_guidance", "completed" if context.references else "not_required", f"References: {', '.join(context.references) or 'none'}")
    return WorkflowPlan("release shipment", (validation, retrieval, review, approval, execute))
