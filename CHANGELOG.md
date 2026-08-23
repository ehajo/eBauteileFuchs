# Changelog

Alle wesentlichen Änderungen an eBauteileFuchs werden in dieser Datei
dokumentiert. Das Format orientiert sich an Keep a Changelog; Versionen folgen
Semantic Versioning.

## [Unreleased]

### Added

- M0-Projektfundament mit FastAPI, SQLite, Alembic, Jinja2 und zentraler
  Konfiguration.
- Gebrandete Startseite und Health-Check.
- Entwicklungsstarts für Windows und Linux sowie Docker-Grundlage.
- Apache-2.0-Lizenz und getrennte Markenhinweise.

### Fixed

- Der Windows-Entwicklungsstart wählt bei belegtem Standardport verständlich den
  nächsten freien Port, statt mit einem Uvicorn-Bindefehler abzubrechen.
- Der Standardport wurde vom häufig belegten Port 8080 auf Port 8008 geändert.
