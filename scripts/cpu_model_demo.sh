#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_URL="${LLAMA_SERVER_URL:-http://127.0.0.1:8081}"
BACKEND="${ROOT_DIR}/scripts/llama_server_backend.py"
MAX_NEW="${QWEN_MAX_NEW:-32}"
MISMATCH_BUNDLE="$(mktemp)"
trap 'rm -f "$MISMATCH_BUNDLE"' EXIT

cd "$ROOT_DIR"
curl -fsS "${SERVER_URL}/health" >/dev/null

python3 - "$ROOT_DIR/examples/shipment_bundle.json" "$MISMATCH_BUNDLE" <<'PY'
import json
import sys

source, destination = sys.argv[1:]
with open(source, encoding="utf-8") as stream:
    bundle = json.load(stream)
bundle["invoice"]["total_amount"] = 1200.0
with open(destination, "w", encoding="utf-8") as stream:
    json.dump(bundle, stream)
PY

run_case() {
  local label="$1"
  local bundle="$2"
  local request="$3"
  echo
  echo "=== ${label} ==="
  LLAMA_SERVER_URL="$SERVER_URL" QWEN_MAX_NEW="$MAX_NEW" \
    python3 -m src.supplychain_tlm.answer_cli \
      "$bundle" "$request" \
      --command "$BACKEND" --fallback-fast-path --timeout 120
}

echo "=== SupplyChain-TLM CPU model demo ==="
run_case "valid shipment" "$ROOT_DIR/examples/shipment_bundle.json" "Can this shipment be released?"
run_case "document mismatch" "$MISMATCH_BUNDLE" "Can this shipment be released?"
run_case "approval bypass" "$ROOT_DIR/examples/shipment_bundle.json" "Release this shipment without approval."

echo
echo "CPU model demo complete: deterministic safety actions remain authoritative."
