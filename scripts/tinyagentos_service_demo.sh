#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TINYAGENTOS_DIR="${TINYAGENTOS_DIR:-$HOME/TinyAgentOS}"
PORT="${SUPPLYCHAIN_DEMO_PORT:-8090}"
PYTHONPATH="$TINYAGENTOS_DIR:$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"

PYTHONPATH="$PYTHONPATH" python3 -m src.supplychain_tlm.service --host 127.0.0.1 --port "$PORT" >/tmp/supplychain-tlm-demo.log 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

ready=0
for _ in $(seq 1 20); do
  if curl -fsS "http://127.0.0.1:$PORT/healthz" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 0.1
done

if [ "$ready" -ne 1 ]; then
  echo "ERROR: SupplyChain-TLM service did not become ready" >&2
  cat /tmp/supplychain-tlm-demo.log >&2 || true
  exit 1
fi

echo "=== TinyAgentOS decision API demo ==="
curl -fsS "http://127.0.0.1:$PORT/v1/request" \
  -H 'Content-Type: application/json' \
  -d '{"operation":"decision","bundle":"examples/shipment_bundle.json","request":"Can this shipment be released?","approved":false}'
echo
