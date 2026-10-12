#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"

if [ ! -f .env ]; then
  echo "Es fehlt .env. Update abgebrochen." >&2
  exit 1
fi
echo "Vor einem Update eine Sicherung über die Oberfläche erstellen."
git pull --ff-only
docker compose up -d --build
docker compose ps
