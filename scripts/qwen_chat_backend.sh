#!/usr/bin/env bash
set -euo pipefail

: "${QWEN_CHAT_BIN:?Set QWEN_CHAT_BIN to the qwen chat executable}"
: "${QWEN_MODEL:?Set QWEN_MODEL to the model directory}"
: "${QWEN_CONFIG:?Set QWEN_CONFIG to config.json}"
: "${QWEN_TOKENIZER:?Set QWEN_TOKENIZER to tokenizer.json}"
QWEN_MAX_NEW="${QWEN_MAX_NEW:-128}"

prompt="$(cat)"
exec "$QWEN_CHAT_BIN" "$QWEN_MODEL" "$QWEN_CONFIG" "$QWEN_TOKENIZER" "$prompt" "$QWEN_MAX_NEW"
