# Arbeitsanweisungen für eBauteileFuchs

Diese Datei gilt für das gesamte Repository. Untergeordnete `AGENTS.md` dürfen
für ihren Bereich strengere oder konkretere Regeln ergänzen.

## Projektziel und Sprache

eBauteileFuchs ist eine lokal betriebene Lagerverwaltung für Elektronikbauteile
und private Bastellager. Produkttexte und Projektdokumentation werden auf Deutsch
verfasst. Code, Bezeichner, API-Felder und Commit-Texte werden auf Englisch
gehalten. Der Produktname wird immer exakt als `eBauteileFuchs` geschrieben.

Untertitel: „Clever finden statt lange suchen.“  
Zuordnung: „Ein Open-Source-Projekt von eHaJo.“

## Verbindliche Leitplanken

- Die Anwendung bleibt offline-first und funktioniert ohne Cloud-Dienst. Nur
  ausdrücklich konfigurierte Lieferantenadapter dürfen externe Dienste nutzen.
- Version 1 ist ein modularer Monolith mit Python 3.12, FastAPI, SQLAlchemy,
  Alembic, SQLite, Jinja2 und HTMX.
- Fachlogik gehört in Services beziehungsweise Domain-Module, nicht in
  HTTP-Routen, Templates, ORM-Hooks oder Lieferantenadapter.
- Die HTML-Oberfläche und die interne REST-API verwenden dieselben
  Anwendungsservices und Transaktionsregeln.
- Technische Artikeldaten dürfen niemals erfunden werden. Fehlende Werte bleiben
  leer und importierte Werte müssen vor dem Speichern prüfbar sein.
- Es gibt keine Telemetrie, kein Tracking, keine extern geladenen Schriften und
  keine fest eingebauten Geheimnisse.
- Datenbanken, Sicherungen, `.env`-Dateien und persönliche Lagerdaten gehören
  niemals ins Repository.
- Logo und Markenbestandteile dürfen nicht verändert oder nachgezeichnet werden.
  Ein endgültiges Fuchs-Maskottchen darf ohne Freigabe nicht erzeugt werden.

## Vor jeder Änderung

1. Relevante Dokumente in `docs/` sowie `branding/branding.md` lesen.
2. Bestehende Änderungen respektieren und keine fremden Arbeiten zurücksetzen.
3. Prüfen, ob die gewünschte Funktion in Version 1 liegt. Ausgeschlossene
   Funktionen stehen in `docs/PRODUCT_SPEC.md`.
4. Bei Änderungen an Datenhaltung, Schnittstellen oder Sicherheit die
   zugehörige Dokumentation und gegebenenfalls eine ADR aktualisieren.

## Architektur- und Codekonventionen

- Kleine, klar abgegrenzte Module und explizite Abhängigkeiten bevorzugen.
- Abhängigkeiten zeigen nach innen: `web`/`api` und `infrastructure` verwenden
  `application` und `domain`, nicht umgekehrt.
- ORM-Modelle sind Persistenzdetails. FastAPI-/Pydantic-Schemata werden nicht als
  Domainobjekte wiederverwendet.
- Schreibvorgänge laufen in klaren Transaktionen. Bestandsmengen werden nur über
  den Bestandsservice verändert; jede Änderung erzeugt eine unveränderliche
  Bestandsbewegung.
- Scan- und Buchungsendpunkte benötigen Schutz vor Doppelausführung
  (Idempotenzschlüssel beziehungsweise kurzlebiges Buchungstoken).
- Hersteller und Artikelnummern werden für Vergleiche normalisiert; Originalwerte
  bleiben gespeichert und sichtbar.
- Lieferanten werden über eine interne Schnittstelle angebunden. Lieferantendaten
  gelangen erst nach Mapping und Validierung in die Domain.
- Zeitpunkte werden intern als UTC gespeichert und in der lokalen Zeitzone
  angezeigt. Primärschlüssel sind nicht erratbare UUIDs.
- Neue Datenbankänderungen benötigen eine vorwärts und rückwärts ausführbare
  Alembic-Migration sowie einen Migrationstest.
- HTML aus externen Quellen wird nie ungeprüft ausgegeben. Jinja-Autoescaping
  bleibt aktiv.

## Qualitätssicherung

Vor Abschluss einer Implementierungsänderung, soweit im Projekt vorhanden:

```text
ruff format --check .
ruff check .
pytest
```

Tests sollen mindestens die veränderte Fachlogik, Fehlerfälle und relevante
HTTP-Verträge abdecken. Für Bestandsbuchungen, Dublettenerkennung, Backup und
Restore sind Integrations- beziehungsweise End-to-End-Tests erforderlich. Tests
dürfen keine echte Mouser-API benötigen; Adapterantworten werden durch Fixtures
oder einen lokalen Fake ersetzt.

## Dokumentation und Veröffentlichungen

- Nutzerrelevante Änderungen werden in `CHANGELOG.md` unter „Unreleased“ erfasst.
- Neue Konfigurationswerte werden in `.env.example` und der Betriebsdokumentation
  beschrieben, ohne reale Geheimnisse einzutragen.
- Beispiele verwenden ausschließlich synthetische Daten.
- Releases folgen Semantic Versioning. Vor `1.0.0` dürfen sich interne Verträge
  ändern, müssen aber in Changelog und Migrationshinweisen dokumentiert sein.
- Eine Code-Lizenz wird erst nach ausdrücklicher Bestätigung durch den
  Rechteinhaber hinzugefügt. Marken- und Asset-Rechte werden davon getrennt
  dokumentiert.

## Freigabestatus

Die Planung sowie M0 bis M4 wurden umgesetzt und lokal abgenommen. M5 wurde am
24. August 2026 ausdrücklich freigegeben und umgesetzt; seine lokale Abnahme
steht aus. M6 und alle späteren Meilensteine bleiben bis zu einer weiteren
ausdrücklichen Freigabe gesperrt. Maßgeblich sind `docs/IMPLEMENTATION_PLAN.md`
und `docs/OPEN_DECISIONS.md`.
