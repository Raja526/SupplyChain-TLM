"""Validation-gated, side-effect-free workflow proposals."""

from __future__ import annotations

from dataclasses import dataclass, field

from .ingest import ShipmentBundle
from .knowledge import DEFAULT_KNOWLEDGE, KnowledgeIndex
from .validation import validate_shipment_bundle


@dataclass(frozen=True)
class ActionProposal:
    action: str
    status: str
    reason: str
    required_approval: str
    inputs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Plan:
    goal: str
    proposals: tuple[ActionProposal, ...]
    validation_passed: bool
    references: tuple[str, ...] = ()


def propose_shipment_release(bundle: ShipmentBundle, knowledge: KnowledgeIndex = DEFAULT_KNOWLEDGE) -> Plan:
    """Propose a release workflow; never calls an ERP or changes state."""
    references = tuple(result.document.document_id for result in knowledge.search("shipment release invoice purchase order customs"))
    report = validate_shipment_bundle(
        bundle.invoice,
        bundle.purchase_order,
        bundle.packing_list,
        bundle.bill_of_lading,
    )
    if not report.passed:
        codes = ", ".join(issue.code for issue in report.issues)
        return Plan(
            goal="release shipment",
            validation_passed=False,
            references=references,
            proposals=(ActionProposal("release_shipment", "blocked", f"Validation failed: {codes}", "none"),),
        )
    return Plan(
        goal="release shipment",
        validation_passed=True,
        references=references,
        proposals=(
            ActionProposal(
                "release_shipment",
                "proposed",
                "All deterministic document checks passed.",
                "procurement_manager",
                (bundle.purchase_order.po_number, bundle.packing_list.shipment_id),
            ),
        ),
    )
