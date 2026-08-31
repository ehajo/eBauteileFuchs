# Manuelle Abnahme von M5

## Windows

1. `powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1` starten.
2. `/search` öffnen. Fokus muss im Suchfeld liegen; Enter muss die Suche starten.
3. Mit synthetischen oder eigenen Daten Kombinationen aus Name, Hersteller-
   beziehungsweise Lieferantennummer, Eigenschaft, Notiz und Lagerpfad suchen.
   Mehrere Wörter müssen als UND wirken.
4. Kategorie, „Nur Artikel mit Bestand“ und einen Raum beziehungsweise ein Regal
   kombinieren. Einzelne Schubladen und Unterfächer dürfen nicht den
   Bereichsfilter überladen. Die kompakten Ergebniszeilen und **Bestand ändern**
   prüfen.
5. Auf der Startseite ohne Umweg einen Artikel suchen. Danach **Bestand ändern**
   öffnen: Bei vorausgewähltem Artikel dürfen weder Artikelsuche noch der große
   Lagerfilter oberhalb der Buchung erscheinen. `+1`, `+5`, `−1` und `−5` müssen
   mit je einem Klick genau eine Bewegung erzeugen.
6. `/locations` öffnen. Große Zweige müssen anfangs geschlossen sein und sich
   einzeln per Tastatur oder Klick öffnen lassen. Checkboxen müssen kompakt neben
   ihrer Beschriftung stehen.
7. Im Magazin-Assistenten ein synthetisches Magazin mit zwei Schubladen anlegen.
   In der Hierarchie muss zuerst das Magazin und darunter müssen die Schubladen
   erscheinen. Zwei vorhandene Geschwisterplätze auswählen und über **In Magazin
   gruppieren** unter ein weiteres Magazin verschieben.
8. Einen Lagerzweig mit Testbeständen auswählen und **Auswahl löschen** öffnen.
   Die Bauteilliste prüfen und die drei Entscheidungen an synthetischen Artikeln
   testen: **Ohne Lagerplatz erhalten**, **Lagerplatz zuweisen** und **Bauteil
   vollständig löschen**. Nach Bestätigung muss der ganze Zweig verschwunden,
   die Bewegungshistorie aber weiterhin vorhanden sein.
9. `/connection` öffnen. Computername, aktuelle Browseradresse und geeignete
   lokale IPv4-Adressen prüfen. Eine synthetische manuelle URL wie
   `http://192.168.1.42:8008` testen; Pfade und `javascript:` müssen abgewiesen
   werden.
10. QR-Code mit einem QR-Leser kontrollieren. Er darf nur die sichtbare URL
   enthalten.
11. In Edge oder Chrome die Installationsmöglichkeit der PWA prüfen. Entwickler-
   werkzeuge offline schalten: Es muss ein deutlicher Hinweis erscheinen und
   Schreibaktionen müssen gesperrt bleiben. Nach Wiederherstellung muss der
   Health-Check die Aktionen wieder freigeben.
12. Health-Check, Artikel, Lagerplätze, Bestand, Mouser-Suche und Buchungsabläufe
   erneut öffnen.

## Smartphone

1. PC und Smartphone mit demselben privaten WLAN verbinden.
2. Auf dem PC `/connection` öffnen und eine tatsächlich erreichbare private
   Adresse auswählen. QR-Code mit dem Smartphone scannen.
3. Falls keine Verbindung möglich ist, Python beziehungsweise TCP-Port 8008 in
   der Windows-Firewall ausschließlich für private Netzwerke erlauben.
4. Startseitensuche, kompakte Treffer, einklappbaren Lagerbaum und gemeinsame
   Schnellbuchung bei mindestens 360 Pixel Breite prüfen. Es darf kein
   horizontales Scrollen nötig sein.
5. Falls der Browser bei der verwendeten vertrauenswürdigen HTTPS-Adresse die
   Installation anbietet, die Website zum Startbildschirm hinzufügen und aus dem
   App-Symbol öffnen. Reines HTTP über eine LAN-IP ist kein sicherer Kontext und
   bietet browserabhängig nur eine normale Verknüpfung statt der vollen PWA.
6. Die Anwendung am Smartphone ausdrücklich über die normale HTTP-LAN-Adresse
   öffnen. Auf der Startseite **Verpackungsbarcode scannen** und **Foto
   aufnehmen** wählen. Einen Barcode von einer Bauteilverpackung fotografieren.
   Danach muss die Mouser-Suchseite mit Suchart **Verpackungsbarcode** geöffnet
   werden. Das Foto darf nicht an den Server übertragen oder gespeichert werden.
7. Eine Verpackung mit mehreren sichtbaren Codes fotografieren und prüfen, dass
   vor der Suche eine kompakte Auswahl der erkannten Nummern erscheint.
8. Ein Würth-Etikett mit `1P`, `1T` und `Q` scannen. Nur der Wert hinter `1P`
   darf als Produktcode auswählbar sein. Lotnummer (`1T`) und Packungsmenge (`Q`)
   müssen korrekt beschriftet erscheinen und dürfen keine Suche auslösen.
9. Optional über vertrauenswürdiges HTTPS den Live-Scan prüfen. Kamera-
   Berechtigung verweigern und sicherstellen, dass Foto-Scan und Texteingabe
   weiterhin verfügbar sind. Ein lokaler Treffer muss vor einer externen Anfrage
   erscheinen; ohne lokalen Treffer muss bei eingerichtetem Schlüssel die
   Mouser-Suche starten. Der Scan selbst darf weder Artikel noch Bestand
   automatisch speichern.
10. WLAN kurz deaktivieren. Offline-Hinweis und gesperrte Schreibaktionen prüfen;
   es darf keine vermeintlich erfolgreiche Offline-Buchung geben.
11. WLAN aktivieren und erst nach bestätigter Serververbindung eine synthetische
   Ein-/Auslagerung vollständig durchführen.

Für dauerhaft gedruckte Verbindungs- oder Lagerplatz-QRs wird eine
DHCP-Reservierung beziehungsweise feste lokale IP empfohlen. Keine öffentliche
Router-Portfreigabe einrichten.
