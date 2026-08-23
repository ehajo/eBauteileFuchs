# UX-Abläufe – eBauteileFuchs Version 1

Status: Grundsätzlich freigegeben am 23. August 2026

## 1. Bedienkonzept

Die Oberfläche optimiert wiederkehrende Lagerarbeit, nicht maximale Datendichte.
Jede Kernseite besitzt genau eine primäre Aktion. Scan-Felder akzeptieren die
Tastatureingabe gewöhnlicher USB-Scanner und werten Enter als Scanabschluss. Der
Fokus springt nach einem erfolgreichen Schritt automatisch zum nächsten
benötigten Feld; Fehler belassen ihn im korrigierbaren Feld.

Auf Smartphones sind Ziele mindestens gut mit dem Daumen erreichbar, wichtige
Informationen stehen vor Zusatzdetails und die Hauptaktion bleibt sichtbar. Auf
dem PC funktionieren Tab, Shift+Tab, Enter und Escape konsistent. Modale Dialoge
werden nur für irreversible beziehungsweise risikoreiche Bestätigungen verwendet.

## 2. Gemeinsame Scanregeln

- Ein Scan wird erst nach Enter oder explizitem Absenden verarbeitet.
- Führende/trailing Leerzeichen und Scannersteuerzeichen werden entfernt; der
  sichtbare Originalinhalt bleibt zur Kontrolle erhalten.
- Während einer Anfrage ist die Aktion gesperrt und zeigt einen Fortschrittsstatus.
- Jeder Buchungsversuch erhält ein einmaliges Token. Doppelklick, Enter-Wiederholung
  und HTMX-Retry erzeugen keine zweite Bewegung.
- Erfolg wird mit Klartext, Artikel, Menge und Lagerplatz bestätigt. Fehlermeldungen
  erklären den nächsten möglichen Schritt.
- Escape bietet Abbruch beziehungsweise Rückkehr, ohne bereits bestätigte
  Buchungen rückgängig zu machen.

## 3. Einlagern

### 3.1 Bekannter Artikel – Schnellweg

```text
Artikel scannen
  -> lokaler eindeutiger Treffer
  -> Artikel + vorhandene Lagerplätze/Bestände anzeigen
  -> Standardlagerplatz vorauswählen (bei genau einem aktiven Ort)
  -> Menge eingeben
  -> Lagerplatz bestätigen oder Lagerplatz-QR scannen
  -> Zusammenfassung bestätigen
  -> Erfolg; Fokus zurück auf Artikelscan
```

Die Menge startet nicht automatisch bei 1, sofern dies nicht später als
Nutzereinstellung freigegeben wird. Ein abweichender Lagerplatz ist immer
erkennbar auswählbar.

### 3.2 Unbekannter Artikel

```text
Artikelnummer/Barcode eingeben
  -> lokale Suche ohne Treffer
  -> Mouser verfügbar?
       nein: verständlicher Grund + „Manuell anlegen“
       ja: Mouser-Suche
  -> kein Treffer: Suche ändern | manuell anlegen | abbrechen
  -> ein Treffer: prüfbares, bearbeitbares Importformular
  -> mehrere Treffer: Vergleichsauswahl
  -> Dublettenprüfung
  -> neuer Artikel oder vorhandenen Artikel auswählen
  -> Menge + Lagerplatz
  -> Bestätigung und Buchung
```

Manuelle Anlage und Mouser-Import verwenden dasselbe Formular. Importwerte werden
markiert, fehlende Werte bleiben leer. „Zurück“ verliert die eingegebene Menge und
den Scan nicht, solange keine Buchung erfolgt ist.

### 3.3 Mehrere Mouser-Treffer

Jede Ergebniszeile/-karte zeigt Bezeichnung, Hersteller, Herstellerartikelnummer,
Mouser-Nummer, Kategorie, Bauform, zentrale Eigenschaften sowie Produkt- und
Datenblatt-Link. Auf dem Smartphone werden Kernwerte zuerst gezeigt, Details sind
aufklappbar. Aktionen: Treffer auswählen, Suche ändern, vollständig abbrechen.
Eine Auswahl öffnet immer die bearbeitbare Prüfung vor dem Speichern.

### 3.4 Dublettensituation

- Sicherer Einzelkandidat: vorhandener Artikel, Lieferantenzuordnungen,
  Lagerplätze und Bestände werden gezeigt. Aktionen: am vorhandenen Lagerplatz
  einlagern, anderen Lagerplatz verwenden, neue Supplier-Nummer zuordnen, abbrechen.
- Mehrere Kandidaten: Unterschiede werden nebeneinander beziehungsweise als
  mobile Karten dargestellt. Der Nutzer wählt genau einen oder bricht ab.
- Nur Ähnlichkeitswarnung: „Trotzdem neu anlegen“ bleibt möglich, ist aber nicht
  vorausgewählt.

## 4. Auslagern

### 4.1 Start mit Artikel

```text
Artikel suchen/scannen
  -> Bestände nach Lagerplatz anzeigen
  -> Lagerplatz wählen oder QR scannen
  -> Menge: -1 | -5 | alles | frei
  -> Restbestand und Entnahme vorab anzeigen
  -> bestätigen
  -> Erfolg; Fokus zurück auf Artikelscan
```

Aktionen über dem verfügbaren Bestand sind deaktiviert. Eine freie Menge wird
serverseitig erneut gegen den aktuellen Bestand geprüft.

### 4.2 Start mit Lagerplatz-QR

Der QR öffnet den Lagerplatzkontext und zeigt dort vorhandene Artikel. Bei genau
einem Bestand kann dieser vorausgewählt werden; ansonsten wird Artikel gescannt
oder aus der Liste gewählt. Danach gilt derselbe Mengen- und Bestätigungsablauf.

### 4.3 Konfliktfall

Hat sich der Bestand seit Anzeige verändert, erfolgt keine stille Anpassung. Die
Seite zeigt alten und aktuellen Bestand, verlangt eine neue Mengenauswahl und
erzeugt noch keine Bewegung.

## 5. Suche und Artikel

### Globale Suche

Das Suchfeld steht oben, erhält auf der Suchseite automatisch Fokus und startet
per Enter. Ergebnisse zeigen Bezeichnung, Hersteller/MPN, wichtigste Eigenschaften,
Gesamtbestand und primären Lagerpfad. Filter für Kategorie, „mit Bestand“ und
Lagerbereich werden nach dem ersten Ergebnis angeboten, ohne die einfache Suche
zu verdecken.

Ein Ergebnis führt zur Artikeldetailseite mit:

- Stammdaten und technischen Eigenschaften;
- Lieferantenzuordnungen;
- Bestand je Lagerplatz und Gesamtbestand;
- letzten Bestandsbewegungen;
- Aktionen Einlagern, Auslagern und Bearbeiten.

Änderungen an identitätsbildenden Feldern lösen vor dem Speichern erneut die
Dublettenerkennung aus.

## 6. Lagerplätze

### Hierarchie verwalten

Die Standardansicht zeigt einen aufklappbaren Baum und auf kleinen Bildschirmen
einen navigierbaren Pfad. Anlegen geschieht im Kontext des Elternknotens. Vor dem
Verschieben zeigt eine Vorschau alten und neuen Pfad. Zyklen und doppelte
Geschwisterkennungen werden direkt erklärt.

### Magazin-Assistent

1. Elternlagerplatz und Kindtyp wählen.
2. Anzahl, Startnummer, Stellenzahl, Kennungs- und Namensmuster eingeben.
3. Vorschau aller erzeugten Schubladen prüfen.
4. Konflikte werden markiert; es wird nichts teilweise angelegt.
5. Einmal bestätigen; danach Zusammenfassung und optional QR-Sammel-PDF öffnen.

Voreinstellung für 60 Schubladen: Start 1, zwei Stellen, Kennungen `01` bis `60`.

### QR-Etiketten

Einzelansicht und Sammelauswahl zeigen vor dem PDF-Export eine Vorschau mit
Logo, Produktname, Lagerplatzkennung/-name, optional vollständigem Pfad und QR.
Papierformat und Etikettenraster werden aus freigegebenen V1-Vorgaben gewählt.

## 7. Verbindung

Die Seite zeigt Computername, Port und jede geeignete Adresse als vollständige
URL mit eigenem QR-Code. Eine empfohlene Adresse ist hervorgehoben, aber nicht
als sicher korrekt behauptet. Der Nutzer kann eine Adresse auswählen oder eine
manuell konfigurierte Basis-URL verwenden. Hinweise: Smartphone im selben Netz,
gegebenenfalls Windows-Firewall freigeben, für dauerhafte Ausdrucke feste IP oder
DHCP-Reservierung verwenden.

## 8. Einstellungen, Export und Backup

Einstellungen gruppieren Verbindung, Mouser-Status (Schlüssel nur als
„eingerichtet/nicht eingerichtet“), Datenpfade, Export und Datensicherung.

- CSV-Export zeigt Inhalt, Zeitpunkt und Downloadaktion.
- Backup zeigt Ziel, Datenbank-/Schemaversion und Prüfsumme nach Erfolg.
- Restore ist ein geführter Hochrisikoablauf: Datei wählen, prüfen, Inhalt und
  Version anzeigen, Warnung bestätigen, automatische Vorsicherung, Restore,
  Integritätsprüfung und Neustarthinweis. Fehlgeschlagene Prüfung verändert
  niemals die aktive Datenbank.

## 9. Leere, Lade- und Fehlerzustände

Jede Liste besitzt einen hilfreichen Leerzustand mit passender Hauptaktion. HTMX-
Anfragen zeigen einen lokalen Ladeindikator und lassen die Navigation nutzbar.
Offline- oder Serverfehler unterscheiden „Verbindung verloren“ von fachlichen
Fehlern. Mouser-Fehler bieten Suche erneut versuchen, ändern, manuell anlegen oder
abbrechen – aber keine erfundenen Ersatzdaten.

## 10. Branding und Barrierearmut

Die dunkle Gestaltung verwendet die freigegebenen eHaJo-Farben als zentral
definierte Tokens. Das unveränderte Logo erscheint in Navigation, Start,
Verbindungsseite und Druckansicht. Der Maskottchenbereich bleibt bis zur Freigabe
ein neutraler Platzhalter. Browser-Titel, Manifest, Footer und Terminalausgabe
verwenden die festgelegten Texte. Fokus, Fehler und Erfolg sind zusätzlich zu
Farbe durch Rahmen, Icon und Text erkennbar; Bewegung respektiert reduzierte
Bewegungspräferenzen.
