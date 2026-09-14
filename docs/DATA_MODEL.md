# Datenmodell – eBauteileFuchs Version 1

Status: Grundsätzlich freigegeben am 23. August 2026

Umsetzungsstand: Die Kapitel 3 bis 7 sowie die Integritätsregeln für Bestand und
Journal sind mit M1 bis M4 realisiert. Die M5-Praxisergänzung benötigt keine neue
Tabelle, ergänzt aber per Revision `0006_unassigned_location` einen internen
Systemlagerplatz für revisionssicher erhaltene Bestände.

## 1. Konventionen

- Primärschlüssel: UUID, als kanonischer Text persistiert.
- Zeitpunkte: UTC mit `created_at` und `updated_at`, wo veränderliche Stammdaten
  vorliegen.
- Löschung: referenzierte Stammdaten werden deaktiviert, nicht hart gelöscht.
- Mengen: Dezimalwerte, niemals Binär-Fließkomma; V1 verhindert negative Salden.
- Original- und Normalwerte werden getrennt gespeichert.
- Fremdschlüssel und fachliche Unique Constraints werden in der Datenbank
  erzwungen, fachliche Fehlermeldungen zusätzlich im Service erzeugt.

## 2. Beziehungen im Überblick

```text
Location 1 --- n Location (parent)
Article  n --- 1 Category
Article  1 --- n SupplierPart n --- 1 Supplier
Article  1 --- n ArticleAttribute n --- 1 AttributeDefinition
Category 1 --- n CategoryAttribute n --- 1 AttributeDefinition
Article  1 --- n InventoryBalance n --- 1 Location
Article  1 --- n InventoryMovement n --- 1 Location
InventoryTransaction 1 --- n InventoryMovement
```

## 3. Lagerplätze

### `location_type`

`id`, `code`, `name`, `sort_order`, `is_system`, `is_active`.

Vorgaben: room, cabinet, shelf, magazine, drawer, compartment, box und crate.
Eigene Typen dürfen ergänzt werden; verwendete Typen bleiben stabil.

### `location`

`id`, `code`, `normalized_code`, `name`, `location_type_id`, `parent_id`
(nullable), `parent_scope`, `description`, `is_active`, `qr_token`, `created_at`,
`updated_at`.

Regeln:

- `(parent_scope, normalized_code)` ist eindeutig. `parent_scope` enthält die
  Eltern-UUID oder für Wurzelknoten den festen Wert `__root__`; ein Check
  verhindert Abweichungen. Damit erzwingt auch SQLite die Geschwistereindeutigkeit
  einschließlich der Wurzelebene.
- Ein Knoten darf weder eigener Vorfahr sein noch unter einen Nachfahren
  verschoben werden.
- `qr_token` ist stabil, zufällig und eindeutig. Anzeige-Code und Name dürfen sich
  ändern, ohne gedruckte Etiketten zu entwerten.
- Das sichere rekursive Löschen archiviert den gewählten Teilbaum durch
  Deaktivierung. Bestände werden in derselben Bestandsjournal-Transaktion auf den
  internen, in der normalen Oberfläche verborgenen Systemlagerplatz
  `OHNE-LAGERPLATZ` oder auf einen gewählten aktiven Lagerplatz übertragen.
  „Bauteil vollständig löschen“ bucht dessen Bestände an allen Lagerplätzen auf
  null und deaktiviert den Artikel. Bewegungen und Transaktionen bleiben
  unverändert erhalten.
- Der Magazin-Assistent erzeugt zuerst einen Knoten vom Typ `magazine` und legt
  die Schubladen darunter an. Er kann unter jeder erzeugten Schublade atomar die
  Unterfächer `A` und `B` anlegen; dafür ist keine zusätzliche Tabellenspalte
  erforderlich, weil dieselbe freie Hierarchie verwendet wird.

## 4. Artikelidentität

### `manufacturer`

`id`, `name`, `normalized_name`, `created_at`, `updated_at`.

Normalisierte Herstellernamen sind indexiert. Ein automatisches Zusammenführen
ähnlicher Hersteller findet nicht statt; Aliasverwaltung ist eine spätere
Erweiterung.

### `category`

`id`, `code`, `name`, `description`, `is_system`, `is_active`, `sort_order`.

Startkategorien: resistor, capacitor, inductor, diode, transistor_mosfet,
integrated_circuit, led, connector, mechanical und other.

### `article`

`id`, `name`, `manufacturer_id` (nullable), `manufacturer_part_number`,
`normalized_manufacturer_part_number`, `category_id`, `description`,
`datasheet_url`, `product_url`, `note`, `search_text`, `is_active`, `created_at`,
`updated_at`.

Regeln:

- Wenn Hersteller und Herstellerartikelnummer vorhanden sind, ist die
  normalisierte Kombination eindeutig. Konflikte führen in den
  Dublettenablauf, nicht zu einem zweiten Artikel.
- Artikel ohne belastbare Herstelleridentität sind erlaubt, benötigen aber eine
  Bezeichnung und werden nur über Supplier-Link beziehungsweise Warnstufe erkannt.
- `search_text` ist ein abgeleiteter Indextext, kein führendes Stammdatum.

### Normalisierung

Hersteller: Unicode normalisieren, trimmen, Groß-/Kleinschreibung vereinheitlichen
und wiederholte Leerzeichen reduzieren. Herstellerartikelnummer: Unicode
normalisieren, trimmen, Großschreibung verwenden und Leerzeichen, Bindestriche
sowie rein trennende Satzzeichen entfernen. Originale bleiben unverändert.
Normalisierungsregeln werden versioniert und durch Regressionstests abgesichert.

### Technische Kompatibilitätsrevision `0007_article_barcodes`

Diese Revision wurde kurzzeitig bereits auf Entwicklungsdatenbanken angewendet
und bleibt deshalb dauerhaft in der Alembic-Kette. Ihre leere Tabelle
`article_barcode` wird von der Anwendung nicht verwendet. Verpackungsbarcodes
werden ausschließlich unmittelbar an die Lieferantensuche übergeben und nicht
als Artikelstammdaten gespeichert.

## 5. Lieferantenzuordnungen

### `supplier`

`id`, `code`, `name`, `adapter_name`, `is_active`. V1 enthält den Systemwert
`mouser`; die Tabelle schafft keine Verpflichtung, weitere Adapter zu liefern.

### `supplier_part`

`id`, `article_id`, `supplier_id`, `supplier_part_number`,
`normalized_supplier_part_number`, `product_url`, `created_at`, `updated_at`.

`(supplier_id, normalized_supplier_part_number)` ist eindeutig. Eine
Lieferantenartikelnummer gehört höchstens zu einem Artikel, ein Artikel aber zu
beliebig vielen Lieferantenzuordnungen.

### `supplier_cache_entry`

`id`, `supplier_id`, `query_type`, `query_normalized`, `adapter_version`,
`response_json`, `status`, `created_at`, `expires_at`.

Cacheeinträge sind austauschbar und keine Stammdaten. Schlüssel, Auth-Header und
unnötige personenbezogene Inhalte werden nicht gespeichert.

Die Tabelle wurde mit M4 als allgemeine Erweiterungsschnittstelle angelegt. Der
Mouser-Adapter schreibt aufgrund der veröffentlichten Mouser-API-Bedingungen
keine Antwortdaten hinein. Sie bleibt für Adapter mit nachweislich erlaubter
Zwischenspeicherung beziehungsweise eine spätere schriftliche Mouser-Freigabe
verfügbar.

## 6. Technische Eigenschaften

### `attribute_definition`

`id`, `code`, `name`, `value_kind` (`text`, `decimal`, `integer`, `boolean`),
`canonical_unit` (nullable), `is_system`, `is_active`.

### `category_attribute`

`category_id`, `attribute_definition_id`, `sort_order`, `is_typical`,
`allowed_units_json` (kleine Konfigurationsliste, keine Artikeldaten).

### `article_attribute`

`id`, `article_id`, `attribute_definition_id` (nullable für freie Eigenschaft),
`custom_name`, `raw_value`, `normalized_text`, `numeric_value` (nullable), `unit`,
`canonical_numeric_value` (nullable), `canonical_unit` (nullable), `sort_order`.

Ein Wert darf immer als `raw_value` erhalten bleiben. Numerische Normalisierung
wird nur vorgenommen, wenn Zahl und Einheit sicher geparst werden. Freie
Eigenschaften benötigen `custom_name`; definierte Eigenschaften nicht.

Typische V1-Definitionen:

| Kategorie | Eigenschaften |
| --- | --- |
| Widerstand | Widerstandswert, Toleranz, Leistung, Bauform, Temperaturkoeffizient |
| Kondensator | Kapazität, Nennspannung, Toleranz, Dielektrikum, Bauform |
| Induktivität | Induktivität, Nennstrom, Gleichstromwiderstand, Bauform |
| Diode | Diodentyp, Sperrspannung, Strom, Gehäuse |
| Transistor/MOSFET | Technologie, Spannung, Strom, Verlustleistung, Gehäuse |
| Integrierter Schaltkreis | Funktion, Gehäuse, Pinzahl, Versorgungsspannung |
| LED | Farbe, Wellenlänge, Spannung, Strom, Bauform |
| Steckverbinder | Serie, Polzahl, Raster, Geschlecht, Montageart |
| Mechanisch | Abmessungen, Material, Gewinde, Ausführung |
| Sonstiges | frei definierte Eigenschaften |

## 7. Bestand und Journal

### `inventory_balance`

`id`, `article_id`, `location_id`, `quantity`, `unit`, `updated_at`, `version`.

`(article_id, location_id, unit)` ist eindeutig. `version` unterstützt
optimistische Konflikterkennung. Zeilen mit Nullbestand dürfen für Historie und
schnelle Wiederverwendung erhalten bleiben.

### `inventory_transaction`

`id`, `transaction_type`, `idempotency_key`, `request_fingerprint`, `comment`,
`created_at`.

Typen: `stock_in`, `stock_out`, `transfer`, `adjustment`, `initial`.
`idempotency_key` ist eindeutig und wird für einen begrenzten, dokumentierten
Zeitraum akzeptiert. Ein Vorgang gruppiert eine oder mehrere Bewegungen.
`request_fingerprint` erkennt eine versehentliche Wiederverwendung desselben
Schlüssels für inhaltlich verschiedene Buchungen. In M3 werden Schlüssel für die
gesamte lokale Journalhistorie eindeutig gehalten; eine automatische Bereinigung
findet nicht statt.

### `inventory_movement`

`id`, `transaction_id`, `article_id`, `location_id`, `quantity_delta`, `unit`,
`balance_after`, `created_at`.

`quantity_delta` trägt ein Vorzeichen; `balance_after` erleichtert Audit und
Fehlersuche. Eine Umlagerung besitzt zwei Bewegungen in derselben Transaktion.
Journalzeilen werden nie editiert oder gelöscht.

## 8. Konfiguration und Betrieb

### `app_setting`

Nur nicht-geheime, über die Oberfläche änderbare Werte: `key`, `value_json`,
`updated_at`. Der Mouser-Schlüssel gehört ausdrücklich nicht in diese Tabelle,
sondern in die Umgebung beziehungsweise `.env`.

### `schema_metadata` / Backupmanifest

Alembic bleibt führend für die Schemaversion. Ein Backupmanifest enthält
Anwendungsversion, Schemaversion, Erstellzeit, Prüfsumme und Formatversion, aber
keine Geheimnisse.

Die Revision `0008_location_grid` ergänzt optionale Rastermetadaten
`location.grid_columns` und `location.grid_rows` (je 1–50, gemeinsam oder beide
leer) für die grafische Lagerübersicht.

M6 verwendet `format=ebauteilefuchs-backup`, `format_version=1` und genau die
ZIP-Mitglieder `manifest.json` und `database.sqlite3`. Das Manifest enthält
`app_version`, `schema_revision`, `created_at`, `database_file`,
`database_size` und `database_sha256`. Unterstützt wird derzeit Revision
`0008_location_grid`; Sicherungen des vorherigen unterstützten Standes werden
beim Restore auf diesen Stand angehoben.

## 9. Integritätsregeln und Nebenläufigkeit

- Fremdschlüssel werden bei jeder SQLite-Verbindung aktiviert.
- Bestand und Bewegung werden atomar aktualisiert; die Prüfung auf negativen
  Bestand erfolgt innerhalb derselben Schreibtransaktion.
- Die erwartete `version` verhindert stilles Überschreiben paralleler Buchungen.
- Unter SQLite beginnt jeder Bestands-Schreibvorgang mit `BEGIN IMMEDIATE`.
  Dadurch kann zwischen Saldenprüfung und Aktualisierung kein zweiter Schreiber
  denselben alten Saldo verwenden; der Versionsvergleich bleibt zusätzliche
  Konflikterkennung.
- Datenbanktrigger verhindern `UPDATE` und `DELETE` auf Journaltransaktionen und
  Bewegungen. Korrekturen sind ausschließlich neue Bewegungen.
- Eindeutigkeitskonflikte werden als fachliche Dubletten beziehungsweise bereits
  gebuchte Idempotenzschlüssel behandelt.
- Eine periodische Diagnose darf Salden aus dem Journal nachrechnen, verändert
  sie aber nicht automatisch.

## 10. Aufbewahrung und Löschung

Stammdaten mit Historie werden deaktiviert. Supplier-Cache darf nach Ablauf
gelöscht werden. Export- und Backupdateien liegen außerhalb der Datenbank und
unterliegen einer dokumentierten, vom Nutzer gesteuerten Aufbewahrung. V1
speichert keine Benutzer- oder Telemetriedaten.
