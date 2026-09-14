# CSV-Export, Sicherung und Wiederherstellung

## CSV-Exporte

Unter **Daten** stellt eBauteileFuchs vier dokumentierte CSV-Dateien bereit. Sie
verwenden UTF-8 mit BOM, Komma als Trennzeichen, CRLF-Zeilenenden und eine feste
Kopfzeile. Text, der in Tabellenprogrammen als Formel ausgeführt werden könnte,
wird mit einem Apostroph geschützt. Leere Datenbankwerte bleiben leere Felder.

| Datei | Inhalt und Spalten |
| --- | --- |
| `artikel.csv` | `article_id`, `bezeichnung`, `hersteller`, `hersteller_artikelnummer`, `kategorie`, `beschreibung`, `datenblatt_url`, `produkt_url`, `notiz`, `lieferanten_artikelnummern`, `aktiv`, `erstellt_utc`, `geaendert_utc` |
| `artikel-eigenschaften.csv` | `article_id`, `bezeichnung`, `eigenschaft_code`, `eigenschaft`, `originalwert`, `numerischer_wert`, `einheit`, `kanonischer_wert`, `kanonische_einheit`, `sortierung` |
| `lagerplaetze.csv` | `lagerplatz_id`, `uebergeordneter_lagerplatz_id`, `code`, `name`, `typ`, `vollstaendiger_pfad`, `beschreibung`, `aktiv`, `erstellt_utc`, `geaendert_utc` |
| `bestaende.csv` | `artikel_id`, `bezeichnung`, `hersteller_artikelnummer`, `lagerplatz_id`, `lagerpfad`, `menge`, `einheit`, `geaendert_utc` |

CSV ist für Auswertung und Weiterverarbeitung bestimmt, nicht für eine
verlustfreie Wiederherstellung. Dafür dient ausschließlich die ZIP-Sicherung.

## Sicherungsformat Version 1

Eine Sicherung enthält genau `manifest.json` und `database.sqlite3`. Das Manifest
nennt Format- und Anwendungsversion, Alembic-Schemaversion, UTC-Erstellzeit,
Byte-Größe und SHA-256. Die Datenbank ist eine konsistente SQLite-Momentaufnahme.
Das aktuelle Format heißt `ebauteilefuchs-backup`, hat Version `1` und unterstützt
den Datenbankstand `0008_location_grid`. Sicherungen vom vorherigen Stand
`0007_article_barcodes` werden beim Restore automatisch auf das aktuelle Format
angehoben.

API-Schlüssel, `.env`, Zertifikate und private Schlüssel werden nicht aufgenommen.
Sicherungen sind nicht verschlüsselt; für vertrauliche Daten ist ein
verschlüsseltes Zielmedium zu verwenden. Standardablage ist `backups` unterhalb
des Datenordners. Regelmäßig eine zweite Kopie auf einem anderen Datenträger
ablegen.

## Wiederherstellung

1. Unter **Daten** eine ZIP-Sicherung auswählen und **Datei prüfen** wählen.
2. eBauteileFuchs prüft ZIP-Struktur, Größenlimit, Manifest, Format und Schema,
   SHA-256, SQLite-Integrität und Fremdschlüssel.
3. Metadaten kontrollieren und exakt `WIEDERHERSTELLEN` eingeben.
4. Direkt vor dem Austausch entsteht eine vollständige
   `ebauteilefuchs-vorsicherung-…zip` des aktuellen Stands.
5. Die geprüfte Datenbank wird atomar ausgetauscht; bei einem Austauschfehler
   wird die bisherige Datei zurückgelegt.
6. Anwendung neu starten und Health-Check, Artikel, Lagerplätze und Bestand prüfen.

Uploads erhalten serverseitige Zufallsnamen und werden nach dem Vorgang entfernt.
Fremde ZIP-Pfade werden nicht extrahiert. Der Standardgrenzwert von 512 MB kann
mit `EBAUTEILEFUCHS_RESTORE_UPLOAD_LIMIT_MB` angepasst werden.

## Frische Installation

Die neue Installation zuerst bis zum aktuellen Alembic-Stand starten, dann die
Wiederherstellung über **Daten** ausführen. ZIP-Inhalte nicht manuell in den
Datenordner kopieren. Die Vorsicherung aufbewahren, bis alle Daten geprüft sind.
