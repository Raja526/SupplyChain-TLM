"""Export validated tasks to a model-agnostic chat fine-tuning JSONL format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .dataset import TrainingExample, load_jsonl


SYSTEM_PROMPT = "You are SupplyChain-TLM. Use only supplied evidence. Never execute tools or bypass validation and approval."


def to_chat_record(example: TrainingExample) -> dict[str, Any]:
    user = f"{example.instruction}\n\nCONTEXT:\n{json.dumps(example.context, sort_keys=True)}"
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": example.target},
        ],
        "metadata": {
            "example_id": example.example_id,
            "domain": example.domain,
            "safety_label": example.safety_label,
        },
    }


def export_jsonl(source: str | Path, destination: str | Path) -> int:
    examples = load_jsonl(source)
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as stream:
        for example in examples:
            stream.write(json.dumps(to_chat_record(example), sort_keys=True) + "\n")
    return len(examples)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export SupplyChain-TLM tasks for chat fine-tuning")
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args(argv)
    print(f"exported: {export_jsonl(args.source, args.destination)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
