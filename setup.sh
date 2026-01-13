#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python and retry." >&2
  exit 1
fi

if [ ! -d "$ROOT_DIR/.venv" ]; then
  "$PYTHON_BIN" -m venv "$ROOT_DIR/.venv"
fi

# shellcheck disable=SC1091
source "$ROOT_DIR/.venv/bin/activate"

pip install --upgrade pip >/dev/null
pip install -r "$ROOT_DIR/requirements.txt"

echo "\nSetup complete."
echo "Run the service:" \
  "uvicorn app.main:app --host 127.0.0.1 --port 3717"

echo
if [ "${1:-}" = "--run" ]; then
  exec uvicorn app.main:app --host 127.0.0.1 --port 3717
fi
