# Linux-Server

Für einen x86-64-Linux-Server ist der Docker-Betrieb derselbe wie auf dem
Raspberry Pi. Docker wählt beim Build die Architektur des Hosts automatisch.

1. Docker Engine mit Compose-Plug-in nach der
   [offiziellen Docker-Anleitung](https://docs.docker.com/engine/install/)
   installieren und mit `docker compose version` prüfen.
2. Repository klonen, mit `cp .env.example .env` die lokale Konfiguration
   anlegen und `EBAUTEILEFUCHS_PUBLIC_BASE_URL` auf die feste LAN-Adresse
   setzen.
3. Mit `docker compose up -d --build` starten und mit
   `docker compose ps` sowie `/api/v1/health` prüfen.
4. Die Smartphone-Verbindungsseite aufrufen, QR-Code im gleichen WLAN testen
   und unter **Daten** eine Sicherung erstellen.
5. Für Aktualisierungen `git pull` und anschließend
   `docker compose up -d --build` ausführen.

Die vollständigen Befehle zu Testcontainer, Logs, Datenvolume, Stoppen und
Wiederherstellung stehen in der [Docker-Anleitung](docker.md). Native
Entwicklung bleibt mit `scripts/start-dev.sh` möglich.
