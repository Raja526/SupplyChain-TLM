"""Preflight checks for connecting a local Qwen checkpoint to the backend."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
from pathlib import Path


@dataclass(frozen=True)
class CheckpointReport:
    path: str
    passed: bool
    errors: tuple[str, ...]
    model_type: str = ""
    hidden_size: int = 0
    layers: int = 0


def inspect_checkpoint(path: str | Path, expected_hidden_size: int = 2048, expected_layers: int = 24) -> CheckpointReport:
    root = Path(path)
    errors: list[str] = []
    config_path = root / "config.json"
    tokenizer_path = root / "tokenizer.json"
    if not config_path.is_file():
        errors.append("missing config.json")
    if not tokenizer_path.is_file():
        errors.append("missing tokenizer.json")
    if errors:
        return CheckpointReport(str(root), False, tuple(errors))
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return CheckpointReport(str(root), False, (f"invalid config.json: {error}",))
    model_type = str(config.get("model_type", config.get("architectures", [""])[0] if config.get("architectures") else ""))
    hidden_size = int(config.get("hidden_size", 0))
    layers = int(config.get("num_hidden_layers", 0))
    if hidden_size != expected_hidden_size:
        errors.append(f"hidden_size={hidden_size}, expected {expected_hidden_size}")
    if layers != expected_layers:
        errors.append(f"num_hidden_layers={layers}, expected {expected_layers}")
    return CheckpointReport(str(root), not errors, tuple(errors), model_type, hidden_size, layers)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a Qwen3.5-2B checkpoint before CPU inference")
    parser.add_argument("path")
    args = parser.parse_args(argv)
    report = inspect_checkpoint(args.path)
    print(f"path: {report.path}")
    print(f"model_type: {report.model_type or 'unknown'}")
    print(f"hidden_size: {report.hidden_size}")
    print(f"layers: {report.layers}")
    print(f"passed: {report.passed}")
    for error in report.errors:
        print(f"error: {error}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
