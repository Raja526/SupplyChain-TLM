"""Run a TLM backend against a shipment bundle without executing tools."""

from __future__ import annotations

import argparse

from .context import build_decision_context
from .ingest import load_bundle
from .model import RuleBasedSupplyChainTLM


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Answer a supply-chain question from a validated document bundle")
    parser.add_argument("bundle")
    parser.add_argument("request")
    args = parser.parse_args(argv)
    response = RuleBasedSupplyChainTLM().answer(build_decision_context(args.request, load_bundle(args.bundle)))
    print(f"answer: {response.answer}")
    print(f"confidence: {response.confidence:.2f}")
    print(f"suggested_action: {response.suggested_action}")
    print(f"references: {','.join(response.references) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
