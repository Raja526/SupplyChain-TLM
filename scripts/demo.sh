#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

AUDIT_FILE="$(mktemp)"
trap 'rm -f "$AUDIT_FILE"' EXIT

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
echo "3) Audit trail"
wc -l "$AUDIT_FILE"
echo "PoC complete: validation, approval gate, dry-run ERP action, and audit log demonstrated."
