# eBauteileFuchs

**Clever finden statt lange suchen.**

eBauteileFuchs ist eine lokal betriebene Open-Source-Lagerverwaltung
für Elektronikbauteile, Kleinteile und private Bastellager.

> Ein Open-Source-Projekt von eHaJo – <https://www.ehajo.de>

## Projektstatus

Meilenstein M3 ist umgesetzt: Neben Lagerplätzen und Artikelstammdaten stehen ein
unveränderliches Bestandsjournal, schnelle Salden je Artikel und Lagerplatz sowie
initiale Bestände, Ein-, Aus-, Um- und Korrekturbuchungen bereit. M2 wurde lokal
abgenommen; die lokale M3-Abnahme steht aus.

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
- Artikel: <http://127.0.0.1:8008/articles>
- Lagerplätze: <http://127.0.0.1:8008/locations>
- Bestand: <http://127.0.0.1:8008/inventory>
- Einlagern: <http://127.0.0.1:8008/inventory/stock-in>
- Auslagern: <http://127.0.0.1:8008/inventory/stock-out>
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

`requirements.lock` und `requirements-dev.lock` halten die für M3 geprüften
Abhängigkeiten reproduzierbar fest.

## Bestand buchen

**Bestand**, **Einlagern** und **Auslagern** sind direkt in der Hauptnavigation
erreichbar. Artikel können gesucht oder mit einem tastaturartigen USB-Scanner
samt Enter eingegeben und direkt aus der Ergebnisliste gewählt werden. Beim
Auslagern stehen anschließend nur Lagerplätze mit Bestand für diesen Artikel zur
Wahl. Eine über „Hier einlagern“ getroffene Lagerplatzauswahl bleibt während der
Artikelsuche erhalten. Artikel- und Lagerplatzdetailseiten zeigen aktuelle
Mengen, Lagerpfade und letzte Bewegungen. Ein Lagerplatz-QR öffnet denselben
Kontext mit passenden Buchungsaktionen auf dem Smartphone.

Auslagerungen bieten die Schnellmengen 1, 5 und den gesamten Bestand. Umlagerungen
schreiben Entnahme und Zugang atomar unter einer gemeinsamen Vorgangskennung.
Korrekturen erfassen entweder eine positive/negative Differenz oder rechnen einen
gezählten Zielbestand in eine zusätzliche Journalbewegung um. Mengen verwenden
Dezimalwerte mit höchstens acht Nachkommastellen; Standard ist `Stück`.

Jeder Schreibaufruf der REST-API benötigt den Header `Idempotency-Key`. Eine
identische Wiederholung liefert die ursprüngliche Buchung zurück; derselbe
Schlüssel mit anderem Inhalt wird abgewiesen. Die vollständigen M3-Verträge sind
in der [API-Dokumentation](docs/API.md) beschrieben.

## Artikelverwaltung

Unter **Artikel** können Bauteile mit Original-Herstellerartikelnummer,
Kategorie, Beschreibung, Links, Notizen, typischen oder freien Eigenschaften und
mehreren Lieferantenartikelnummern angelegt werden. Vor dem Speichern prüft
eBauteileFuchs sichere Identitäten und ähnliche Kandidaten. Ähnlichkeitswarnungen
müssen ausdrücklich bestätigt werden; sichere Treffer können nicht als neuer
Artikel übergangen werden.

Bei typischen technischen Eigenschaften wird der Zahlenwert getrennt von einer
passenden Einheit erfasst. Die Auswahl bietet gebräuchliche SI-Vorsätze wie
`pF`, `nF`, `µF`, `mF` oder `F` sowie `mΩ`, `Ω`, `kΩ`, `MΩ` und `GΩ` an. Freie
Eigenschaften schlagen dieselben Einheiten vor, erlauben aber weiterhin eigene
Angaben.

Die lokale Suche verknüpft mehrere Suchwörter mit UND und berücksichtigt Namen,
Hersteller, Artikelnummern, Eigenschaften, Notizen und Lieferantennummern.

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

Für kleine 60er-Magazine steht auf der Lagerplatzdetailseite zusätzlich ein
35 × 13-mm-Kompaktetikett bereit. Im Magazin-Assistenten können Schubladen
optional automatisch mit den Unterfächern A und B angelegt werden.

Ein noch unbenutzter Lagerplatz kann über seine Detailseite nach einer
Sicherheitsabfrage endgültig gelöscht werden. Sobald Unterplätze, Bestände oder
Bestandsbewegungen darauf verweisen, bleibt er zur Nachvollziehbarkeit erhalten
und kann stattdessen deaktiviert werden.

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
- [Interne REST-API](docs/API.md)
- [Manuelle M3-Abnahme](docs/MANUAL_TEST_M3.md)

Version 1 ist als responsive lokale Webanwendung für Raspberry Pi, Linux und
Windows vorgesehen. Kerntechnologien sind Python 3.12, FastAPI, SQLAlchemy,
SQLite, Alembic und Jinja2; HTMX wird mit den interaktiven Abläufen ergänzt.

## Lizenz und Marken

Der Programmcode steht unter der [Apache License 2.0](LICENSE). Diese Lizenz
gewährt keine Rechte an eHaJo, eBauteileFuchs, Logo, einem späteren
Fuchs-Maskottchen oder anderen Brandingbestandteilen. Es gelten die Hinweise in
[TRADEMARKS.md](TRADEMARKS.md). Das vorhandene eHaJo-Logo darf nicht verändert
oder nachgezeichnet werden.
