#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"

if [ ! -x .venv/bin/python ]; then
  echo "Keine lokale Installation gefunden. Zuerst scripts/install-linux.sh ausführen." >&2
  exit 1
fi

echo "Vor einem Update eine Sicherung über die Oberfläche erstellen."
git pull --ff-only
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation .
.venv/bin/python -m alembic upgrade head

if command -v systemctl >/dev/null 2>&1 && systemctl is-enabled --quiet ebauteilefuchs; then
  systemctl restart ebauteilefuchs
fi
echo "Update abgeschlossen. Healthcheck und Oberfläche bitte prüfen."
