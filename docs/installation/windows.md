# Windows

Die native Entwicklungs- und Startmöglichkeit bleibt unabhängig von Docker
erhalten. Voraussetzung ist Python 3.12. In PowerShell im Repository:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

Das Skript installiert die lokalen Entwicklungsabhängigkeiten, führt Alembic-
Migrationen aus und startet die Anwendung. Mit `-NoBrowser` unterdrückt es nur
das automatische Öffnen des Browsers. Ist Port 8008 belegt, wählt es einen
freien Folgeport und öffnet genau diese Adresse.

Docker Desktop kann zusätzlich verwendet werden. Dafür `.env.example` nach
`.env` kopieren und dann in PowerShell ausführen:

```powershell
docker compose up -d --build
docker compose ps
```

Für den Docker-Testcontainer, persistente Daten, Backups und sicheres Stoppen
gilt die [Docker-Anleitung](docker.md). Docker Desktop ist keine Voraussetzung
für die native Windows-Nutzung.
