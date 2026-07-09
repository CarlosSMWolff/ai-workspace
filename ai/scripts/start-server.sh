#!/usr/bin/env sh
set -eu

PORT="${1:-8000}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

echo "Research dashboard: http://127.0.0.1:${PORT}/"
exec python3 "$SCRIPT_DIR/serve.py" --port "$PORT"
