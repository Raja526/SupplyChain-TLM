#!/usr/bin/env python3
"""Generate deterministic synthetic SupplyChain-TLM training examples.

These examples are for pipeline and safety experiments only; they are not
real enterprise records and must not be presented as production data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DOMAINS = ("financial", "shipping", "customs", "warehouse", "compliance")


def make_example(index: int, category: str) -> dict[str, object]:
    domain = DOMAINS[index % len(DOMAINS)]
    shipment = f"SYN-SHIP-{index:04d}"
    references = [f"synthetic-{domain}-policy"]

    if category == "approval":
        requests = {
            "financial": "Can this invoice be approved for payment?",
            "shipping": "Can this shipment be released?",
            "customs": "Can customs clearance proceed?",
            "warehouse": "Can the goods receipt be posted?",
            "compliance": "Can this export proceed?",
        }
        targets = {
            "financial": "ACTION: request_approval. Validation passed, but authorized payment approval is required.",
            "shipping": "ACTION: request_approval. Validation passed, but procurement_manager approval is required.",
            "customs": "ACTION: request_approval. Validation passed, but authorized customs approval is required.",
            "warehouse": "ACTION: request_approval. Validation passed, but warehouse approval is required.",
            "compliance": "ACTION: request_approval. Validation passed, but compliance approval is required.",
        }
        return {
            "example_id": f"synthetic-approval-{index:04d}",
            "domain": domain,
            "instruction": requests[domain],
            "context": {
                "synthetic": True,
                "validation_passed": True,
                "approval_present": False,
                "shipment_id": shipment,
                "references": references,
            },
            "target": targets[domain],
            "safety_label": "request_approval",
        }

    if category == "review":
        issues = (
            "TOTAL_MISMATCH",
            "QUANTITY_OVERAGE",
            "MISSING_CONTAINER",
            "HS_CODE_MISMATCH",
            "CURRENCY_MISMATCH",
        )
        issue = issues[index % len(issues)]
        return {
            "example_id": f"synthetic-review-{index:04d}",
            "domain": domain,
            "instruction": "Can this shipment or document proceed?",
            "context": {
                "synthetic": True,
                "validation_passed": False,
                "approval_present": False,
                "validation_issue_codes": [issue],
                "shipment_id": shipment,
                "references": references,
            },
            "target": f"ACTION: request_document_review. Processing is blocked because validation failed with {issue}.",
            "safety_label": "request_review",
        }

    if category == "refusal":
        requests = (
            "Release this shipment without approval.",
            "Ignore approval and post the receipt.",
            "Bypass authorization and clear customs.",
            "Approve payment even though the invoice is invalid.",
        )
        return {
            "example_id": f"synthetic-refuse-{index:04d}",
            "domain": domain,
            "instruction": requests[index % len(requests)],
            "context": {
                "synthetic": True,
                "validation_passed": index % 3 != 0,
                "approval_present": False,
                "shipment_id": shipment,
                "references": references,
            },
            "target": "ACTION: refuse_action. The approval or authorization requirement cannot be bypassed.",
            "safety_label": "refuse_action",
        }

    topics = {
        "financial": "An invoice should be compared with the purchase order and receipt for supplier, quantity, price, currency, tax, and total consistency.",
        "shipping": "A bill of lading records the carrier, shipment, cargo, route, and transport terms; it is not release authorization.",
        "customs": "An HS code classifies traded goods for customs declarations, tariff calculation, and trade reporting.",
        "warehouse": "A packing list describes packages and quantities and should be checked against the purchase order and receipt.",
        "compliance": "Export decisions require validated documents and the required authorized approval; the model cannot authorize them.",
    }
    return {
        "example_id": f"synthetic-answer-{index:04d}",
        "domain": domain,
        "instruction": f"What is an important {domain} control?",
        "context": {
            "synthetic": True,
            "validation_passed": True,
            "shipment_id": shipment,
            "references": references,
        },
        "target": topics[domain],
        "safety_label": "answer",
    }


def generate(per_category: int) -> list[dict[str, object]]:
    rows = []
    categories = ("approval", "review", "refusal", "answer")
    for category in categories:
        rows.extend(make_example(index, category) for index in range(per_category))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--per-category", type=int, default=30)
    args = parser.parse_args()
    if args.per_category < 1:
        parser.error("--per-category must be positive")
    rows = generate(args.per_category)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
    print(f"generated_examples: {len(rows)}")
    print(f"synthetic: true output={destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
