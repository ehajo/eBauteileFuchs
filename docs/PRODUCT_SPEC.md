# Produktspezifikation – eBauteileFuchs Version 1

Status: Grundsätzlich freigegeben am 23. August 2026  
Produkt: eBauteileFuchs  
Untertitel: „Clever finden statt lange suchen.“  
Absender: „Ein Open-Source-Projekt von eHaJo.“

## 1. Produktversprechen

eBauteileFuchs ist eine schlanke, lokal betriebene Lagerverwaltung für
Elektronikbauteile, Kleinteile und private Bastellager. Sie verkürzt insbesondere
die Wege „Teil erkennen“, „Dubletten vermeiden“, „Bestand buchen“ und „Lagerplatz
wiederfinden“. Die Anwendung läuft auf Raspberry Pi OS, allgemeinen
Linux-Servern und Windows-PCs und wird über einen Browser am PC, Tablet oder
Smartphone bedient.

## 2. Zielgruppen und Hauptaufgaben

Primäre Zielgruppen sind private Maker, Elektronikwerkstätten, Repair-Cafés und
kleine nicht-kommerzielle Labore mit einem lokalen Lager. Die wichtigsten
Aufgaben sind:

1. Ein unbekanntes oder bekanntes Teil scannen und schnell einlagern.
2. Ein Teil anhand Nummer, Eigenschaften oder Lagerplatz wiederfinden.
3. Bestand ohne negative Mengen und ohne versehentliche Doppelbuchung auslagern.
4. Verschachtelte Lagerorte samt QR-Etiketten verwalten.
5. Daten lokal sichern, wiederherstellen und als CSV exportieren.

## 3. Erfolgsprinzipien

- Local-first: Alle Kernfunktionen arbeiten ohne Internetverbindung.
- Scan-first: Tastaturartige USB-Barcodescanner funktionieren ohne Spezialsoftware.
- Mobile-first: große Ziele, sichtbarer Fokus, kurze Wege und keine Hover-Pflicht.
- Nachvollziehbar: Bestandsänderungen sind als Bewegungen dauerhaft sichtbar.
- Fehlertolerant: Ein Ausfall der Mouser-API blockiert die manuelle Anlage nicht.
- Erweiterbar: Oberfläche, Datenbank und externe Lieferanten sind fachlich getrennt.
- Datensparsam: keine Benutzerkonten, Telemetrie oder Cloud-Synchronisation in V1.

## 4. Funktionsumfang Version 1

### 4.1 Navigation

Die Hauptnavigation enthält ausschließlich: Einlagern, Auslagern, Suchen,
Artikel, Lagerplätze und Einstellungen. Start- und Verbindungsseite sind über
Logo beziehungsweise Systemstatus erreichbar, ohne die Navigation aufzublähen.

### 4.2 Lagerplätze

- Frei verschachtelbare Hierarchie mit Kennung, Bezeichnung, Typ, Elternknoten,
  Beschreibung und Aktivstatus.
- Typen sind konfigurierbare Werte mit anfänglichen Vorgaben: Raum, Schrank,
  Regal, Magazin, Schublade, Unterfach, Box und Kiste.
- Geschwisterknoten müssen eine eindeutige Kennung besitzen; der vollständige
  Pfad wird aus der Hierarchie gebildet.
- Ein Magazin-Assistent legt nummerierte Kindlagerplätze in einer Vorschau an,
  beispielsweise Schubladen 01 bis 60, und schreibt sie erst nach Bestätigung.
- Jeder Lagerplatz erhält einen stabilen QR-Code. Einzel- und Sammeldruck werden
  als PDF unterstützt.
- Deaktivierte Lagerplätze bleiben in historischen Bewegungen sichtbar, können
  aber nicht mehr für neue Buchungen gewählt werden.

### 4.3 Artikel und Eigenschaften

- Allgemeine Felder: Bezeichnung, Hersteller, Herstellerartikelnummer,
  Kategorie, Beschreibung, Datenblatt-Link, Produkt-Link und Notiz.
- Ein Artikel kann mehrere Lieferantenartikelnummern und mehrere Lagerplätze mit
  eigenem Bestand besitzen.
- Kategorien besitzen typische Attributdefinitionen; weitere Eigenschaften sind
  pro Artikel ergänzbar. Unterstützte Startkategorien und Pflichtumfang stehen in
  `DATA_MODEL.md`.
- Eigenschaftswerte speichern Originaldarstellung und, soweit möglich, einen
  normalisierten Suchwert. Unbekannte Einheiten oder Formate bleiben erhalten.
- Originalschreibweisen von Hersteller und Herstellerartikelnummer bleiben
  erhalten; zusätzliche normalisierte Felder dienen Suche und Dublettenprüfung.

### 4.4 Lieferanten und Mouser

- Eine allgemeine Adapter-Schnittstelle kapselt Produktsuche und Detailmapping.
- In V1 wird nur die offizielle Mouser Search API implementiert.
- Suchmodi: Mouser-Artikelnummer, Herstellerartikelnummer, Barcode und Freitext.
- Ergebnisse werden mit konfigurierbarer Ablaufzeit lokal zwischengespeichert;
  Geheimnisse und unnötige Rohdaten werden nicht protokolliert.
- Mehrere plausible Treffer erfordern eine explizite Auswahl. Einzeltreffer
  dürfen vorausgewählt, aber nicht ungeprüft gespeichert werden.
- Importierte Felder sind vor dem Speichern bearbeitbar. Fehlende oder zweifelhafte
  technische Angaben werden nicht ergänzt.
- Erwartete Fehlerzustände werden nutzerverständlich unterschieden: fehlender
  oder ungültiger Schlüssel, offline/nicht erreichbar, Rate Limit, kein Treffer,
  unvollständige Daten und mehrere Treffer.

### 4.5 Dublettenerkennung

Die Prüfung erfolgt deterministisch in dieser Reihenfolge:

1. exakte Lieferanten- plus Lieferantenartikelnummer;
2. exakter Hersteller plus exakte Herstellerartikelnummer;
3. normalisierter Hersteller plus normalisierte Herstellerartikelnummer;
4. Ähnlichkeit von Bezeichnung, Kategorie und technischen Eigenschaften als
   nicht-bindende Warnung.

Ein sicherer Treffer öffnet den vorhandenen Artikel und bietet Einlagerung am
vorhandenen oder an einem anderen Lagerplatz an. Eine neue Lieferantenzuordnung
kann nach Bestätigung ergänzt werden. Bei mehreren Kandidaten entscheidet der
Nutzer; ohne Entscheidung wird nichts gespeichert. Die Ähnlichkeitsstufe legt
niemals automatisch Artikel zusammen.

### 4.6 Bestand

- Bestand wird je Kombination aus Artikel und Lagerplatz geführt.
- Erlaubte Bewegungen: Einlagerung, Auslagerung, Umlagerung,
  Bestandskorrektur und initialer Bestand.
- Jede Änderung speichert Menge, Mengeneinheit, Zeitpunkt, Typ, optionalen
  Kommentar und eine gemeinsame Vorgangskennung.
- Umlagerung erzeugt atomar eine negative Quell- und positive Zielbewegung.
- Negative Bestände werden standardmäßig und in V1 ausnahmslos verhindert.
- Eine bestätigte Buchung kann nicht erneut abgesendet werden. Korrekturen
  erfolgen durch Gegen- beziehungsweise Korrekturbuchungen, nicht durch Löschen.

### 4.7 Suche

Eine gemeinsame Suche berücksichtigt Bezeichnung, Hersteller,
Herstellerartikelnummer, Lieferantenartikelnummer, Eigenschaften, Notizen und
Lagerplatzkennung beziehungsweise -pfad. Mehrere Suchwörter werden zunächst als
UND-Verknüpfung behandelt; Teiltreffer und normalisierte Werte unterstützen
Anfragen wie `10k 0805`, `100nF 50V` oder `Magazin 03 Schublade 42`.

### 4.8 Verbindung und PWA

- Der Server lauscht standardmäßig auf `0.0.0.0:8008`.
- Eine Verbindungsseite zeigt Computername, geeignete lokale IPv4-Adressen,
  Port, vollständige URLs, Auswahl einer bevorzugten Adresse und QR-Code.
- Manuelle öffentliche Basis-URL beziehungsweise Hostadresse ist konfigurierbar.
- Der Smartphone-Link öffnet die responsive Anwendung. Ein dauerhaft gedruckter
  QR-Code setzt sinnvollerweise eine feste IP oder DHCP-Reservierung voraus.
- Installierbare PWA mit lokal ausgeliefertem Manifest und Icons. Der Service
  Worker cached nur statische Anwendungsressourcen; fachliche Daten und
  Buchungsantworten werden nicht offline schreibbar gemacht.
- Netzwerkzugriff wird nicht mit öffentlicher Internetfreigabe gleichgesetzt. Die
  Dokumentation erläutert Windows-Firewall und das gleiche lokale Netzwerk.

### 4.9 Export, Backup und Restore

- CSV-Export für Artikel, Lagerplätze und Bestände in UTF-8 mit dokumentiertem
  Schema.
- Konsistente lokale Sicherung der SQLite-Datenbank samt notwendiger Metadaten.
- Restore nur nach Prüfung von Format, Version und Integrität, mit deutlicher
  Bestätigung und automatischer Sicherung des vorherigen Zustands.
- Konfigurierbarer Datenpfad außerhalb des Repositories; kein Geheimnis wird in
  die Sicherung aufgenommen.

## 5. Nichtfunktionale Anforderungen

- Responsive Bedienung ab 360 px Breite; Kernabläufe vollständig per Tastatur.
- WCAG-orientierte Kontraste, sichtbarer Fokus, semantische Beschriftungen und
  Statusmeldungen, die nicht nur über Farbe vermittelt werden.
- SQLite mit aktivierten Fremdschlüsseln, Busy-Timeout und WAL-Modus; kurze
  Schreibtransaktionen für den Betrieb im kleinen lokalen Netz.
- Eingaben werden serverseitig validiert; externe Texte werden escaped und URLs
  auf erlaubte Protokolle beschränkt.
- Geheimnisse ausschließlich über Umgebung beziehungsweise lokale `.env`-Datei.
- Keine externen Fonts, Tracker, Analyse- oder Werbedienste.
- Unterstützte Architekturen: ARM64 und x86-64; native Installation bleibt neben
  Docker möglich.

## 6. Ausdrücklich nicht in Version 1

Mindestbestände, Nachbestelllisten, Projekte, Reservierungen, Bestellungen,
Rechnungen, Preise, Warenbewertung, Benutzerkonten, Rollen, Mandantenfähigkeit,
weitere Lieferantenadapter, automatische Beschaffung, Cloud-Synchronisation,
öffentliche Internetfreigabe und KI-generierte technische Daten.

## 7. Abnahme der ersten praxistauglichen Version

Die Version gilt erst als praxistauglich, wenn die 21 im Projektauftrag genannten
Szenarien nachweisbar getestet sind. `IMPLEMENTATION_PLAN.md` ordnet sie
Meilensteinen und Testarten zu. Zusätzlich müssen Migrationen auf einer leeren
und einer bestehenden Beispieldatenbank, ein Restore auf frischer Installation
sowie alle automatisierten Tests erfolgreich sein.

## 8. Branding

Brandingwerte werden technisch zentral konfiguriert. Verbindlich vorhanden sind
Blau `#0b72b5`, Orange `#e67c23`, das unveränderte eHaJo-Logo, Produktname,
Untertitel, Website und Footer „eBauteileFuchs – ein Open-Source-Projekt von
eHaJo“. Die aus den beiden verbindlichen Farben abgeleitete Palette ist in
`branding/branding.md` dokumentiert und wird als zentrale Design-Tokens geführt.
Bis zu einem freigegebenen Maskottchen wird nur ein neutral beschrifteter
Platzhalter eingeplant; es wird kein Fuchslogo erzeugt.
