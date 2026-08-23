# Offene Entscheidungen

Status: Standardwerte am 23. August 2026 grundsätzlich übernommen. Verbleibende
meilensteinspezifische Detailprüfungen sind ausdrücklich markiert.

## A. Freigabe vor Implementierungsbeginn erforderlich

### A1. Open-Source-Lizenz

**Entschieden:** Apache License 2.0 für den Programmcode. Marken und
Brandingbestandteile sind ausgenommen und werden in `TRADEMARKS.md` getrennt
behandelt.

**Vorschlag:** Apache License 2.0 für den Quellcode. Sie ist permissiv, enthält
eine ausdrückliche Patentlizenz und eignet sich für breite Nutzung auf Raspberry
Pi, Linux und Windows. `eHaJo`, `eBauteileFuchs`, Logo, späteres Maskottchen und
weitere Markenassets werden davon ausgenommen und separat in `TRADEMARKS.md`
beziehungsweise der Asset-Dokumentation geregelt.

**Alternativen:** MIT für maximale Einfachheit; GPL-3.0-only für Copyleft bei
verteilten Ableitungen; AGPL-3.0-only, falls auch geänderte, über ein Netzwerk
bereitgestellte Versionen ihren Quellcode anbieten sollen.

Die vollständige Lizenz liegt als `LICENSE` vor. Als Projektabsender wird eHaJo
geführt.

### A2. Verbindliche Branding-Palette

**Entschieden:** Die beiden eHaJo-Farben bleiben unverändert. Alle weiteren
Designfarben werden harmonisch und kontrastreich daraus abgeleitet und zentral
verwaltet. Die freigegebene M0-Palette steht in `branding/branding.md`.

`branding/branding.md` definiert Blau `#0b72b5` und Orange `#e67c23`, lässt aber
Akzentfarbe sowie dunklen und hellen Hintergrund offen.

Konkrete Werte werden ausschließlich über zentrale Design-Tokens verwendet.

### A3. Rechtehinweise und offizielle Version

**Entschieden:** eHaJo und eBauteileFuchs sind Kennzeichen des Projektinhabers.
Forks dürfen nicht als offizielle eHaJo-Version erscheinen; unveränderte
Weitergaben dürfen bestehende Herkunftshinweise behalten. Die sachliche Regelung
steht in `TRADEMARKS.md`.

Die konkrete Release-Signatur beziehungsweise Checksumme wird planmäßig in M7
technisch umgesetzt.

## B. Vor dem jeweiligen Meilenstein zu bestätigen

Die nachfolgenden empfohlenen V1-Standards sind grundsätzlich übernommen. Wo ein
reales Medium, ein externer Vertrag oder ein Plattformtest nötig ist, bleibt nur
diese konkrete Prüfung vor dem genannten Meilenstein offen.

### B1. Lagerplatz-QR-Nutzlast (vor M1)

**Übernommen:** vollständige URL im QR plus lesbarer Kurzcode auf dem Etikett.

**Vorschlag:** ein relativer, versionierter Pfad mit zufälligem stabilem Token,
zum Beispiel `/q/l/v1/<token>`. Beim Erzeugen eines PDFs kann optional die
konfigurierte Basis-URL vorangestellt werden. Damit bleiben Umbenennungen gültig;
bei Serveradressänderung können relative Nutzlasten in spezialisierten Scannern
weiterverwendet werden, normale Smartphone-QRs benötigen jedoch eine vollständige
URL.

**Entscheidung:** Sollen Lagerplatzetiketten immer eine vollständige URL oder
zusätzlich einen portablen Kurzcode tragen? Der Vorschlag ist: vollständige URL im
QR plus lesbarer Kurzcode auf dem Etikett.

### B2. Etikettenformate (vor M1)

**Teilweise abgeschlossen:** frei konfigurierbarer A4-Bogen und universelles
Einzeletikett sind gesetzt. Ein konkretes Standardraster muss vor M1 anhand der
tatsächlich verwendeten Etiketten benannt werden.

**Vorschlag für V1:** A4-Bogen frei konfigurierbar über Ränder, Spalten, Zeilen
und Etikettengröße sowie ein universelles Einzeletikett. Ein konkretes häufig
verwendetes Standardraster sollte eHaJo benennen, damit reale Drucktests nicht an
der Hardware vorbeigehen.

### B3. Mengeneinheiten (vor M3)

**Übernommen:** Standard `Stück`, Dezimalmengen, keine Einheitenumrechnung in V1.

**Vorschlag:** pro Artikel/Lagerplatz genau eine frei benannte Einheit, Standard
`Stück`; Mengen als Dezimalzahl. Umrechnungen zwischen Rollen, Metern, Packungen
und Stück sind nicht Teil von V1. Ein Einheitenwechsel bei bestehender Historie
erfordert eine Korrekturbuchung beziehungsweise neuen Bestandsschlüssel.

### B4. Mouser-Cache-Aufbewahrung (vor M4)

**Übernommen unter Vorbehalt der Vertragsprüfung:** 24 Stunden für Treffer,
15 Minuten für „kein Treffer“, keine Fehlerzwischenspeicherung.

**Vorschlag:** erfolgreiche Suchergebnisse 24 Stunden, „kein Treffer“ 15 Minuten,
Fehler nicht cachen; manuelles Leeren in Einstellungen. Rohantworten nur soweit
für Mapping und Diagnose nötig speichern. Vor Umsetzung sind die aktuellen
Mouser-API-Nutzungsbedingungen auf erlaubte Cache-Dauer zu prüfen.

### B5. Suchähnlichkeit (vor M2/M5)

**Übernommen:** konservative transparente Warnung, nie automatische Vereinigung.

**Vorschlag:** Stufe 4 ist eine transparente, konservative Warnung aus
normalisierten Tokens und übereinstimmenden Kerneigenschaften, ohne externe
Bibliothek oder automatische Zusammenführung. Schwellenwerte werden an
synthetischen Beispielen und realistisch anonymisierten Testfällen justiert.

### B6. Plattform-Datenpfade (vor M0/M7)

**Abgeschlossen für M0:** Die empfohlenen Pfade sind übernommen und zentral in
`platform/paths.py` umgesetzt. Der systemweite Linux-Dienst folgt erst in M7.

**Vorschlag:**

- systemweiter Linux-Dienst: `/var/lib/ebauteilefuchs`;
- benutzerlokale Linux-Entwicklung: XDG-Datenpfad;
- Windows: `%LOCALAPPDATA%\eBauteileFuchs`;
- Docker: `/data` als Pflichtvolume;
- Repository-Entwicklung: `./data`, vollständig ignoriert.

Installationsskripte dürfen vorhandene Datenpfade nie ungefragt überschreiben.

### B7. Backupformat und Verschlüsselung (vor M6)

**Übernommen:** versioniertes ZIP mit Manifest und Prüfsumme; keine eigene
Backupverschlüsselung in V1.

**Vorschlag:** versioniertes ZIP-Archiv mit konsistenter SQLite-Kopie,
JSON-Manifest und SHA-256-Prüfsumme. V1 verschlüsselt Backups nicht selbst;
Dokumentation empfiehlt verschlüsselte Zielmedien. In-App-Verschlüsselung würde
Schlüsselverwaltung und Restore-UX wesentlich erweitern und benötigt eine
gesonderte Freigabe.

### B8. PWA-Umfang und Browserunterstützung (vor M5)

**Übernommen:** installierbare App-Shell ohne Offline-Buchungen.

**Vorschlag:** aktuelle stabile Versionen von Chrome/Edge/Firefox und Safari auf
iOS; installierbare App-Shell, aber keine offline Buchungen. Eine verlorene
Verbindung zeigt einen klaren Status und lässt erst nach Serverbestätigung weiter
buchen.

### B9. Windows-Paketierung (vor M7)

**Übernommen:** zuerst PowerShell-Start und entpackbares Paket; EXE-Bündelung wird
gesondert geprüft.

**Vorschlag:** V1 liefert zuerst ein getestetes PowerShell-Startskript und ein
entpackbares Paket. Die konkrete EXE-Bündelung (zum Beispiel PyInstaller) wird in
einem eigenen Spike geprüft, da native Abhängigkeiten, Virenscanner-Signale und
Updateverhalten die Wahl beeinflussen.

## C. Bewusst gesetzte V1-Entscheidungen

Diese Punkte sind im Plan bereits als Standard gesetzt und müssen nur geändert
werden, wenn die Produktabsicht abweicht:

- modularer Monolith statt getrenntem Frontend/Backend;
- SQLite als Standard, keine PostgreSQL-Zusage in V1;
- UUIDs und stabile QR-Tokens statt sprechender Primärschlüssel;
- Bewegungsjournal plus materialisierter Saldo;
- keine negativen Bestände;
- kein Login und keine Rollen, daher ausdrücklich nur vertrauenswürdiges lokales
  Netz und keine öffentliche Internetfreigabe;
- keine offline Bestandsbuchungen in der PWA;
- nur Mouser als Lieferantenadapter;
- kein endgültiges Maskottchen ohne freigegebenes Asset;
- deutsche UI/Dokumentation, englische Code- und API-Bezeichner.

## D. Später, nicht blockierend für Version 1

- zusätzliche Sprachen;
- weitere Datenbanken und Mehrprozessbetrieb;
- zusätzliche Lieferantenadapter;
- Benutzerkonten und Rollen;
- verschlüsselte Backups in der Anwendung;
- signierter Auto-Updater und vollwertiger Windows-Installer;
- semantische Einheitenumrechnung;
- Cloud- oder Offline-Synchronisation.

## Freigabestatus

M0 ist freigegeben. M1 und spätere Meilensteine benötigen weiterhin eine
ausdrückliche Freigabe. Vor M1 ist lediglich das konkrete Standard-Etikettenraster
aus B2 noch zu benennen; dies blockiert M0 nicht.
