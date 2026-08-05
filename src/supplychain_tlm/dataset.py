"""Versioned JSONL examples for SupplyChain-TLM training and evaluation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TrainingExample:
    example_id: str
    domain: str
    instruction: str
    context: dict[str, Any]
    target: str
    safety_label: str


def example_from_dict(data: dict[str, Any]) -> TrainingExample:
    required = ("example_id", "domain", "instruction", "context", "target", "safety_label")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"training example is missing: {', '.join(missing)}")
    if data["safety_label"] not in {"answer", "request_review", "request_approval", "refuse_action"}:
        raise ValueError(f"unsupported safety label: {data['safety_label']}")
    if not isinstance(data["context"], dict):
        raise ValueError("training example context must be an object")
    return TrainingExample(str(data["example_id"]), str(data["domain"]), str(data["instruction"]), data["context"], str(data["target"]), str(data["safety_label"]))


def load_jsonl(path: str | Path) -> tuple[TrainingExample, ...]:
    examples = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            examples.append(example_from_dict(json.loads(line)))
        except (json.JSONDecodeError, ValueError) as error:
            raise ValueError(f"invalid training example at line {line_number}: {error}") from error
    return tuple(examples)
