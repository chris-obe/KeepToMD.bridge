#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python and retry." >&2
  exit 1
fi

PY_VERSION="$($PYTHON_BIN -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
PY_MAJOR=${PY_VERSION%%.*}
PY_MINOR=${PY_VERSION##*.}

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]; }; then
  echo "Python 3.8+ is required. Current: $PY_VERSION" >&2
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
