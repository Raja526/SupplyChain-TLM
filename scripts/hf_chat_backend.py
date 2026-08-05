#!/usr/bin/env python3
"""Run a local Transformers causal LM as a text-only stdin/stdout backend."""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model")
    parser.add_argument("--max-new", type=int, default=64)
    args = parser.parse_args()
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as error:
        raise SystemExit("torch and transformers are required") from error
    prompt = sys.stdin.read()
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(args.model, local_files_only=True)
    model.eval()
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=args.max_new, do_sample=False, pad_token_id=tokenizer.eos_token_id)
    generated = output[0, inputs["input_ids"].shape[1]:]
    print(tokenizer.decode(generated, skip_special_tokens=True).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
