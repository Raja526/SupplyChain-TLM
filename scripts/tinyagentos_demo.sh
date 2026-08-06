#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TINYAGENTOS_DIR="${TINYAGENTOS_DIR:-$HOME/TinyAgentOS}"
PYTHONPATH="$TINYAGENTOS_DIR:$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
  python3 "$ROOT_DIR/scripts/tinyagentos_demo.py"

