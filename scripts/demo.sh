#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

AUDIT_FILE="$(mktemp)"
INVALID_BUNDLE="$(mktemp)"
trap 'rm -f "$AUDIT_FILE" "$INVALID_BUNDLE"' EXIT

echo "=== SupplyChain-TLM CPU PoC ==="
echo
echo "1) Validate and prepare a shipment release (review-only)"
python3 -m src.supplychain_tlm.cli examples/shipment_bundle.json \
  --audit "$AUDIT_FILE"

echo
echo "2) Execute only after explicit procurement approval (dry run)"
python3 -m src.supplychain_tlm.cli examples/shipment_bundle.json \
  --approve-as procurement_manager \
  --audit "$AUDIT_FILE"

echo
echo "3) Safety check: mismatched invoice is blocked"
python3 - "$ROOT_DIR/examples/shipment_bundle.json" "$INVALID_BUNDLE" <<'PY'
import json
import sys

source, destination = sys.argv[1:]
bundle = json.load(open(source, encoding="utf-8"))
bundle["invoice"]["total_amount"] = 1200.0
json.dump(bundle, open(destination, "w", encoding="utf-8"))
PY
if python3 -m src.supplychain_tlm.cli "$INVALID_BUNDLE" --audit "$AUDIT_FILE"; then
  echo "ERROR: invalid shipment was not blocked"
  exit 1
else
  echo "blocked as expected: no ERP action executed"
fi

echo
echo "4) Audit trail"
wc -l "$AUDIT_FILE"
echo "PoC complete: validation, approval gate, dry-run ERP action, and audit log demonstrated."
