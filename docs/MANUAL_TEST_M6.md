# Manuelle Abnahme M6 unter Windows

Diese Prüfung verwendet eine Testkopie deiner Daten. Den normalen Server vorher
beenden und den produktiven Datenordner nicht verändern.

1. Eine Kopie des Datenordners anlegen und in einer nicht versionierten `.env`
   als `EBAUTEILEFUCHS_DATA_DIR` eintragen.
2. In PowerShell `powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1`
   ausführen. Nur diesen selbst gestarteten Server verwenden.
3. Startseite, `/api/v1/health`, Artikel, Lagerplätze und Bestand öffnen.
4. Unter **Daten** alle vier CSV-Dateien herunterladen. Umlaute, Original-
   Herstellerartikelnummern, Lieferantennummern, Werte/Einheiten, Lagerpfade und
   Dezimalmengen stichprobenartig prüfen.
5. **Sicherung erstellen** wählen. Download und zusätzliche ZIP-Datei im
   angezeigten Sicherungsordner prüfen.
6. Einen eindeutig erkennbaren Testartikel in der Testkopie ändern.
7. Die ZIP-Datei unter **Sicherung wiederherstellen** auswählen, Prüfvorschau
   kontrollieren, `WIEDERHERSTELLEN` eingeben und bestätigen.
8. Anwendung mit `Strg+C` beenden und per PowerShell neu starten. Die Änderung
   aus Schritt 6 muss zurückgesetzt sein; Health-Check, Artikel, Lagerplätze,
   Bestand und Journal müssen funktionieren.
9. Im Sicherungsordner muss zusätzlich eine `vorsicherung` vorhanden sein.
10. Fehlerfälle prüfen: umbenannte Textdatei, beschädigte ZIP-Kopie, falscher
    Bestätigungstext und zu große Datei. Die laufenden Daten dürfen sich nicht
    ändern und die Meldung muss verständlich sein.
11. Browser auf Smartphonebreite ziehen. Karten, Dateiauswahl, Prüfsumme und
    Bestätigung müssen ohne horizontales Seitenrollen bedienbar sein.

M6 enthält keine Docker-, systemd-, Raspberry-Pi-, Paketierungs-, Release- oder
Updatefunktion; diese Punkte beginnen ausdrücklich erst mit M7.
