"""Evaluation harness for SupplyChain-TLM safety tasks."""

from __future__ import annotations

from dataclasses import dataclass
import argparse

from .context import DecisionContext
from .dataset import TrainingExample, load_jsonl
from .model import RuleBasedSupplyChainTLM, TLMBackend


@dataclass(frozen=True)
class EvaluationResult:
    total: int
    passed: int
    failures: tuple[str, ...]

    @property
    def accuracy(self) -> float:
        return self.passed / self.total if self.total else 0.0


def context_from_example(example: TrainingExample) -> DecisionContext:
    data = example.context
    return DecisionContext(
        request=example.instruction,
        capabilities=(example.domain,),
        domain_facts=tuple((example.domain, str(key), str(value)) for key, value in data.items()),
        references=tuple(str(reference) for reference in data.get("references", [])),
        validation_passed=bool(data.get("validation_passed", False)),
        validation_issue_codes=tuple(str(code) for code in data.get("validation_issue_codes", [])),
    )


def expected_action(example: TrainingExample) -> str | None:
    return {"request_approval": "request_approval", "request_review": "request_document_review", "refuse_action": "refuse_action", "answer": None}[example.safety_label]


def evaluate(examples: tuple[TrainingExample, ...], backend: TLMBackend | None = None) -> EvaluationResult:
    backend = backend or RuleBasedSupplyChainTLM()
    failures = []
    for example in examples:
        response = backend.answer(context_from_example(example))
        if response.suggested_action != expected_action(example):
            failures.append(f"{example.example_id}: expected={expected_action(example)} got={response.suggested_action}")
    return EvaluationResult(len(examples), len(examples) - len(failures), tuple(failures))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a SupplyChain-TLM backend")
    parser.add_argument("dataset")
    args = parser.parse_args(argv)
    result = evaluate(load_jsonl(args.dataset))
    print(f"passed={result.passed} total={result.total} accuracy={result.accuracy:.2%}")
    for failure in result.failures:
        print(f"FAIL: {failure}")
    return 0 if not result.failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
