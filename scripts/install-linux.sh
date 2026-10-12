#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"

if [ "$(id -u)" -eq 0 ]; then
  echo "Bitte nicht als root ausführen. Der systemd-Dienst nutzt einen eigenen Benutzer." >&2
  exit 1
fi

PYTHON=${PYTHON:-python3.12}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python 3.12 wurde nicht gefunden. Setze PYTHON auf einen passenden Interpreter." >&2
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  "$PYTHON" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation .
.venv/bin/python -m alembic upgrade head

echo "eBauteileFuchs ist installiert. Für systemd: scripts/install-systemd.sh als root ausführen."
