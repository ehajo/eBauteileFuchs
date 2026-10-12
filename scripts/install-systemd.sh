#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
APP_DIR=${EBAUTEILEFUCHS_APP_DIR:-/opt/ebauteilefuchs}
SERVICE_USER=${EBAUTEILEFUCHS_SERVICE_USER:-ebauteilefuchs}
ENV_DIR=/etc/ebauteilefuchs
ENV_FILE=$ENV_DIR/ebauteilefuchs.env

if [ "$(id -u)" -ne 0 ]; then
  echo "Dieses Skript benötigt root-Rechte, um Benutzer und systemd-Dienst einzurichten." >&2
  exit 1
fi
if [ "$PROJECT_ROOT" != "$APP_DIR" ]; then
  echo "Projekt muss für diese Standardvorlage unter $APP_DIR liegen (aktuell: $PROJECT_ROOT)." >&2
  exit 1
fi

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --home-dir /var/lib/ebauteilefuchs --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
fi
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 /var/lib/ebauteilefuchs
install -d -o root -g "$SERVICE_USER" -m 0750 "$ENV_DIR"
if [ ! -f "$ENV_FILE" ]; then
  install -o root -g "$SERVICE_USER" -m 0640 packaging/systemd/ebauteilefuchs.env.example "$ENV_FILE"
  echo "Environment-Datei angelegt: $ENV_FILE"
fi
install -o root -g root -m 0644 packaging/systemd/ebauteilefuchs.service /etc/systemd/system/ebauteilefuchs.service
systemctl daemon-reload
systemctl enable --now ebauteilefuchs
systemctl --no-pager status ebauteilefuchs
