# Vorgeschlagene Repositorystruktur

Status: Grundsätzlich freigegeben am 23. August 2026. Die Struktur wird jeweils
im Umfang des ausdrücklich freigegebenen Meilensteins angelegt.

```text
eBauteileFuchs/
├── AGENTS.md
├── README.md
├── LICENSE                         # erst nach Lizenzfreigabe
├── TRADEMARKS.md                   # getrennte Marken-/Asset-Regeln
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── .env.example
├── .gitignore
├── pyproject.toml
├── alembic.ini
├── Dockerfile
├── compose.yaml
├── branding/
│   ├── branding.md
│   ├── ehajo-logo.svg
│   ├── ehajo-logo.png
│   └── README.md                   # Nutzung/Rechte der Assets
├── docs/
│   ├── PRODUCT_SPEC.md
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── MANUAL_TEST_M3.md
│   ├── MANUAL_TEST_M5.md
│   ├── MOUSER.md
│   ├── DATA_MODEL.md
│   ├── UX_FLOWS.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── REPOSITORY_STRUCTURE.md
│   ├── OPEN_DECISIONS.md
│   ├── adr/
│   ├── installation/
│   │   ├── raspberry-pi.md
│   │   ├── linux.md
│   │   ├── windows.md
│   │   └── docker.md
│   ├── backup-restore.md
│   ├── configuration.md
│   └── release-process.md
├── src/
│   └── ebauteilefuchs/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── branding.py
│       ├── domain/
│       │   ├── articles.py
│       │   ├── inventory.py
│       │   ├── locations.py
│       │   ├── normalization.py
│       │   └── errors.py
│       ├── application/
│       │   ├── articles.py
│       │   ├── duplicates.py
│       │   ├── inventory.py
│       │   ├── locations.py
│       │   ├── search.py
│       │   ├── backup.py
│       │   └── ports/
│       ├── persistence/
│       │   ├── models.py
│       │   ├── repositories.py
│       │   ├── session.py
│       │   └── unit_of_work.py
│       ├── suppliers/
│       │   ├── base.py
│       │   └── mouser/
│       │       ├── client.py
│       │       ├── mapper.py
│       │       └── schemas.py
│       ├── api/
│       │   ├── dependencies.py
│       │   ├── schemas/
│       │   └── v1/
│       ├── web/
│       │   ├── routes/
│       │   ├── forms.py
│       │   └── viewmodels.py
│       ├── platform/
│       │   ├── network.py
│       │   └── paths.py
│       ├── templates/
│       └── static/
├── migrations/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   ├── e2e/
│   ├── fixtures/
│   │   └── mouser/                 # anonymisierte API-Fixtures
│   └── conftest.py
├── scripts/
│   ├── install-linux.sh
│   ├── start-dev.ps1
│   ├── backup.py
│   └── restore.py
├── packaging/
│   ├── systemd/
│   ├── windows/
│   └── docker/
├── examples/
│   └── demo-data/                  # ausschließlich synthetische Daten
├── data/
│   └── .gitkeep                    # Entwicklung; Inhalte ignoriert
└── .github/
    ├── workflows/
    ├── ISSUE_TEMPLATE/
    └── pull_request_template.md
```

## Begründete Abweichungen vom groben Vorschlag

- `domain`, `application` und `persistence` ersetzen ein allgemeines `models`-
  Verzeichnis. So bleiben Fachobjekte, Use Cases und ORM klar getrennt.
- HTML-Routen liegen in `web`, JSON-Routen in `api`; beide verwenden
  `application`.
- Betriebspakete liegen in `packaging`, einmalige Entwickler-/Adminwerkzeuge in
  `scripts`.
- `compose.yaml` folgt dem aktuellen neutralen Compose-Dateinamen; eine spätere
  Entscheidung kann aus Kompatibilitätsgründen `docker-compose.yml` wählen.
- `TRADEMARKS.md` trennt Code-Lizenz von eHaJo-, Produkt-, Logo- und
  Maskottchenrechten.
- Laufzeitdaten liegen bei Installationen bevorzugt in Plattform-Datenpfaden.
  `data/` ist nur ein ignorierter Entwicklungsort, keine fest verdrahtete
  Produktionsablage.

## Paketgrenzen

`domain` importiert keine anderen Projektbereiche. `application` darf `domain`
und Port-Protokolle verwenden. `persistence`, `suppliers`, `platform`, `web` und
`api` sind Adapter; sie dürfen nach innen importieren, werden aber nicht von
Domainmodulen importiert. Diese Regeln sollen später mit Tests beziehungsweise
einem Import-Linter abgesichert werden, sofern dafür keine unverhältnismäßige
Zusatzabhängigkeit nötig ist.

## In M1 realisierte Ergänzungen

- `domain/locations.py` und `application/locations.py` enthalten Regeln und Use
  Cases der Lagerhierarchie.
- `application/ports/locations.py` und `application/ports/labels.py` definieren
  die Persistenz- und Ausgabeverträge.
- `persistence/locations.py` kapselt Repository und Unit of Work;
  `labels/renderer.py` erzeugt QR-SVG und PDF vollständig offline.
- `api/v1/locations.py`, `web/locations.py` und `templates/locations/` bilden die
  JSON- beziehungsweise HTML-Eingänge ab.

## In M2 realisierte Ergänzungen

- `domain/articles.py` enthält Artikelobjekte und deterministische
  Normalisierungs- und Validierungsregeln.
- `application/articles.py` koordiniert Referenzdaten, Artikel, Eigenschaften,
  Lieferantennummern, Suche und Dublettenstufen.
- `persistence/articles.py` und `persistence/article_catalog.py` implementieren
  Repository, Unit of Work und stabile Startdaten.
- `api/v1/articles.py`, `web/articles.py` und `templates/articles/` bilden die
  REST- und responsive HTML-Oberfläche ab.

## In M3 realisierte Ergänzungen

- `domain/inventory.py` enthält Dezimalmengen, Transaktionsarten, Salden,
  Bewegungen und Buchungsergebnisse.
- `application/inventory.py` koordiniert Initial-, Ein-, Aus-, Um- und
  Korrekturbuchungen sowie Idempotenz und Negativbestandsschutz.
- `application/ports/inventory.py` und `persistence/inventory.py` kapseln das
  Journal, materialisierte Salden und die SQLite-Schreibserialisierung.
- `api/v1/inventory.py`, `web/inventory.py`, `templates/inventory/` und das lokale
  `static/js/inventory.js` bilden REST-, Scan- und mobile HTML-Abläufe ab.

## In M4 realisierte Ergänzungen

- `domain/suppliers.py`, `application/ports/suppliers.py` und
  `application/supplier_search.py` bilden neutrale Lieferantenprodukte und Use
  Cases ohne Mouser-Abhängigkeit ab.
- `suppliers/mouser/` trennt HTTP-Kommunikation, Antwortschema, Mapping und den
  offiziellen Adapter.
- `persistence/supplier_cache.py` sowie Revision `0005_m4_supplier_cache`
  implementieren den allgemeinen Cachevertrag; Mouser-Schreibzugriffe bleiben
  aus Vertragsgründen deaktiviert.
- Revision `0006_unassigned_location` ergänzt den internen Systemlagerplatz für
  revisionssicher archivierte Lagerzweige; er erscheint nicht in normalen
  Lagerplatzbäumen oder Zielauswahlen.
- `api/v1/suppliers.py`, `web/suppliers.py` und `templates/suppliers/` bilden
  REST-, Scan-, Auswahl-, Prüf- und Importabläufe ab.

## In M5 realisierte Ergänzungen

- `application/search.py` führt die portable globale UND-Suche aus;
  `api/v1/search.py`, `web/search.py` und `templates/search/` stellen sie bereit.
- `platform/network.py` erkennt lokale IPv4-Adressen; `application/connection.py`,
  `web/connection.py` und `templates/connection/` bilden URL-Auswahl und
  Verbindungs-QR ab.
- `static/manifest.webmanifest`, `static/service-worker.js`, `static/js/pwa.js`
  und `templates/offline.html` bilden die App-Shell ohne Offline-Fachdaten.
- `static/js/barcode-scanner.js` kapselt Foto- und Live-Kamera-Scan für die
  Verpackungsbarcode-Suche bei Mouser. Der fest versionierte Decoder unter
  `static/vendor/zxing-wasm/` wertet Fotos lokal aus; Herkunft und Lizenz stehen
  in `THIRD_PARTY_NOTICES.md`.
- Revision `0007_article_barcodes` bleibt ausschließlich als Kompatibilitäts-
  revision für bereits aktualisierte Entwicklungsdatenbanken erhalten; ihre
  Tabelle wird fachlich nicht verwendet.

## In M6 realisierte Ergänzungen

- `application/data_management.py` definiert Dienst, sichere Fehler und
  Backup-/Restore-Ergebnisse.
- `persistence/data_management.py` erzeugt CSV und konsistente SQLite-
  Sicherungen, prüft ZIP/Manifest und tauscht validierte Daten atomar aus.
- `web/data_management.py` und `templates/data/` bilden Export, Sicherung,
  Prüfvorschau und ausdrücklich bestätigte Wiederherstellung ab.
- `docs/BACKUP_RESTORE.md` dokumentiert CSV-Verträge, Format und Notfallablauf;
  `docs/MANUAL_TEST_M6.md` beschreibt die Windows-Abnahme.
- Revision `0008_location_grid` speichert optionale Spalten-/Reihenangaben für
  die grafische Lagerübersicht und ist vorwärts sowie rückwärts ausführbar.
- `Dockerfile` besitzt die getrennten Ziele `production` und `test`;
  `packaging/docker/entrypoint.sh` führt die kontrollierte Migration vor dem
  Produktionsstart aus. `compose.yaml` verbindet nur den App-Service mit dem
  persistenten Volume und aktiviert Tests ausschließlich über das Profil `test`.
