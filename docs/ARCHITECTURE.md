# Architektur – eBauteileFuchs

Status: Grundsätzlich freigegeben am 23. August 2026

## 1. Architekturziel

eBauteileFuchs wird als modularer Monolith umgesetzt: ein Python-Paket, ein
Webprozess und standardmäßig eine SQLite-Datenbank. Das hält Installation und
Betrieb auf Raspberry Pi, Linux und Windows klein, ohne Fachlogik mit FastAPI,
Jinja, SQLAlchemy oder Mouser zu verschmelzen.

## 2. Bausteine und Abhängigkeitsrichtung

```text
Browser / USB-Scanner / PWA
          |
          v
Web-Seiten (Jinja + HTMX)      interne REST-API
          \                       /
           v                     v
             Application Services
          /      |        |       \
         v       v        v        v
      Domain   Repositories  Supplier Port  File/QR Ports
                  |              |             |
                  v              v             v
        SQLAlchemy/SQLite      Mouser       CSV/PDF/Backup
```

Die Domain enthält Regeln und Wertobjekte ohne Frameworkimporte. Application
Services koordinieren Anwendungsfälle und Transaktionen. Ports beschreiben
benötigte Fähigkeiten; Infrastrukturadapter implementieren sie. HTML-Routen und
REST-Routen sind zwei dünne Eingänge zu denselben Services.

## 3. Vorgeschlagene Module

- `domain`: Artikelidentität, Normalisierung, Lagerplatzhierarchie,
  Bestandsregeln, Bewegungsarten und fachliche Fehler.
- `application`: Use Cases für Artikel, Dubletten, Ein-/Aus-/Umlagerung,
  Lagerplatzassistent, Suche, Export, Backup und Restore.
- `persistence`: SQLAlchemy-Mappings, Repositoryimplementierungen, Unit of Work
  und Datenbankkonfiguration.
- `suppliers`: portabler Lieferantenvertrag, Mouser-HTTP-Client, Mapper, Cache und
  klar typisierte Fehler.
- `api`: versionierte JSON-Endpunkte und eigene Request-/Response-Schemata.
- `web`: HTML-Routen, Formularschemata und Präsentationslogik.
- `templates` und `static`: serverseitige Ansichten, HTMX-Fragmente, lokales CSS,
  minimales JavaScript, Manifest und Icons.
- `platform`: Netzwerkerkennung, Pfade, Startverhalten und betriebssystemspezifische
  Integrationen.

## 4. Anwendungs- und Datenfluss

### Schreibvorgang Bestand

1. Route validiert Eingabe und Idempotenzschlüssel.
2. Bestandsservice lädt Artikel, Lagerplatz und aktuellen Bestand in einer Unit
   of Work.
3. Domain prüft Aktivstatus, Einheit und ausreichenden Bestand.
4. Service schreibt Bewegungszeile und aktualisiert den materialisierten Saldo in
   derselben Transaktion.
5. Nach Commit wird eine eindeutige Buchungsbestätigung zurückgegeben. Eine
   Wiederholung desselben Schlüssels liefert dasselbe Ergebnis.

Der Saldo beschleunigt Anzeigen; das Bewegungsjournal bleibt die überprüfbare
Quelle. Tests stellen sicher, dass beide übereinstimmen.

### Lieferantensuche

1. Lokale Identitäts- und Lieferantensuche läuft immer zuerst.
2. Nur bei unbekanntem Artikel und Nutzerabsicht wird der Supplier Port aufgerufen.
3. Ein Cache-Schlüssel besteht aus Adapter, Suchmodus, normalisierter Anfrage und
   Adapterversion.
4. Mouser-Rohdaten werden in ein internes Suchergebnis gemappt. Die Domain kennt
   keine Mouser-Antwortstrukturen.
5. Auswahl und Überprüfung geschehen vor Dublettenprüfung und Speicherung.

## 5. REST-API

Die interne API beginnt unter `/api/v1`. Geplante Ressourcen:

- `/articles`, `/articles/{id}` und `/articles/{id}/supplier-links`
- `/locations`, `/locations/{id}` und `/locations/batch`
- `/inventory`, `/inventory/transactions` und `/inventory/transfers`
- `/search`
- `/suppliers/mouser/search`
- `/exports/*`, `/backups` und `/connection`

In M1 umgesetzt sind `/location-types`, `/locations`, `/locations/tree`,
`/locations/batch` sowie QR- und PDF-Unterressourcen. HTML und REST verwenden
denselben `LocationService` und dieselbe SQLAlchemy-Unit-of-Work. QR und PDF sind
über einen eigenen Renderer-Port angebunden und benötigen keinen Netzzugriff.

HTML-spezifische HTMX-Fragmente liegen nicht unter `/api`. OpenAPI dokumentiert
die API, gilt vor Version 1.0 aber als intern. Schreibzugriffe sind im lokalen Netz
ohne Benutzerkonten trotzdem gegen Cross-Site Requests, versehentliche
Doppelbuchung und fremde Origins zu schützen. Eine externe/public API ist nicht
Teil von V1.

## 6. Persistenz und Migrationen

- SQLite ist Standard; die DB-URL bleibt konfigurierbar, ohne in V1 weitere
  Datenbanken zu versprechen.
- SQLAlchemy 2.x mit expliziten Sessions und kurzen Unit-of-Work-Grenzen.
- SQLite: Fremdschlüssel an, WAL, Busy-Timeout; kein Betrieb der DB auf ungeeigneten
  Netzwerkdateisystemen.
- Alembic verwaltet jede Schemaänderung. Beim Start wird nicht stillschweigend ein
  unbekanntes Schema verändert; Installations- und Upgradepfade führen Migrationen
  sichtbar aus.
- UUIDs werden portabel als kanonischer Text gespeichert. Zeitstempel sind UTC.
- Flexible Eigenschaften liegen relational in Definitionen und Werten, nicht als
  immer weiter wachsende Artikeltabelle. Ein begrenztes JSON-Feld ist nur für den
  kurzlebigen Lieferantencache vorgesehen.

## 7. Suche

V1 verwendet eine von der Domain getrennte SQLite-Suchimplementierung. Normalisierte
Suchspalten und ein denormalisierter Suchtext ermöglichen robuste UND-Suche über
kleine bis mittlere private Lager. SQLite FTS5 wird nur eingesetzt, wenn ein
Starttest die Verfügbarkeit bestätigt; andernfalls bleibt eine portable LIKE-
Strategie funktionsfähig. Suchindizes werden nach relevanten Änderungen in
derselben Transaktion aktualisiert.

## 8. Netzwerk, QR und PWA

- Uvicorn bindet konfigurierbar, standardmäßig an `0.0.0.0:8008`.
- Netzwerkerkennung filtert Loopback-, Link-local-, Tunnel- und offensichtlich
  ungeeignete Adressen, erlaubt aber manuelle Übersteuerung.
- Verbindungs-QRs enthalten eine vollständige lokale HTTP(S)-URL. Lagerplatz-QRs
  enthalten einen stabilen, versionsmarkierten Anwendungspfad mit nicht
  semantischer Kennung; umbenannte Lagerplätze bleiben erreichbar.
- QR-Erzeugung und PDF-Layout sind serverseitig und offline.
- Der Service Worker liefert eine App-Shell und statische Assets, aber keine
  offline Bestandsbuchungen. Dadurch entstehen nach Verbindungsabbrüchen keine
  schwer auflösbaren Synchronisationskonflikte.

## 9. Konfiguration und Pfade

Priorität: Umgebungsvariable, lokale `.env`, sichere Standardwerte. Geplant sind
mindestens Bind-Adresse, Port, Datenverzeichnis, bevorzugte Basis-URL,
Mouser-API-Schlüssel, Cache-TTL, Log-Level und Backupverzeichnis. Plattformpfade
werden zentral aufgelöst:

- Linux/Raspberry Pi: Daten standardmäßig unter einem dokumentierten
  Systemdatenpfad beziehungsweise bei Entwicklung unter `./data`.
- Windows: Daten unter einem benutzerspezifischen Anwendungsdatenpfad; Entwicklung
  kann `./data` verwenden.
- Container: gemountetes `/data`-Volume.

Konkrete Produktionspfade werden vor Implementierung in der Betriebsdokumentation
festgelegt.

## 10. Sicherheit

- Jinja-Autoescaping, serverseitige Validierung, sichere URL-Protokolle und keine
  ungeprüften Supplier-HTML-Fragmente.
- CSRF-Schutz für Formularschreibvorgänge, restriktive Origin/Host-Prüfung und
  sichere Cookie-Einstellungen, soweit Cookies verwendet werden.
- API-Schlüssel werden weder ausgegeben noch in Cache, Backup-Metadaten oder Logs
  geschrieben.
- Backup-Uploads erhalten serverseitige Namen, Größenlimit, Format- und
  Integritätsprüfung; Restore verhindert Pfadtraversal.
- QR-Codes gelten als Identifikatoren, nicht als Berechtigungsnachweis.
- Lokaler Netzbetrieb bietet keine Benutzertrennung. Diese bewusste V1-Grenze wird
  deutlich dokumentiert; öffentliche Portfreigaben werden ausdrücklich abgeraten.

## 11. Betrieb und Beobachtbarkeit

Strukturierte lokale Logs mit Zeit, Level, Ereignis und Korrelationskennung;
keine sensiblen Artikel- oder Schlüsselwerte bei Standard-Loglevel. Ein
Health-Endpunkt prüft Prozess und Datenbank. Startausgabe zeigt Branding,
Datenpfad, Schema-Version und erreichbare URLs. Keine Telemetrie verlässt das
Gerät.

## 12. Architekturentscheidungen (ADR-Bedarf)

Vor Implementierung werden mindestens folgende Entscheidungen als kurze ADRs
festgehalten: modularer Monolith, UUID-Strategie, Bewegungsjournal plus Saldo,
Eigenschaftsmodell, QR-Nutzlast, Suchstrategie, Datenpfade und Backupformat.
