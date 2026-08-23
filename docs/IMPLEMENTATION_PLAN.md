# Implementierungsplan – eBauteileFuchs

Status: Grundsätzlich freigegeben am 23. August 2026. M0 und M1 sind umgesetzt
und lokal abgenommen. M2 wurde ausdrücklich freigegeben und am 23. August 2026
umgesetzt; die lokale Abnahme steht aus. M3 und spätere Meilensteine bleiben
gesperrt.

## 1. Vorgehensmodell

Die Entwicklung erfolgt in vertikalen, jeweils lauffähigen Schritten. Jeder
Meilenstein enthält Migrationen, Fachlogik, Oberfläche/API, Tests und
Dokumentation. Eine Funktion gilt erst als fertig, wenn sie unter den relevanten
Zielplattformen oder einer repräsentativen CI-Matrix geprüft ist.

Vor Beginn der Umsetzung müssen die als „Freigabe vor Implementierung“ markierten
Punkte in `OPEN_DECISIONS.md` entschieden und diese Planungsdokumente bestätigt
sein.

## 2. Meilensteine

### M0 – Projektfundament (umgesetzt am 23. August 2026)

- Lizenzentscheidung und getrennte Marken-/Asset-Hinweise dokumentieren.
- `pyproject.toml`, `src`-Layout, Ruff, pytest, Alembic und minimale FastAPI-App.
- Zentrale Konfiguration, Plattform-Datenpfade, `.env.example` und `.gitignore`.
- Grundlayout, zentrale Brand-Tokens und unveränderte Logo-Assets einbinden.
- Lokale Startskripte für Entwicklung auf Linux und Windows.
- CI-Grundmatrix für Python 3.12 unter Linux und Windows.

Abnahme: App startet ohne Cloudzugriff, Test/Lint laufen, Daten und Geheimnisse
werden nicht versioniert, Startseite zeigt korrektes Branding.

### M1 – Lagerplätze und QR (umgesetzt und abgenommen am 23. August 2026)

- Lagerplatztypen, Baumregeln, CRUD und Deaktivierung.
- Magazin-Assistent mit atomarer Vorschau/Erzeugung für 60 Schubladen.
- Stabile QR-Tokens, Einzel- und Sammel-PDF nach festgelegtem Etikettenformat.
- Responsive Baum-/Pfadnavigation und REST-Ressourcen.

Umsetzungsstand: vollständig implementiert einschließlich Alembic-Revision
`0002_m1_locations`, HTML-Oberfläche, `/api/v1`-Ressourcen, QR-Auflösung,
PDF-Renderer und automatisierter Zyklus-, Konflikt-, Migrations- und Rendertests.

Abnahmekriterien: Projektauftrag 7 und 8; zusätzlich Zyklus-, Konflikt- und
PDF-Render-Tests.

### M2 – Artikel, Kategorien und Dubletten (umgesetzt am 23. August 2026, Abnahme ausstehend)

- Hersteller, Kategorien, typische/freie Eigenschaften und Lieferantenzuordnungen.
- Manuelle Artikelanlage und -bearbeitung.
- Versionierte Normalisierung und Dublettenstufen 1 bis 4.
- Suchindexgrundlage und synthetische Demo-/Testdaten.

Umsetzungsstand: Hersteller, Start- und eigene Kategorien, relationale typische
und freie Eigenschaften, Lieferantenzuordnungen, versionierbare deterministische
Normalisierung, vierstufige Dublettenprüfung, manuelle HTML-/REST-Verwaltung und
portable lokale UND-Suche sind implementiert. Die Alembic-Revision
`0003_m2_articles` aktualisiert vorhandene M1-Datenbanken ohne Datenverlust.

Abnahmekriterien: 9, 13, 14 und fachliche Regressionstests für Schreibweisen,
Trennzeichen und mehrdeutige Kandidaten.

### M3 – Bestandsjournal und Scanabläufe

- Saldo, unveränderliche Bewegungen, Transaktionen und Idempotenz.
- Einlagern, Auslagern und Umlagern über HTML/HTMX und `/api/v1`.
- USB-Scanner-Fokusführung, Schnellmengen und Nebenläufigkeitsmeldungen.
- Kein negativer Bestand; Korrektur nur als neue Bewegung.

Abnahmekriterien: 15 und 16; zusätzlich Doppelabsendung, parallele Entnahme,
Transfer-Rollback und Journal-Saldo-Abgleich.

### M4 – Mouser-Integration

- Supplier Port, offizieller Mouser-Adapter, Timeout/Retry-Grenzen und Cache.
- Suchmodi, kein/ein/mehrere Treffer und bearbeitbare Importprüfung.
- Fehlerbilder für Schlüssel, Netzwerk, API, Rate Limit und unvollständige Daten.
- Durchgängige Dublettenprüfung vor Speicherung; manueller Fallback.

Abnahmekriterien: 10 bis 12 und 14. Automatisierte Tests verwenden ausschließlich
Fixtures/Fakes; ein optionaler, expliziter Integrationstest prüft einen eigenen
Mouser-Schlüssel und läuft nicht in Standard-CI.

### M5 – Suche, Verbindung und PWA

- Globale UND-Suche über Stammdaten, Supplier-Nummern, Eigenschaften, Notizen und
  Lagerpfade; portable Fallbackstrategie für SQLite.
- Netzwerkerkennung, Auswahl/manuelle Basis-URL und Verbindungs-QR.
- Responsive PWA-App-Shell ohne Offline-Schreibsynchronisation.
- Windows-Firewall- und DHCP-Hinweise.

Abnahmekriterien: 4 bis 6 und 17; reale Smartphone-Prüfung im lokalen Netz.

### M6 – Export, Backup und Restore

- Dokumentierte UTF-8-CSV-Schemata und Exporte.
- Konsistentes versioniertes Backup mit Manifest, Prüfsumme und sicherer Ablage.
- Validierter Restore mit automatischer Vorsicherung und Integritätsprüfung.
- Datenpfad- und Betriebsdokumentation.

Abnahmekriterien: 18 bis 20; Restore wird auf einer frischen Installation sowie
über eine unterstützte Schemaversion getestet.

### M7 – Installation und Veröffentlichungsreife

- Native Raspberry-Pi-/Linux-Installation, systemd-Unit und Updatepfad.
- Multi-Arch-Dockerfile/Compose für ARM64 und x86-64 mit persistentem Volume.
- Windows-Startskript mit Browseröffnung; Vorbereitung eines entpackbaren
  Programmpakets ohne V1-Zwang zu einem Installer.
- README, Plattformanleitungen, CONTRIBUTING, SECURITY und CHANGELOG vervollständigen.
- GitHub Actions, Releasecheckliste, semantische Versionierung, Screenshots und
  Demo-Modus mit synthetischen Daten.
- Manuelle Abnahmematrix auf ARM64-Linux, x86-64-Linux und Windows.

Abnahmekriterien: 1 bis 3 und 21 sowie vollständige Wiederholung der Kriterien
4 bis 20 auf den jeweils relevanten Plattformen.

## 3. Teststrategie

- Unit-Tests: Normalisierung, Mengenregeln, Hierarchie, Mapping und Suchtoken.
- Repository-/Migrationstests: echte temporäre SQLite-Datenbanken, leeres Schema,
  Upgrade und Downgrade mindestens einer Revision.
- API-Tests: Statuscodes, Schemata, Validierung, CSRF/Origin und Idempotenz.
- UI-Integration: HTMX-Fragmente, Fokus-/Scanpfade und Fehlerzustände.
- End-to-End: die 21 Abnahmeszenarien, soweit automatisierbar; echte Geräte und
  Druck/PDF zusätzlich manuell.
- Snapshot/Render-Prüfung: QR-Etiketten und wesentliche responsive Ansichten.
- Supplier-Vertragstests: gespeicherte Mouser-Fixtures für alle Fehlerklassen.

CI-Mindestmatrix: Python 3.12 auf aktuellem Ubuntu und Windows. ARM64-Builds
werden spätestens M7 automatisiert; ein echter Raspberry Pi bleibt Teil der
Releaseabnahme.

## 4. Release- und Migrationsstrategie

- Semantic Versioning; frühe Entwicklung als `0.x`, erste praxistaugliche
  Veröffentlichung nach vollständiger Abnahme.
- Changelog nach „Keep a Changelog“-Struktur mit Upgradehinweisen.
- Jede Version enthält unterstützte Schemaversionen und geprüfte Plattformen.
- Vor Upgrade wird ein Backup empfohlen beziehungsweise im Paketprozess
  automatisiert angeboten. Anwendung und Datenformat werden nicht stillschweigend
  zurückgestuft.
- Offizielle eHaJo-Releases werden über dokumentierte Quelle, Signatur/Checksumme
  und Releasehinweis von inoffiziellen Builds unterscheidbar gemacht.

## 5. Dokumentationslieferumfang

Geplant sind README, Raspberry-Pi-, Linux-, Docker- und Windows-Anleitung,
Backup/Restore-Handbuch, Konfigurationsreferenz, Nutzerkurzanleitung,
CONTRIBUTING, SECURITY, CHANGELOG, Architektur-ADRs, API-Dokumentation und
Releasecheckliste. Screenshots und Demodaten dürfen keine echten persönlichen
Lagerdaten enthalten.

## 6. Risiken und Gegenmaßnahmen

| Risiko | Gegenmaßnahme |
| --- | --- |
| Gleichzeitige SQLite-Schreibzugriffe | kurze Transaktionen, WAL, Busy-Timeout, Konfliktmeldung, Lasttest |
| Schwankende Mouser-Daten | isolierter Mapper, Fixtures, defensive Felder, manueller Fallback |
| Falsch-positive Dubletten | deterministische Stufen; Ähnlichkeit nur als Warnung |
| Doppelbuchung durch Scanner/Netz | Idempotenzschlüssel, gesperrte UI, eindeutige Transaktion |
| Veraltete gedruckte Verbindungs-QRs | Hinweis auf DHCP-Reservierung, manuelle Basis-URL |
| Beschädigter Restore | Format/Checksumme/Schema prüfen, Vorsicherung, atomarer Tausch |
| Uneinheitliche Plattformpfade | zentraler Pfadresolver und Plattformtests |
| Unfreigegebene Markenverwendung | getrennte Rechtehinweise; keine Assetänderung ohne Freigabe |

## 7. Definition of Done

Eine Änderung ist fertig, wenn Fachregeln, HTML/API-Verträge, Migrationen,
Fehlerfälle, Sicherheitsauswirkungen, automatisierte Tests und Nutzerdokumentation
zusammen passen; Ruff und pytest erfolgreich sind; keine Geheimnisse oder echten
Lagerdaten enthalten sind; und die betroffene Abnahme auf mindestens einer
repräsentativen Zielplattform ausgeführt wurde.
