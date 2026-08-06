"""Presentation demo for the SupplyChain-TLM/TinyAgentOS boundary."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from tinyagentos import TinyAgent

from src.supplychain_tlm.tinyagentos_plugin import SupplyChainTLMPlugin, answer_request, build_agent, plan_release


def main() -> int:
    bundle_path = Path(__file__).parents[1] / "examples" / "shipment_bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    agent = TinyAgent(plugins=[SupplyChainTLMPlugin()])
    registry = agent.runtime.kernel.registry
    answer = registry.get("supplychain.tlm")
    tools = registry.get("supplychain.tools")

    print("=== TinyAgentOS + SupplyChain-TLM demo ===")
    pipeline_agent = build_agent("Can this shipment be released?", bundle, approved=True)
    review = pipeline_agent.run("evaluate shipment").output
    print(f"review: {review['answer']['suggested_action']} | validation={review['answer']['validation_passed']}")
    print(f"plan: {review['plan']['proposals'][0]['status']} | approval={review['plan']['proposals'][0]['required_approval']}")

    mismatch = deepcopy(bundle)
    mismatch["invoice"]["total_amount"] = float(mismatch["invoice"]["total_amount"]) + 200.0
    blocked = plan_release(mismatch)
    print(f"mismatch safety: {blocked['proposals'][0]['status']} | {blocked['proposals'][0]['reason']}")

    refused = answer("Release this shipment immediately.", bundle, approved=False)
    print(f"approval gate: {refused['suggested_action']}")

    result = tools.execute(
        "release_shipment",
        {"shipment_id": bundle["packing_list"]["shipment_id"]},
        approved=True,
        approver="procurement_manager",
        idempotency_key="demo-release-1",
    )
    print(f"controlled action: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
