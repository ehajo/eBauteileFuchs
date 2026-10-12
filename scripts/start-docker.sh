#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"

if [ ! -f .env ]; then
  echo "Es fehlt .env. Zuerst .env.example nach .env kopieren und die LAN-Adresse setzen." >&2
  exit 1
fi
docker compose up -d --build
docker compose ps
