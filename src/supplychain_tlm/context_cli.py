"""Print the structured context that would be supplied to a TLM."""

from __future__ import annotations

import argparse

from .context import build_decision_context
from .ingest import load_bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect model-ready supply-chain decision context")
    parser.add_argument("bundle")
    parser.add_argument("request")
    args = parser.parse_args(argv)
    context = build_decision_context(args.request, load_bundle(args.bundle))
    print(context.to_json())
    return 0 if context.validation_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
