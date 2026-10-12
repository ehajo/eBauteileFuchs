# Releaseprozess

Diese Anleitung bereitet eine Veröffentlichung vor. Sie erstellt selbst keinen
Git-Tag und kein GitHub-Release.

## Version und Changelog

Die maßgebliche Versionsnummer steht nur in
`src/ebauteilefuchs/__init__.py`; `pyproject.toml` liest sie dynamisch aus.
Für die erste öffentliche Vorabversion ist `0.1.0` vorgesehen. Vor jeder
Veröffentlichung sind Changelog, bekannte Einschränkungen und unterstützte
Migrationen zu prüfen.

## Release-Checkliste

1. Arbeitsbaum prüfen; `.env`, Datenbanken, Backups, Exporte und persönliche
   Daten dürfen nicht enthalten sein.
2. Vollständige lokale Prüfung ausführen:

   ```text
   ruff format --check .
   ruff check .
   pytest
   python scripts/verify-migrations.py
   ```

   Der Migrationscheck verwendet eine zufällig benannte SQLite-Datei in einem
   automatisch erzeugten System-Tempordner. Vor jedem Upgrade oder Downgrade
   prüft er hart, dass das Ziel weder die aus `.env` konfigurierte Datenbank
   noch eine Datenbank im regulären Datenverzeichnis ist. Die Testdatei wird
   nach erfolgreicher Prüfung entfernt. Direkte Alembic-Downgrades dürfen lokal
   nicht gegen die Nutzdatenbank ausgeführt werden.

3. Docker-Produktions- und Testimage bauen, den Testcontainer ausführen und
   Healthcheck, Datenpersistenz sowie den Ausschluss von `pytest` und `ruff`
   im Produktionsimage prüfen.
4. Auf einer frischen Windows- sowie Linux- oder Raspberry-Pi-Umgebung
   Installation, Upgrade, Smartphone-QR, Backup und Restore testen.
5. Lizenz, Drittkomponenten- und Brandinghinweise prüfen:
   `LICENSE`, `THIRD_PARTY_NOTICES.md`, `TRADEMARKS.md`, `SECURITY.md`.
6. Nach einer Sicherung Upgradehinweise und alle Alembic-Revisionen prüfen.

## Freigabehandlung

Erst nach expliziter Freigabe durch den Projektinhaber:

1. Versionsnummer und `CHANGELOG.md` finalisieren.
2. Einen signierten oder nachvollziehbar dokumentierten Git-Tag `vX.Y.Z`
   erstellen.
3. Ein GitHub-Release mit Release Notes, Upgrade- und Backuphinweisen erzeugen.
4. Quellarchiv und Wheel prüfen; eine PyPI-Veröffentlichung ist nicht Teil von
   Version 1.

Release Notes nennen mindestens Funktionsumfang, korrigierte Fehler,
Migrationshinweise, getestete Plattformen, bekannte Einschränkungen sowie
Lizenz- und Brandinghinweise.
