# Changelog

Alle wesentlichen Änderungen an eBauteileFuchs werden in dieser Datei
dokumentiert. Das Format orientiert sich an Keep a Changelog; Versionen folgen
Semantic Versioning.

## [Unreleased]

### Added

- M2-Artikelverwaltung mit Herstellern, Kategorien, flexiblen technischen
  Eigenschaften, Lieferantenartikelnummern und lokaler UND-Suche.
- Vierstufige Dublettenerkennung für Lieferantennummern, exakte und normalisierte
  Herstelleridentitäten sowie bewusst bestätigbare Ähnlichkeitswarnungen.
- Responsive Artikelübersicht, Detail- und Bearbeitungsformulare sowie
  entsprechende `/api/v1`-Ressourcen.
- Kompaktes Lagerplatzetikett mit 35 × 13 mm für kleine Magazin-Schubladen.
- Direktes Anlegen eines Unterplatzes aus einer Lagerplatzdetailseite und
  optionale Unterteilung jeder Magazin-Schublade in Unterfach A und B.
- M1-Lagerplatzverwaltung mit System- und eigenen Typen, Hierarchie, Pfadansicht,
  Bearbeitung und kontrollierter Deaktivierung.
- Atomarer Magazin-Assistent mit Vorschau und Voreinstellung für 60 Schubladen.
- Stabile Lagerplatz-QR-Tokens sowie universelle Einzel- und A4-Sammeletiketten
  im Standardformat 70 × 36 mm (3 × 8).
- Versionierte REST-Ressourcen für Lagerplätze, Typen, Stapelanlage und Etiketten.
- Konfigurierbare öffentliche Basis-URL für dauerhaft druckbare QR-Codes.
- M0-Projektfundament mit FastAPI, SQLite, Alembic, Jinja2 und zentraler
  Konfiguration.
- Gebrandete Startseite und Health-Check.
- Entwicklungsstarts für Windows und Linux sowie Docker-Grundlage.
- Apache-2.0-Lizenz und getrennte Markenhinweise.

### Fixed

- Der Windows-Entwicklungsstart wählt bei belegtem Standardport verständlich den
  nächsten freien Port, statt mit einem Uvicorn-Bindefehler abzubrechen.
- Der Standardport wurde vom häufig belegten Port 8080 auf Port 8008 geändert.
