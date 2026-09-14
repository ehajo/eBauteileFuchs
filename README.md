# eBauteileFuchs

**Clever finden statt lange suchen.**

eBauteileFuchs ist eine lokal betriebene Open-Source-Lagerverwaltung
für Elektronikbauteile, Kleinteile und private Bastellager.

> Ein Open-Source-Projekt von eHaJo – <https://www.ehajo.de>

## Projektstatus

M0 bis M5 sind lokal abgenommen. M6 ergänzt dokumentierte CSV-Exporte,
versionierte ZIP-Sicherungen und eine validierte Wiederherstellung mit
automatischer Vorsicherung sowie einen optionalen Docker-Betrieb. Die lokale
M6-Abnahme steht aus.

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

Docker ist eine zusätzliche Betriebsform; der native Windows-Start bleibt
vollständig unterstützt. Für Docker Desktop, Raspberry Pi und Linux zuerst die
Beispielkonfiguration kopieren und die LAN-Adresse eintragen:

```bash
cp .env.example .env
# In .env mindestens EBAUTEILEFUCHS_PUBLIC_BASE_URL auf die LAN-Adresse setzen.
docker compose up -d --build
```

Die SQLite-Datenbank, Sicherungen und die Laufzeitablage liegen ausschließlich
im benannten Volume `ebauteilefuchs-data` unter `/data`. `docker compose down`
stoppt die Anwendung ohne Datenverlust. **`docker compose down -v` löscht dieses
Volume und damit die produktiven Daten unwiderruflich.**

Weitere Befehle, der isolierte Testcontainer und die Einrichtungsanleitungen
stehen unter [Docker](docs/installation/docker.md),
[Raspberry Pi](docs/installation/raspberry-pi.md) und
[Linux](docs/installation/linux.md).

## Browser und Systemstatus

Nach dem Start:

- Startseite: <http://127.0.0.1:8008>
- Artikel: <http://127.0.0.1:8008/articles>
- Lagerplätze: <http://127.0.0.1:8008/locations>
- Bestand: <http://127.0.0.1:8008/inventory>
- Bestand direkt ändern: <http://127.0.0.1:8008/inventory/book>
- Globale Suche: <http://127.0.0.1:8008/search>
- Mouser-Suche: <http://127.0.0.1:8008/suppliers/mouser>
- Smartphone verbinden: <http://127.0.0.1:8008/connection>
- Daten exportieren/sichern: <http://127.0.0.1:8008/data>
- Health-Check: <http://127.0.0.1:8008/api/v1/health>
- OpenAPI: <http://127.0.0.1:8008/docs>

Der Server bindet standardmäßig an `0.0.0.0:8008`. Die Verbindungsseite erkennt
geeignete lokale IPv4-Adressen, erlaubt eine manuelle Basis-URL und erzeugt den
zugehörigen Smartphone-QR-Code. Öffentliche Portfreigaben sind nicht vorgesehen.

## Smartphone-Kamera und Barcodes

Auf der Startseite und unter **Suchen → Mouser** öffnet
**Verpackungsbarcode scannen** den Scan-Dialog. **Foto aufnehmen** funktioniert
auf Smartphones auch beim normalen HTTP-Aufruf im privaten LAN. Das Bild wird
direkt auf dem Smartphone durch den lokal mitgelieferten Decoder ausgewertet,
weder hochgeladen noch gespeichert und anschließend verworfen. Werden mehrere
Codes auf einer Verpackung erkannt, muss die passende Nummer gewählt werden.
Würth-Kennungen werden dabei fachlich ausgewertet: `1P` bezeichnet den für die
Suche verwendeten Produktcode, `1T` die Lotnummer und `Q` die Packungsmenge.
Lotnummer und Menge werden angezeigt, aber niemals als Artikelnummer gesucht.

Der erkannte Inhalt wird als Barcode-Suche verarbeitet: eBauteileFuchs prüft
zunächst bereits gespeicherte Artikel- und Lieferantennummern und fragt nur ohne
lokalen Treffer die konfigurierte Mouser Search API ab. Treffer werden weiterhin
vor dem Import angezeigt und geprüft; der Scan speichert oder bucht nichts
automatisch.

Nur der komfortable Live-Scan mit laufendem Kamerabild benötigt im lokalen
Netzwerk eine als sicher erkannte HTTPS-Verbindung. HTTPS ist für den Foto-Scan
also nicht erforderlich. Optional ein lokal vertrauenswürdiges Zertifikat und
den zugehörigen privaten Schlüssel außerhalb des Repositorys ablegen und in
`.env` konfigurieren:

```text
EBAUTEILEFUCHS_SSL_CERTFILE=C:/lokal/ebauteilefuchs-cert.pem
EBAUTEILEFUCHS_SSL_KEYFILE=C:/lokal/ebauteilefuchs-key.pem
EBAUTEILEFUCHS_PUBLIC_BASE_URL=https://192.168.1.42:8008
```

Die ausstellende lokale Zertifizierungsstelle muss auf dem Smartphone als
vertrauenswürdig eingerichtet sein und das Zertifikat muss zur verwendeten
IP-Adresse beziehungsweise zum lokalen Hostnamen passen. Ohne HTTPS bietet die
Oberfläche automatisch den Foto-Scan sowie Texteingabe und Bluetooth-/USB-
Scanner an. Kamera- und Fotodaten verlassen das Gerät nicht und werden nicht
gespeichert.

## Manuelle Entwicklungsbefehle

Nach Aktivierung einer Python-3.12-Umgebung:

```text
python -m pip install -r requirements.lock -r requirements-dev.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m alembic upgrade head
python -m ebauteilefuchs
```

`requirements.lock` und `requirements-dev.lock` halten die für M6 geprüften
Abhängigkeiten reproduzierbar fest.

## Mouser-Suche und Import

Ohne API-Schlüssel startet und funktioniert eBauteileFuchs weiterhin vollständig
offline. Für die freiwillige Mouser-Suche einen eigenen Schlüssel beantragen und
ausschließlich in der nicht versionierten `.env` eintragen:

```text
EBAUTEILEFUCHS_MOUSER_API_KEY=dein-lokaler-schlüssel
```

Die Suche prüft zuerst lokale Lieferanten- und Herstellerartikelnummern. Erst
wenn kein lokaler Treffer vorliegt oder „Trotzdem bei Mouser suchen“ gewählt
wird, erfolgt ein externer Aufruf. Ergebnisse werden niemals automatisch
gespeichert. Auswahl, normalisierte Eigenschaften, Kategorie und Links müssen auf
der Prüfseite bestätigt werden. Bei einem vorhandenen Artikel kann ausschließlich
die Mouser-Nummer ergänzt werden; lokale Stammdaten und Bestände bleiben dabei
unverändert.

Die veröffentlichten Mouser-API-Bedingungen untersagen das Cachen von
Mouser-Inhalten. Deshalb ist der technisch allgemeine Supplier-Cache für Mouser
deaktiviert. Details, Schlüsselbeantragung und Tests beschreibt die
[Mouser-Anleitung](docs/MOUSER.md).

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

Die globale Suche steht direkt auf der Startseite und unter **Suchen**. Sie
verknüpft mehrere Suchwörter mit UND und
berücksichtigt Namen, Hersteller, Artikelnummern, Eigenschaften, Notizen,
Lieferantennummern und aktuelle Lagerpfade. Kategorie, aktueller Bestand und
grobe Lagerbereiche können zusätzlich gefiltert werden, ohne jede einzelne
Schublade in der Filterliste anzuzeigen.

Ein- und Auslagern sind unter **Bestand ändern** zusammengeführt. Bei einem
vorausgewählten Artikel entfallen die erneute Artikelsuche und der obere
Lagerfilter. Die Schaltflächen `−5`, `−1`, `+1` und `+5` buchen unmittelbar;
andere Mengen werden über **Entnehmen** beziehungsweise **Hinzufügen** gebucht.

## PWA und Smartphone-Verbindung

Die Anwendung liefert Manifest, App-Shell und Service Worker lokal aus und kann
in unterstützten Browsern zum Startbildschirm hinzugefügt werden. Statische
Ressourcen und eine Offline-Hinweisseite sind verfügbar; Artikel-, Bestands- und
Buchungsdaten werden ausdrücklich nicht offline gespeichert. Ohne bestätigten
Health-Check sperrt die Oberfläche Schreibaktionen.

Service Worker setzen einen sicheren Browserkontext voraus: `localhost` wird am
PC als sicher behandelt, bei einer Smartphone-Adresse im LAN ist für die volle
PWA-Installation normalerweise vertrauenswürdiges HTTPS nötig. Die normale
responsive Browserbedienung bleibt über privates HTTP-LAN möglich.

Unter **Verbindung · M5** stehen Computername, erkannte Adressen, manuelle
Basis-URL, QR-Code sowie Hinweise zu privater Windows-Firewall, gleichem WLAN und
DHCP-Reservierung bereit. Details enthält die
[M5-Testanleitung](docs/MANUAL_TEST_M5.md).

## Export, Sicherung und Wiederherstellung

Unter **Daten** stehen UTF-8-CSV-Dateien für Artikel, Eigenschaften,
Lagerplätze und Bestände bereit. Eine vollständige Sicherung erzeugt eine
versionierte ZIP-Datei mit konsistenter SQLite-Kopie, Manifest und
SHA-256-Prüfsumme. Vor einer validierten Wiederherstellung wird automatisch eine
Vorsicherung angelegt. Format und Notfallablauf beschreibt
[Sicherung und Wiederherstellung](docs/BACKUP_RESTORE.md); für die lokale Abnahme
gilt die [M6-Testanleitung](docs/MANUAL_TEST_M6.md).

## Lagerplätze und Etiketten

Unter **Lagerplätze** können Räume, Schränke, Regale, Magazine, Schubladen,
Unterfächer, Boxen und Kisten hierarchisch angelegt werden. Eigene Typen lassen
sich unter **Typen** ergänzen. Der Magazin-Assistent erzeugt standardmäßig 60
Schubladen (`01` bis `60`) erst nach einer konfliktfreien Vorschau atomar. Dabei
wird zuerst ein eigenständiges Magazin angelegt und die Schubladen werden darin
einsortiert. Bereits vorhandene Schubladen derselben Ebene lassen sich in der
Baumansicht auswählen und nachträglich unter einem neuen Magazin gruppieren.

Die grafische Übersicht bildet Räume und größere Lagerbereiche als Gruppen und
Magazine beziehungsweise Schubladen als kompaktes Fachraster ab. Eine lokale
Hervorhebungssuche zeigt schnell den passenden Pfad; jedes Fach führt direkt zur
Detailseite. Für Pflege, Sammelauswahl und Löschen kann zur kompakten
Verwaltungsansicht gewechselt werden. Dort lassen sich alle Unterplätze eines
Zweigs mit einer Aktion markieren.

Für einen Bereich mit festem Aufbau können im Formular **Spalten** und **Reihen**
(je 1–50) hinterlegt werden. Die grafische Karte übernimmt diese Angaben direkt;
beide Felder müssen gemeinsam ausgefüllt werden. Bestehende Lagerplätze ohne
Rasterangabe bleiben automatisch angeordnet.

Die Detailseite bietet ein universelles Einzeletikett. In der Baumansicht können
mehrere Lagerplätze für einen A4-Sammelbogen ausgewählt werden. Das Standardraster
ist 70 × 36 mm mit 24 Etiketten pro A4-Seite (3 × 8). Für dauerhaft gedruckte
Smartphone-QR-Codes sollte `EBAUTEILEFUCHS_PUBLIC_BASE_URL` auf eine im lokalen
Netz stabile Adresse gesetzt oder über die Verbindungsseite geprüft werden.

Für kleine 60er-Magazine steht auf der Lagerplatzdetailseite zusätzlich ein
35 × 13-mm-Kompaktetikett bereit. Im Magazin-Assistenten können Schubladen
optional automatisch mit den Unterfächern A und B angelegt werden.

In der Baumansicht können ein oder mehrere Lagerplätze einschließlich aller
Unterplätze sicher gelöscht werden. Vorher zeigt eBauteileFuchs alle betroffenen
Bauteile. Je Bauteil kann der Bestand ohne Lagerplatz erhalten, einem anderen
Lagerplatz zugewiesen oder vollständig ausgebucht und das Bauteil deaktiviert
werden. Lagerplätze und Buchungshistorie werden revisionssicher archiviert; in
der normalen Übersicht sind sie anschließend nicht mehr sichtbar.

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
- [Mouser-Einrichtung und manuelle M4-Abnahme](docs/MOUSER.md)
- [Manuelle M5-Abnahme](docs/MANUAL_TEST_M5.md)
- [CSV, Sicherung und Wiederherstellung](docs/BACKUP_RESTORE.md)
- [Manuelle M6-Abnahme](docs/MANUAL_TEST_M6.md)
- [Docker-Betrieb](docs/installation/docker.md)
- [Raspberry Pi](docs/installation/raspberry-pi.md)
- [Linux](docs/installation/linux.md)
- [Windows](docs/installation/windows.md)

Version 1 ist als responsive lokale Webanwendung für Raspberry Pi, Linux und
Windows vorgesehen. Kerntechnologien sind Python 3.12, FastAPI, SQLAlchemy,
SQLite, Alembic und Jinja2; HTMX wird mit den interaktiven Abläufen ergänzt.

## Lizenz und Marken

Der Programmcode steht unter der [Apache License 2.0](LICENSE). Diese Lizenz
gewährt keine Rechte an eHaJo, eBauteileFuchs, Logo, einem späteren
Fuchs-Maskottchen oder anderen Brandingbestandteilen. Es gelten die Hinweise in
[TRADEMARKS.md](TRADEMARKS.md). Das vorhandene eHaJo-Logo darf nicht verändert
oder nachgezeichnet werden.

Hinweise und Lizenztexte der lokal mitgelieferten Barcode-Komponente stehen in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
