"""Coverage and split report for auditable SupplyChain-TLM datasets."""

from __future__ import annotations

import argparse
from collections import Counter
import json

from .dataset import load_jsonl
from .split import split_examples


def report(path: str, *, train_ratio: float = 0.8, validation_ratio: float = 0.1) -> dict[str, object]:
    examples = load_jsonl(path)
    split = split_examples(examples, train_ratio, validation_ratio)
    return {
        "total": len(examples),
        "domains": dict(sorted(Counter(example.domain for example in examples).items())),
        "safety_labels": dict(sorted(Counter(example.safety_label for example in examples).items())),
        "splits": {"train": len(split.train), "validation": len(split.validation), "test": len(split.test)},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report SupplyChain-TLM dataset coverage")
    parser.add_argument("dataset")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--validation-ratio", type=float, default=0.1)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    payload = report(args.dataset, train_ratio=args.train_ratio, validation_ratio=args.validation_ratio)
    if args.as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(f"examples: {payload['total']}")
        print(f"domains: {payload['domains']}")
        print(f"safety_labels: {payload['safety_labels']}")
        print(f"splits: {payload['splits']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
