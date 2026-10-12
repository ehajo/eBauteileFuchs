#!/usr/bin/env sh
set -eu

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl ist auf diesem System nicht verfügbar." >&2
  exit 1
fi
systemctl --no-pager status ebauteilefuchs
