# Mouser-Suche und manuelle M4-Abnahme

Stand: 24. August 2026. Beispiele verwenden ausschließlich synthetische Daten.

## API-Schlüssel beantragen und einrichten

1. Auf der offiziellen Mouser-Seite ein MyMouser-Konto anlegen beziehungsweise
   anmelden.
2. Den Antrag für die **Search API** ausfüllen und eBauteileFuchs als lokale
   Anwendung wahrheitsgemäß beschreiben.
3. Die jeweils aktuellen Mouser-API-Bedingungen lesen und akzeptieren.
4. Im Repository `.env.example` nach `.env` kopieren.
5. Den erhaltenen Schlüssel ausschließlich lokal eintragen:

   ```text
   EBAUTEILEFUCHS_MOUSER_API_KEY=dein-lokaler-schlüssel
   ```

Die echte `.env` niemals committen, weitergeben, in Screenshots zeigen oder in
Fehlermeldungen kopieren. Die Anwendung zeigt nur „eingerichtet“ oder „nicht
eingerichtet“. Ohne Schlüssel bleiben alle lokalen Funktionen verfügbar.

Offizielle Quellen:

- Search API und Antrag: <https://www.mouser.com/en/api-search/>
- API-Dokumentation: <https://api.mouser.com/api/docs/ui/index>
- API-Bedingungen: <https://eu.mouser.com/en/apiterms/>

## Ablauf

Unter **Suchen** eine Mouser-Nummer, Herstellerartikelnummer, einen Barcode oder
Freitext eingeben. Enter funktioniert mit einem tastaturartigen USB-Scanner.
eBauteileFuchs sucht zuerst lokal. Bei einem lokalen Treffer werden Stammdaten,
Lagerplätze, Bestände und Einlagerungsaktion gezeigt. Eine externe Suche erfolgt
nur ohne lokalen Treffer oder nach „Trotzdem bei Mouser suchen“.

Mehrere Ergebnisse müssen einzeln ausgewählt werden. Die Prüfseite zeigt die
Quelle, Originalwerte, eindeutige Normalisierungen und nicht zuordenbare
Eigenschaften. Alle importierten Felder bleiben vor dem Speichern bearbeitbar.
Ein vorhandener Artikel kann ausgewählt werden; dann wird nur die Mouser-Nummer
ergänzt. Bestehende Felder, Lagerplätze und Bestände werden nicht verändert.

## Cache und API-Grenzen

Die Projektplanung sah 24 Stunden für Treffer und 15 Minuten für „kein Treffer“
vor, ausdrücklich vorbehaltlich einer Vertragsprüfung. Die veröffentlichten
Mouser-API-Bedingungen verbieten jedoch das Cachen, Aufzeichnen oder sonstige
Speichern von API-Inhalten. Deshalb speichert eBauteileFuchs keine
Mouser-Suchergebnisse und bietet bei Ausfall keinen Cache-Fallback an. Der
allgemeine Cache-Port ist technisch vorhanden, bleibt für Mouser aber leer und
kann kontrolliert über `DELETE /api/v1/suppliers/mouser/cache` bereinigt werden.

Pro Suchaufruf gelten acht Sekunden Timeout und höchstens ein unmittelbarer
Wiederholungsversuch bei einem vorübergehenden Netzwerk- oder Serverfehler. Ein
ungültiger Schlüssel und Rate Limits werden nicht wiederholt. Antworten sind auf
2 MB und 50 Treffer begrenzt.

## Manueller Test unter Windows

1. Ohne Schlüssel starten:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
   ```

2. `/api/v1/health`, Startseite, Artikel, Lagerplätze und Bestand öffnen.
3. **Suchen** öffnen. Der Hinweis „Mouser-Suche nicht eingerichtet“ und die
   manuelle Artikelanlage müssen verfügbar sein.
4. Einen bekannten lokalen Artikel beziehungsweise seine Lieferantennummer
   scannen. Es darf kein externer Aufruf nötig sein; Artikel, Lagerplätze und
   Bestände müssen erscheinen.
5. Optional mit eigenem lokalem Schlüssel neu starten und eine bekannte
   Mouser-Nummer suchen. Niemals Schlüssel oder vollständige Rohantwort notieren.
6. Bei mehreren Treffern einen auswählen, zurückgehen, Suche ändern und abbrechen.
7. Auf der Prüfseite Bezeichnung, Kategorie, Links, Eigenschaften, Original- und
   Normalwerte kontrollieren.
8. Einmal als neuen Artikel importieren. Danach dieselbe Prüfung erneut absenden:
   Es darf kein zweiter Artikel entstehen.
9. Einen Treffer einem vorhandenen synthetischen Artikel zuordnen. Nur die
   Mouser-Zuordnung darf neu sein; Bestand und Lagerplätze müssen unverändert
   bleiben.

## Smartphone-Test

Bei 360 bis 390 px Breite die Suchseite öffnen, Suchart wählen, per Enter suchen,
Trefferkarten vergleichen und die Prüfseite vollständig bedienen. Es darf kein
horizontales Scrollen nötig sein. Externe Links öffnen bewusst Mouser oder das
Datenblatt; Produktbilder werden in M4 nicht eingebettet.

## Erwartete Fehler

Fehlender oder abgelehnter Schlüssel, Offlinezustand, DNS-/Netzwerkfehler,
Timeout, HTTP-Fehler, Rate Limit und ungültige Antworten zeigen deutsche,
handlungsorientierte Meldungen. Suche ändern, erneut versuchen, manuell anlegen
und abbrechen bleiben möglich. Kein Fehler erzeugt oder verändert einen Artikel.
