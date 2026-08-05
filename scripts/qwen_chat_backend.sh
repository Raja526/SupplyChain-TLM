#!/usr/bin/env bash
set -euo pipefail

: "${QWEN_CHAT_BIN:?Set QWEN_CHAT_BIN to the qwen chat executable}"
: "${QWEN_MODEL:?Set QWEN_MODEL to the model directory}"
: "${QWEN_CONFIG:?Set QWEN_CONFIG to config.json}"
: "${QWEN_TOKENIZER:?Set QWEN_TOKENIZER to tokenizer.json}"
QWEN_MAX_NEW="${QWEN_MAX_NEW:-128}"
# Supply-chain answers should not enter an unbounded reasoning mode by default.
# Weight residency is faster for the supported 2B CPU deployment; both remain
# user-overridable for larger checkpoints or low-memory machines.
export QWEN_THINKING="${QWEN_THINKING:-0}"
export QWEN_CACHE_WEIGHTS="${QWEN_CACHE_WEIGHTS:-1}"
export QWEN_CHAT="${QWEN_CHAT:-1}"

prompt="$(cat)"
exec "$QWEN_CHAT_BIN" "$QWEN_MODEL" "$QWEN_CONFIG" "$QWEN_TOKENIZER" "$prompt" "$QWEN_MAX_NEW"
