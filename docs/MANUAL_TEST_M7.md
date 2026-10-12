# Manuelle Abnahme M7

Diese Checkliste ergänzt die automatisierten Tests. Sie erzeugt weder einen Tag
noch ein GitHub-Release.

## Windows und Docker Desktop

1. Docker Desktop starten und im Repository eine sichere lokale `.env` aus
   `.env.example` erzeugen. Keinen echten Mouser-Schlüssel für diesen Test
   verwenden.
2. Konfiguration und Images prüfen:

   ```powershell
   docker compose config
   docker compose build app
   docker compose --profile test build test
   docker compose --profile test run --rm test pytest
   ```

3. Produktion starten und prüfen:

   ```powershell
   docker compose up -d
   docker compose ps
   Invoke-WebRequest http://127.0.0.1:8008/api/v1/health
   ```

   Der Service muss `healthy` werden, die Antwort Version `0.1.0` enthalten und
   Startseite sowie `/about` müssen erreichbar sein.

4. Sicherstellen, dass das Produktionsimage keine Testwerkzeuge enthält:

   ```powershell
   docker compose exec app python -c "import importlib.util; assert importlib.util.find_spec('pytest') is None; assert importlib.util.find_spec('ruff') is None"
   ```

5. Einen synthetischen Testartikel anlegen, `docker compose restart app`
   ausführen und die Daten erneut prüfen. Danach `docker compose down` und
   `docker compose up -d` wiederholen. Daten müssen erhalten bleiben.
6. Mit `docker compose down` beenden. **Nicht** `docker compose down -v`
   verwenden: Dieser Befehl löscht das Datenvolume.

## Raspberry Pi OS 64-Bit

1. Auf einem frischen Raspberry Pi OS 64-Bit Docker mit Compose-Plug-in oder
   Python 3.12 für die native Variante installieren.
2. Repository klonen, `.env.example` nach `.env` kopieren und eine feste
   LAN-Basis-URL konfigurieren.
3. Docker: `docker compose up -d --build` und `docker compose ps`; nativ:
   [Linux-Anleitung](installation/linux.md) einschließlich systemd befolgen.
4. `/api/v1/health`, `/about`, Artikel, Lagerplätze, Bestandsbuchung,
   Smartphone-QR und eine ZIP-Sicherung praktisch prüfen.
5. Update mit Sicherung davor testen; danach Datenbankrevision und vorhandene
   Daten kontrollieren.

## Öffentliche Veröffentlichung

Vor einer Veröffentlichung `LICENSE`, `TRADEMARKS.md`,
`THIRD_PARTY_NOTICES.md`, `SECURITY.md`, Screenshots und Changelog persönlich
prüfen. Anschließend erst nach ausdrücklicher Freigabe dem
[Releaseprozess](release-process.md) folgen.
