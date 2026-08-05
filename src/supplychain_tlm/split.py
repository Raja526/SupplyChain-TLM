"""Deterministic train/validation/test splitting for task examples."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .dataset import TrainingExample


@dataclass(frozen=True)
class DatasetSplit:
    train: tuple[TrainingExample, ...]
    validation: tuple[TrainingExample, ...]
    test: tuple[TrainingExample, ...]


def split_examples(examples: tuple[TrainingExample, ...], train_ratio: float = 0.8, validation_ratio: float = 0.1) -> DatasetSplit:
    if not 0 < train_ratio < 1 or not 0 <= validation_ratio < 1 or train_ratio + validation_ratio >= 1:
        raise ValueError("ratios must satisfy 0 < train < 1, validation >= 0, and train + validation < 1")
    buckets = {"train": [], "validation": [], "test": []}
    for example in examples:
        value = int(hashlib.sha256(example.example_id.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
        target = "train" if value < train_ratio else "validation" if value < train_ratio + validation_ratio else "test"
        buckets[target].append(example)
    return DatasetSplit(tuple(buckets["train"]), tuple(buckets["validation"]), tuple(buckets["test"]))
