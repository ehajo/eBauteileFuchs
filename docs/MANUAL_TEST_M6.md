# Manuelle Abnahme M6 unter Windows

Diese Prüfung verwendet eine Testkopie deiner Daten. Den normalen Server vorher
beenden und den produktiven Datenordner nicht verändern.

1. Eine Kopie des Datenordners anlegen und in einer nicht versionierten `.env`
   als `EBAUTEILEFUCHS_DATA_DIR` eintragen.
2. In PowerShell `powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1`
   ausführen. Nur diesen selbst gestarteten Server verwenden.
3. Startseite, `/api/v1/health`, Artikel, Lagerplätze und Bestand öffnen.
4. Unter **Daten** alle vier CSV-Dateien herunterladen. Umlaute, Original-
   Herstellerartikelnummern, Lieferantennummern, Werte/Einheiten, Lagerpfade und
   Dezimalmengen stichprobenartig prüfen.
5. **Sicherung erstellen** wählen. Download und zusätzliche ZIP-Datei im
   angezeigten Sicherungsordner prüfen.
6. Einen eindeutig erkennbaren Testartikel in der Testkopie ändern.
7. Die ZIP-Datei unter **Sicherung wiederherstellen** auswählen, Prüfvorschau
   kontrollieren, `WIEDERHERSTELLEN` eingeben und bestätigen.
8. Anwendung mit `Strg+C` beenden und per PowerShell neu starten. Die Änderung
   aus Schritt 6 muss zurückgesetzt sein; Health-Check, Artikel, Lagerplätze,
   Bestand und Journal müssen funktionieren.
9. Im Sicherungsordner muss zusätzlich eine `vorsicherung` vorhanden sein.
10. Fehlerfälle prüfen: umbenannte Textdatei, beschädigte ZIP-Kopie, falscher
    Bestätigungstext und zu große Datei. Die laufenden Daten dürfen sich nicht
    ändern und die Meldung muss verständlich sein.
11. Browser auf Smartphonebreite ziehen. Karten, Dateiauswahl, Prüfsumme und
    Bestätigung müssen ohne horizontales Seitenrollen bedienbar sein.

## Docker-Abnahme unter Windows

Docker Desktop ist optional. Falls es installiert ist, die normale native
Anwendung beenden und in einer eigenen Testkopie des Repositorys prüfen:

1. `.env.example` nach `.env` kopieren, eine Test-LAN-Adresse eintragen und
   keinen echten Mouser-Schlüssel verwenden.
2. `docker compose config` ausführen und kontrollieren, dass `app` das Ziel
   `production` und `test` das Profil `test` mit Ziel `test` verwendet.
3. `docker compose up -d --build`, `docker compose ps` und
   `http://127.0.0.1:8008/api/v1/health` prüfen. Der App-Service muss
   `healthy` werden; Startseite, Artikel, Lagerplätze und Bestand öffnen.
4. Einen eindeutig erkennbaren Testartikel anlegen, dann
   `docker compose restart app` ausführen und die Daten erneut prüfen.
5. `docker compose down` und anschließend `docker compose up -d --build`
   ausführen. Die Daten müssen weiterhin vorhanden sein.
6. `docker compose --profile test run --rm test pytest` ausführen. Der Lauf
   darf nicht auf die Produktivdaten zugreifen.
7. Mit folgendem Befehl kontrollieren, dass beide Werkzeuge im
   Produktionsimage nicht installiert sind:

   ```powershell
   docker compose exec app python -c "import importlib.util; assert importlib.util.find_spec('pytest') is None; assert importlib.util.find_spec('ruff') is None"
   ```
8. Zum Abschluss `docker compose down` ausführen. **Nicht** `down -v`
   verwenden; dieses würde das Testvolume samt Daten löschen.

Systemd, Windows-Paketierung, GitHub-Release, Git-Tag und automatische
Veröffentlichung bleiben ausdrücklich M7 oder später vorbehalten.
