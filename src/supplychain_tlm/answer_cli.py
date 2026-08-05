"""Run a TLM backend against a shipment bundle without executing tools."""

from __future__ import annotations

import argparse

from .context import build_decision_context
from .ingest import load_bundle
from .model import RuleBasedSupplyChainTLM
from .process_backend import ProcessTLMBackend


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Answer a supply-chain question from a validated document bundle")
    parser.add_argument("bundle")
    parser.add_argument("request")
    parser.add_argument("--command", nargs="+", help="local CPU model executable and arguments")
    parser.add_argument("--timeout", type=float, default=60.0, help="local backend timeout in seconds")
    parser.add_argument("--fast-path", action="store_true", help="use deterministic validation response without invoking the local model")
    args = parser.parse_args(argv)
    backend = RuleBasedSupplyChainTLM() if args.fast_path or not args.command else ProcessTLMBackend(tuple(args.command), timeout_seconds=args.timeout)
    response = backend.answer(build_decision_context(args.request, load_bundle(args.bundle)))
    print(f"answer: {response.answer}")
    print(f"confidence: {response.confidence:.2f}")
    print(f"suggested_action: {response.suggested_action}")
    print(f"references: {','.join(response.references) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
