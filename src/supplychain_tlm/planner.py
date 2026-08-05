"""Validation-gated, side-effect-free workflow proposals."""

from __future__ import annotations

from dataclasses import dataclass, field

from .ingest import ShipmentBundle
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


def propose_shipment_release(bundle: ShipmentBundle) -> Plan:
    """Propose a release workflow; never calls an ERP or changes state."""
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
            proposals=(ActionProposal("release_shipment", "blocked", f"Validation failed: {codes}", "none"),),
        )
    return Plan(
        goal="release shipment",
        validation_passed=True,
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
