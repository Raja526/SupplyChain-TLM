"""Optional QLoRA training entry point for SupplyChain-TLM domain adapters.

This module is intentionally separate from the dependency-free/CPU trainer.
It requires a Transformers-format checkpoint plus CUDA, bitsandbytes, PEFT,
and the Transformers Trainer.  It never downloads a model automatically.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .dataset import TrainingExample, load_jsonl
from .train import training_prefix


def _require_gpu_dependencies() -> tuple[Any, Any, Any, Any, Any]:
    try:
        import torch
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            DataCollatorForSeq2Seq,
            Trainer,
            TrainingArguments,
        )
    except ImportError as error:
        raise RuntimeError(
            "QLoRA requires CUDA PyTorch, transformers, peft, and bitsandbytes; "
            "install the GPU requirements before training"
        ) from error
    if not torch.cuda.is_available():
        raise RuntimeError("QLoRA requires a CUDA-enabled PyTorch installation")
    return torch, (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig), (LoraConfig, TaskType, get_peft_model), DataCollatorForSeq2Seq, (Trainer, TrainingArguments)


def _rows(tokenizer: Any, examples: tuple[TrainingExample, ...], max_length: int) -> list[dict[str, list[int]]]:
    rows: list[dict[str, list[int]]] = []
    for example in examples:
        prefix = tokenizer(training_prefix(example), add_special_tokens=True, truncation=False)["input_ids"]
        encoded = tokenizer(
            training_prefix(example) + " " + example.target,
            truncation=True,
            max_length=max_length,
        )
        prefix_len = min(len(prefix), len(encoded["input_ids"]))
        labels = [-100] * prefix_len + encoded["input_ids"][prefix_len:]
        if not any(value != -100 for value in labels):
            raise ValueError(f"max_length={max_length} truncates target for {example.example_id}")
        encoded["labels"] = labels
        rows.append(encoded)
    return rows


class _Rows:
    def __init__(self, rows: list[dict[str, list[int]]]) -> None:
        self.rows = rows

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, list[int]]:
        return self.rows[index]


def train(args: argparse.Namespace) -> None:
    torch, model_parts, peft_parts, collator_type, trainer_parts = _require_gpu_dependencies()
    AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig = model_parts
    LoraConfig, TaskType, get_peft_model = peft_parts
    Trainer, TrainingArguments = trainer_parts

    examples = load_jsonl(args.dataset)
    if args.domain:
        examples = tuple(example for example in examples if example.domain == args.domain)
    if not examples:
        raise ValueError("no training examples remain after domain filtering")
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        local_files_only=True,
        quantization_config=quantization,
        device_map="auto",
    )
    model.config.use_cache = False
    model = get_peft_model(
        model,
        LoraConfig(
            r=args.rank,
            lora_alpha=args.alpha,
            lora_dropout=args.dropout,
            target_modules=args.target_modules.split(","),
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        ),
    )
    model.print_trainable_parameters()
    data = _Rows(_rows(tokenizer, examples, args.max_length))
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=str(output),
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=args.gradient_accumulation,
        logging_steps=1,
        save_strategy="epoch",
        report_to=[],
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        gradient_checkpointing=True,
        remove_unused_columns=False,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=data,
        data_collator=collator_type(tokenizer, padding=True, label_pad_token_id=-100, return_tensors="pt"),
    )
    trainer.train()
    model.save_pretrained(output)
    tokenizer.save_pretrained(output)
    (output / "training_metadata.json").write_text(
        json.dumps({"base_model": args.model, "domain": args.domain, "examples": len(examples)}, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train a SupplyChain-TLM QLoRA adapter")
    parser.add_argument("model", help="local Transformers-format base checkpoint")
    parser.add_argument("dataset")
    parser.add_argument("output")
    parser.add_argument("--domain", help="train only one domain, such as shipping")
    parser.add_argument("--epochs", type=float, default=3)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--alpha", type=int, default=32)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--gradient-accumulation", type=int, default=8)
    parser.add_argument("--target-modules", default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj")
    args = parser.parse_args(argv)
    train(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
