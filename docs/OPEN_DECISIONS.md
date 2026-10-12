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

**Abgeschlossen für M1:** frei konfigurierbarer A4-Bogen und universelles
Einzeletikett sind umgesetzt. Als praxistauglicher Standard gilt das Raster
70 × 36 mm mit 24 Etiketten pro A4-Seite (3 × 8), kompatibel zum verbreiteten
Avery-Zweckform-Format 3475. Abweichende Bögen können über Ränder, Raster,
Etikettengröße und Abstände im REST-Vertrag beschrieben werden.

**Vorschlag für V1:** A4-Bogen frei konfigurierbar über Ränder, Spalten, Zeilen
und Etikettengröße sowie ein universelles Einzeletikett. Ein konkretes häufig
verwendetes Standardraster sollte eHaJo benennen, damit reale Drucktests nicht an
der Hardware vorbeigehen.

### B3. Mengeneinheiten (vor M3)

**Abgeschlossen für M3:** Standard `Stück`, Dezimalmengen mit höchstens acht
Nachkommastellen und keine Einheitenumrechnung in V1 sind umgesetzt. Salden werden
je Artikel, Lagerplatz und Einheit getrennt geführt; Gesamtanzeigen vermischen
unterschiedliche Einheiten nicht.

**Vorschlag:** pro Artikel/Lagerplatz genau eine frei benannte Einheit, Standard
`Stück`; Mengen als Dezimalzahl. Umrechnungen zwischen Rollen, Metern, Packungen
und Stück sind nicht Teil von V1. Ein Einheitenwechsel bei bestehender Historie
erfordert eine Korrekturbuchung beziehungsweise neuen Bestandsschlüssel.

### B4. Mouser-Cache-Aufbewahrung (vor M4)

**Abgeschlossen für M4:** Der allgemeine Cache-Port und das relationale
Cache-Schema sind umgesetzt. Für Mouser ist die Speicherung von API-Inhalten
deaktiviert, weil die am 24. August 2026 geprüften veröffentlichten
Mouser-API-Bedingungen Caching, Aufzeichnung und sonstige Speicherung ausdrücklich
untersagen. Ohne abweichende schriftliche Erlaubnis von Mouser gelten deshalb
effektiv 0 Sekunden Aufbewahrung und kein Offline-Fallback auf Mouser-Daten.

**Vorschlag:** erfolgreiche Suchergebnisse 24 Stunden, „kein Treffer“ 15 Minuten,
Fehler nicht cachen; manuelles Leeren in Einstellungen. Rohantworten nur soweit
für Mapping und Diagnose nötig speichern. Vor Umsetzung sind die aktuellen
Mouser-API-Nutzungsbedingungen auf erlaubte Cache-Dauer zu prüfen.

### B5. Suchähnlichkeit (vor M2/M5)

**Abgeschlossen für M2:** Die konservative transparente Warnung ist als Stufe 4
umgesetzt. Sie vergleicht normalisierte Bezeichnungen nur innerhalb derselben
Kategorie, legt niemals automatisch zusammen und verlangt vor einem neuen
Artikel eine ausdrückliche Bestätigung. Die globale Suchgewichtung wird in M5
weiter verfeinert.

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

**Abgeschlossen für M6:** versioniertes ZIP mit konsistenter SQLite-Kopie,
strengem JSON-Manifest, SHA-256 und automatischer Vorsicherung; keine eigene
Backupverschlüsselung in V1.

**Vorschlag:** versioniertes ZIP-Archiv mit konsistenter SQLite-Kopie,
JSON-Manifest und SHA-256-Prüfsumme. V1 verschlüsselt Backups nicht selbst;
Dokumentation empfiehlt verschlüsselte Zielmedien. In-App-Verschlüsselung würde
Schlüsselverwaltung und Restore-UX wesentlich erweitern und benötigt eine
gesonderte Freigabe.

### B8. PWA-Umfang und Browserunterstützung (vor M5)

**Abgeschlossen für M5:** installierbare App-Shell ohne Offline-Buchungen. Der
Service Worker cached ausschließlich statische Shell-Ressourcen und die
Offline-Hinweisseite. Schreibformulare werden ohne erfolgreichen Serverkontakt
gesperrt; fachliche Daten gelangen nicht in den Browsercache.

Die nachträgliche Praxisergänzung nutzt für Verpackungsbarcode-Suchen bei Mouser
ausschließlich lokale Browsererkennung. Ein lokal mitgelieferter Foto-Decoder
funktioniert im privaten LAN auch über HTTP; das laufende Live-Kamerabild bleibt
eine optionale HTTPS-Komfortfunktion. Bei fehlender Browserunterstützung stehen
Eingabe oder Tastaturscanner bereit. Bilder werden weder hochgeladen noch
gespeichert.

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
- das bereitgestellte Fuchs-Maskottchen ist für die konsistente Verwendung in der
  Anwendung freigegeben; Logo und Illustration bleiben unverändert;
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

M0 bis M6 sind abgenommen. M7 ist für die Veröffentlichungsvorbereitung
ausdrücklich freigegeben; Git-Tag, GitHub-Release und Veröffentlichung bleiben
weiterhin gesondert freigabepflichtig. Für M6 und M7 sind keine neuen
Fachentscheidungen offen.

Die Praxisentscheidung zum Löschen hierarchischer Lagerplätze ist abgeschlossen:
referenzierte Knoten werden nicht hart gelöscht, sondern verborgen archiviert.
Bestände bleiben wahlweise auf dem internen Systemlagerplatz „Ohne Lagerplatz“
oder werden nachvollziehbar umgebucht; vollständig gelöschte Artikel werden nach
Ausbuchung deaktiviert. Das unveränderliche Journal bleibt in allen Fällen erhalten.
