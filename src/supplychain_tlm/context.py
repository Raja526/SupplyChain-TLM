"""Build structured context for a future SupplyChain-TLM call."""

from __future__ import annotations

from dataclasses import dataclass

from .domains import DEFAULT_ADAPTERS, DomainAdapter
from .ingest import ShipmentBundle
from .knowledge import DEFAULT_KNOWLEDGE, KnowledgeIndex
from .router import route_request
from .validation import validate_shipment_bundle


@dataclass(frozen=True)
class DecisionContext:
    request: str
    capabilities: tuple[str, ...]
    domain_facts: tuple[tuple[str, str, str], ...]
    references: tuple[str, ...]
    validation_passed: bool
    validation_issue_codes: tuple[str, ...]


def build_decision_context(
    request: str,
    bundle: ShipmentBundle,
    *,
    adapters: tuple[DomainAdapter, ...] = DEFAULT_ADAPTERS,
    knowledge: KnowledgeIndex = DEFAULT_KNOWLEDGE,
) -> DecisionContext:
    routes = route_request(request)
    capabilities = tuple(route.capability for route in routes)
    selected = set(capabilities)
    facts: list[tuple[str, str, str]] = []
    for adapter in adapters:
        if adapter.capability in selected:
            facts.extend((adapter.capability, key, value) for key, value in adapter.build_context(bundle).facts)
    references = tuple(result.document.document_id for result in knowledge.search(request))
    report = validate_shipment_bundle(bundle.invoice, bundle.purchase_order, bundle.packing_list, bundle.bill_of_lading)
    return DecisionContext(request, capabilities, tuple(facts), references, report.passed, tuple(issue.code for issue in report.issues))
