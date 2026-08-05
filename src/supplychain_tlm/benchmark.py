"""Small benchmark harness for comparing CPU TLM backends."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
import time

from .context import DecisionContext
from .dataset import load_jsonl
from .evaluation import context_from_example
from .model import RuleBasedSupplyChainTLM, TLMBackend
from .process_backend import ProcessTLMBackend


@dataclass(frozen=True)
class BenchmarkResult:
    samples: int
    elapsed_seconds: float

    @property
    def average_milliseconds(self) -> float:
        return self.elapsed_seconds * 1000 / self.samples if self.samples else 0.0

    @property
    def samples_per_second(self) -> float:
        return self.samples / self.elapsed_seconds if self.elapsed_seconds else 0.0


def benchmark(contexts: tuple[DecisionContext, ...], backend: TLMBackend | None = None) -> BenchmarkResult:
    backend = backend or RuleBasedSupplyChainTLM()
    start = time.perf_counter()
    for context in contexts:
        backend.answer(context)
    return BenchmarkResult(len(contexts), time.perf_counter() - start)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark a SupplyChain-TLM backend")
    parser.add_argument("dataset")
    parser.add_argument("--command", nargs="+", help="local backend executable and arguments")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    contexts = tuple(context_from_example(example) for example in load_jsonl(args.dataset))
    backend = ProcessTLMBackend(tuple(args.command), timeout_seconds=args.timeout) if args.command else None
    result = benchmark(contexts, backend)
    if args.as_json:
        print(json.dumps({"samples": result.samples, "elapsed_seconds": result.elapsed_seconds, "average_ms": result.average_milliseconds, "samples_per_second": result.samples_per_second}, sort_keys=True))
    else:
        print(f"samples: {result.samples}")
        print(f"elapsed_seconds: {result.elapsed_seconds:.6f}")
        print(f"average_ms: {result.average_milliseconds:.3f}")
        print(f"samples_per_second: {result.samples_per_second:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
