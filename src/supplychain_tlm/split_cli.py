"""Materialize deterministic, disjoint dataset splits as JSONL files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dataset import TrainingExample, load_jsonl
from .split import split_examples


def record(example: TrainingExample) -> dict[str, object]:
    return {
        "example_id": example.example_id,
        "domain": example.domain,
        "instruction": example.instruction,
        "context": example.context,
        "target": example.target,
        "safety_label": example.safety_label,
    }


def write_split(path: Path, examples: tuple[TrainingExample, ...]) -> None:
    path.write_text("".join(json.dumps(record(example), sort_keys=True) + "\n" for example in examples), encoding="utf-8")


def materialize(source: str, output_dir: str, *, train_ratio: float = 0.8, validation_ratio: float = 0.1) -> dict[str, int]:
    split = split_examples(load_jsonl(source), train_ratio, validation_ratio)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    groups = {"train": split.train, "validation": split.validation, "test": split.test}
    for name, examples in groups.items():
        write_split(output / f"{name}.jsonl", examples)
    return {name: len(examples) for name, examples in groups.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize deterministic SupplyChain-TLM dataset splits")
    parser.add_argument("source")
    parser.add_argument("output_dir")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--validation-ratio", type=float, default=0.1)
    args = parser.parse_args(argv)
    counts = materialize(args.source, args.output_dir, train_ratio=args.train_ratio, validation_ratio=args.validation_ratio)
    print("splits:", json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
