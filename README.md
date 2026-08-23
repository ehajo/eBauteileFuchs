# eBauteileFuchs

**Clever finden statt lange suchen.**

eBauteileFuchs ist eine lokal betriebene Open-Source-Lagerverwaltung
für Elektronikbauteile, Kleinteile und private Bastellager.

> Ein Open-Source-Projekt von eHaJo – <https://www.ehajo.de>

## Projektstatus

Meilenstein M1 ist umgesetzt: Neben dem technischen Fundament stehen jetzt eine
hierarchische Lagerplatzverwaltung, ein Magazin-Assistent für fortlaufend
nummerierte Schubladen, stabile Lagerplatz-QR-Codes und PDF-Etiketten bereit.
Artikel- und Bestandsfunktionen folgen erst in späteren Meilensteinen.

## Schnellstart unter Windows

Voraussetzung ist Python 3.12. In PowerShell im Repository:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

Das Skript legt `.venv` an, installiert die Entwicklungsabhängigkeiten, führt
Migrationen aus, öffnet den Standardbrowser und startet den Server. Ohne
automatische Browseröffnung:

```powershell
.\scripts\start-dev.ps1 -NoBrowser
```

Ist Port 8008 bereits belegt, wählt das Windows-Entwicklungsskript automatisch
den nächsten freien Port und zeigt die verwendete Adresse im Terminal an.

## Schnellstart unter Linux

Voraussetzungen sind Python 3.12 und das zugehörige `venv`-Paket.

```bash
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

## Docker

Docker ist optional; Daten bleiben in einem benannten Volume erhalten.

```text
docker compose up --build
```

## Browser und Systemstatus

Nach dem Start:

- Startseite: <http://127.0.0.1:8008>
- Lagerplätze: <http://127.0.0.1:8008/locations>
- Health-Check: <http://127.0.0.1:8008/api/v1/health>
- OpenAPI: <http://127.0.0.1:8008/docs>

Der Server bindet standardmäßig an `0.0.0.0:8008`. Die komfortable
Verbindungsseite samt Netzwerkadressauswahl und QR-Code folgt erst in M5.

## Manuelle Entwicklungsbefehle

Nach Aktivierung einer Python-3.12-Umgebung:

```text
python -m pip install -r requirements.lock -r requirements-dev.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m alembic upgrade head
python -m ebauteilefuchs
```

`requirements.lock` und `requirements-dev.lock` halten die für M1 geprüften
Abhängigkeiten reproduzierbar fest.

## Lagerplätze und Etiketten

Unter **Lagerplätze** können Räume, Schränke, Regale, Magazine, Schubladen,
Unterfächer, Boxen und Kisten hierarchisch angelegt werden. Eigene Typen lassen
sich unter **Typen** ergänzen. Der Magazin-Assistent erzeugt standardmäßig 60
Schubladen (`01` bis `60`) erst nach einer konfliktfreien Vorschau atomar.

Die Detailseite bietet ein universelles Einzeletikett. In der Baumansicht können
mehrere Lagerplätze für einen A4-Sammelbogen ausgewählt werden. Das Standardraster
ist 70 × 36 mm mit 24 Etiketten pro A4-Seite (3 × 8). Für dauerhaft gedruckte
Smartphone-QR-Codes sollte `EBAUTEILEFUCHS_PUBLIC_BASE_URL` auf eine im lokalen
Netz stabile Adresse gesetzt werden; die geführte Verbindungsseite folgt in M5.

Qualitätsprüfung:

```text
ruff format --check .
ruff check .
pytest
```

Lokale Einstellungen können aus `.env.example` in eine nicht versionierte
`.env` übernommen werden. Details stehen in
[Konfiguration](docs/configuration.md).

## Planungsdokumente

- [Produktspezifikation](docs/PRODUCT_SPEC.md)
- [Architektur](docs/ARCHITECTURE.md)
- [Datenmodell](docs/DATA_MODEL.md)
- [UX-Abläufe](docs/UX_FLOWS.md)
- [Implementierungsplan](docs/IMPLEMENTATION_PLAN.md)
- [Vorgeschlagene Repositorystruktur](docs/REPOSITORY_STRUCTURE.md)
- [Offene Entscheidungen](docs/OPEN_DECISIONS.md)

Version 1 ist als responsive lokale Webanwendung für Raspberry Pi, Linux und
Windows vorgesehen. Kerntechnologien sind Python 3.12, FastAPI, SQLAlchemy,
SQLite, Alembic und Jinja2; HTMX wird mit den interaktiven Abläufen ergänzt.

## Lizenz und Marken

Der Programmcode steht unter der [Apache License 2.0](LICENSE). Diese Lizenz
gewährt keine Rechte an eHaJo, eBauteileFuchs, Logo, einem späteren
Fuchs-Maskottchen oder anderen Brandingbestandteilen. Es gelten die Hinweise in
[TRADEMARKS.md](TRADEMARKS.md). Das vorhandene eHaJo-Logo darf nicht verändert
oder nachgezeichnet werden.
