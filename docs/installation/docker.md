# Docker-Betrieb

Docker ist optional. Für die native Windows-Entwicklung bleibt
`scripts/start-dev.ps1` der vorgesehene Weg. Diese Anleitung verwendet bewusst
die aktuelle Compose-Schreibweise `docker compose`.

## Erststart

1. Docker Engine mit Compose-Plug-in (oder Docker Desktop unter Windows)
   installieren und prüfen:

   ```bash
   docker --version
   docker compose version
   ```

2. Im Repository die lokale Konfiguration anlegen. Die echte `.env` bleibt
   lokal und wird weder gebaut noch versioniert:

   ```bash
   cp .env.example .env
   ```

3. In `.env` mindestens die dauerhafte LAN-Adresse anpassen, zum Beispiel:

   ```text
   EBAUTEILEFUCHS_PUBLIC_BASE_URL=http://192.168.1.42:8008
   ```

   Host, Port, Datenpfad, Backupziel, Log-Level und der optionale
   Mouser-Schlüssel verwenden unverändert die in
   [Konfiguration](../configuration.md) beschriebenen Variablen. Der
   Mouser-Schlüssel gehört ausschließlich in die lokale `.env`.

4. Produktion bauen und im Hintergrund starten:

   ```bash
   docker compose up -d --build
   ```

5. Zustand und Healthcheck kontrollieren:

   ```bash
   docker compose ps
   docker compose logs -f app
   ```

   `app` muss den Status `healthy` erreichen. Anschließend
   `http://SERVER-IP:8008/api/v1/health` und die Startseite im Browser öffnen.

## Daten und Migrationen

Der Service `app` baut ausdrücklich das Docker-Ziel `production`. Vor dem
Webstart führt sein Startskript `alembic upgrade head` aus. Bei einem
Migrationsfehler endet der Container; es startet kein teilweise aktualisierter
Webprozess. Der vorhandene Health-Endpunkt `/api/v1/health` prüft danach
regelmäßig den laufenden Dienst.

Die SQLite-Datenbank, ZIP-Sicherungen, Exporte und Restore-Zwischendateien
liegen im benannten Volume `ebauteilefuchs-data` bei `/data`. Dieses Volume
überlebt sowohl einen Containerneustart als auch:

```bash
docker compose down
docker compose up -d --build
```

**Warnung:** `docker compose down -v` löscht das Volume einschließlich aller
produktiven Lagerdaten. Diesen Befehl nur nach einer geprüften Sicherung und
mit ausdrücklicher Löschabsicht verwenden.

Für Sicherungen und Wiederherstellungen immer die Oberfläche unter **Daten**
verwenden. Sie erzeugt konsistente SQLite-Snapshots, prüft Manifest und
Prüfsumme und legt vor einer Wiederherstellung automatisch eine Vorsicherung
an. Keine laufende SQLite-Datei direkt aus dem Volume kopieren. Details stehen
in [CSV, Sicherung und Wiederherstellung](../BACKUP_RESTORE.md).

## Tests

Der Service `test` verwendet ausschließlich das Docker-Ziel `test` und ist
nur mit dem Compose-Profil `test` aktiv. Er erhält kein produktives Volume,
keine `.env` und nutzt `/tmp/ebauteilefuchs` als flüchtigen Datenordner.
Anders als die Produktion erhält er den bereinigten Repository-Kontext, weil
Vertragstests bewusst lokale Dokumentationslinks, Branding-Originale und die
Docker-Konfiguration prüfen. Docker stellt `Dockerfile` und `.dockerignore`
nicht direkt für `COPY` bereit; deshalb liegen bytegleich geprüfte Testkopien
unter `packaging/docker/test-repository-context/`. Sie sind nur für das
Testziel bestimmt und werden nie in das Produktionsimage kopiert.

```bash
docker compose --profile test run --rm test pytest
```

Weitere pytest-Argumente werden direkt angehängt, beispielsweise:

```bash
docker compose --profile test run --rm test pytest -q tests/integration
```

Das Produktionsimage enthält nur die Laufzeitabhängigkeiten. `pytest` und
`ruff` werden ausschließlich im Ziel `test` installiert.

## Betrieb

```bash
# Anhalten ohne Datenverlust
docker compose down

# Aktualisierung
git pull
docker compose up -d --build

# Aktuelle Protokolle
docker compose logs -f app
```

Nach einem Update zunächst `docker compose ps`, den Health-Endpunkt, die
Startseite und eine Stichprobe aus Artikeln, Lagerplätzen und Bestand prüfen.
