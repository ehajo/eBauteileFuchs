#!/bin/sh
set -eu

echo "eBauteileFuchs: Datenbankschema wird geprüft."
if ! alembic upgrade head; then
    echo "eBauteileFuchs: Migration fehlgeschlagen; Anwendung wird nicht gestartet." >&2
    exit 1
fi

echo "eBauteileFuchs: Anwendung wird gestartet."
exec python -m ebauteilefuchs
