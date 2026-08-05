"""Small supervised causal-LM trainer for local SupplyChain-TLM experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .dataset import TrainingExample, load_jsonl
from .training_export import SYSTEM_PROMPT


def training_text(example: TrainingExample) -> str:
    context = json.dumps(example.context, sort_keys=True)
    return f"{SYSTEM_PROMPT}\nUSER: {example.instruction}\nCONTEXT: {context}\nASSISTANT: {example.target}"


def train(model_name: str, dataset_path: str, output_dir: str, *, epochs: int = 1, max_length: int = 512, learning_rate: float = 2e-5, device: str = "cpu") -> list[float]:
    """Fine-tune a local Transformers causal LM; returns mean loss per epoch."""
    try:
        import torch
        from torch.utils.data import DataLoader, Dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer, DataCollatorForLanguageModeling
    except ImportError as error:
        raise RuntimeError("training requires torch and transformers") from error

    examples = load_jsonl(dataset_path)
    if not examples:
        raise ValueError("training dataset is empty")
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    target_device = torch.device(device)
    if target_device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA device requested but CUDA is unavailable")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    rows = [tokenizer(training_text(example), truncation=True, max_length=max_length) for example in examples]

    class Rows(Dataset):
        def __len__(self) -> int:
            return len(rows)

        def __getitem__(self, index: int) -> dict[str, list[int]]:
            return rows[index]

    model = AutoModelForCausalLM.from_pretrained(model_name, local_files_only=True)
    model.to(target_device)
    model.train()
    loader = DataLoader(Rows(), batch_size=1, shuffle=True, collate_fn=DataCollatorForLanguageModeling(tokenizer, mlm=False))
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    losses: list[float] = []
    for _ in range(epochs):
        total = 0.0
        for batch in loader:
            batch = {key: value.to(target_device) for key, value in batch.items()}
            optimizer.zero_grad()
            loss = model(**batch).loss
            loss.backward()
            optimizer.step()
            total += float(loss.detach())
        losses.append(total / len(loader))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output)
    tokenizer.save_pretrained(output)
    return losses


def validate_inputs(model_name: str, dataset_path: str) -> int:
    """Validate local tokenizer availability and dataset contents without loading model weights."""
    examples = load_jsonl(dataset_path)
    if not examples:
        raise ValueError("training dataset is empty")
    try:
        from transformers import AutoTokenizer
        AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    except ImportError as error:
        raise RuntimeError("validation requires transformers") from error
    return len(examples)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fine-tune a local causal LM on SupplyChain-TLM tasks")
    parser.add_argument("model")
    parser.add_argument("dataset")
    parser.add_argument("output")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--device", default="cpu", help="training device, for example cpu or cuda")
    parser.add_argument("--validate-only", action="store_true", help="check local tokenizer and dataset without loading model weights")
    args = parser.parse_args(argv)
    if args.validate_only:
        print(f"validated_examples: {validate_inputs(args.model, args.dataset)}")
        return 0
    losses = train(args.model, args.dataset, args.output, epochs=args.epochs, max_length=args.max_length, learning_rate=args.learning_rate, device=args.device)
    print("losses:", ",".join(f"{loss:.6f}" for loss in losses))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
