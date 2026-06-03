#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PORT="${PORT:-8000}"
OPEN_BROWSER="${OPEN_BROWSER:-1}"

log() {
  printf '[generic-ml] %s\n' "$1"
}

find_python() {
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" --version 2>/dev/null | grep -q 'Python 3'; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

port_available() {
  local port="$1"
  "$PYTHON_BIN" - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        raise SystemExit(1)
PY
}

find_free_port() {
  local start="$1"
  local candidate
  for candidate in $(seq "$start" "$((start + 20))"); do
    if port_available "$candidate"; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="$(find_python)" || {
  echo "Python 3 was not found. Please install Python 3.11+ and retry." >&2
  exit 1
}

if [ ! -x ".venv/bin/python" ]; then
  log "Creating virtual environment..."
  "$PYTHON_BIN" -m venv .venv
fi

VENV_PYTHON=".venv/bin/python"
log "Upgrading pip..."
"$VENV_PYTHON" -m pip install --upgrade pip

log "Installing dependencies from requirements.txt..."
"$VENV_PYTHON" -m pip install -r requirements.txt

log "Applying database migrations..."
"$VENV_PYTHON" manage.py migrate

SELECTED_PORT="$(find_free_port "$PORT")" || {
  echo "No free port found from $PORT to $((PORT + 20))." >&2
  exit 1
}
URL="http://127.0.0.1:${SELECTED_PORT}/"
log "Starting server at $URL"

if [ "$OPEN_BROWSER" = "1" ]; then
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "$URL" >/dev/null 2>&1 || true
  fi
fi

"$VENV_PYTHON" manage.py runserver "127.0.0.1:${SELECTED_PORT}" --noreload
