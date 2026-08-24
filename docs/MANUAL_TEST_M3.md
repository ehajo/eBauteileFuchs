# Manuelle Abnahme von M3

Diese Anleitung verwendet ausschließlich synthetische Beispieldaten.

## Windows-Start

In PowerShell im Repository:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

Die im Terminal ausgegebene Adresse öffnen, normalerweise
`http://127.0.0.1:8008`. Health-Check unter `/api/v1/health`, Startseite,
`/articles`, `/locations` und `/inventory` prüfen.

## Testdaten

1. Unter **Artikel** einen synthetischen Artikel „Testwiderstand 10 kΩ“ anlegen.
2. Unter **Lagerplätze** zwei aktive Plätze `TEST-A` und `TEST-B` anlegen.
3. Beim ersten Platz **Hier einlagern** öffnen und als initialen Bestand 10 Stück
   über den eigenen Ablauf **Initialen Bestand erfassen** buchen.

## Buchungen

1. 5 Stück an `TEST-A` einlagern: neuer Bestand 15.
2. Über **Auslagern** die Schnellmenge 1 wählen: neuer Bestand 14.
3. 5 Stück von `TEST-A` nach `TEST-B` umlagern: Salden 9 und 5, Gesamtbestand 14.
4. Auf `TEST-B` den Zielbestand 6 korrigieren und „Synthetische Zählprobe“ als
   Begründung angeben: Korrekturdifferenz +1, Gesamtbestand 15.
5. Eine Auslagerung von 10 Stück aus `TEST-B` versuchen. Sie muss ohne Bewegung
   und mit verständlicher Meldung abgewiesen werden.
6. Browser-Zurück beziehungsweise Neuladen nach einer bestätigten Buchung testen.
   Der Vorgang darf nicht doppelt erscheinen.
7. Artikel- und Lagerplatzdetailseiten öffnen und Salden, Lagerpfade sowie letzte
   Bewegungen vergleichen.

## Scanner und Smartphone

Ein Suchfeld unter **Einlagern** oder **Auslagern** fokussieren, eine bekannte
Artikelnummer mit einem USB-Scanner eingeben und Enter abschließen. Die passende
Ergebnisliste muss unmittelbar darunter erscheinen. Artikel auswählen und
prüfen, dass beim Auslagern ausschließlich Lagerplätze mit Bestand angeboten
werden. Danach Lagerplatz und Menge auswählen.

Für den Smartphone-Test `EBAUTEILEFUCHS_PUBLIC_BASE_URL` auf die lokale, vom
Smartphone erreichbare PC-Adresse setzen, beispielsweise
`http://192.168.1.42:8008`. Smartphone und PC müssen im selben vertrauenswürdigen
Netz sein. Einen vorhandenen Lagerplatz-QR scannen und prüfen:

- Lagerplatz, enthaltene Artikel und Mengen werden angezeigt;
- **Hier einlagern** und **Hier auslagern** übernehmen den Lagerplatz;
- die Vorauswahl bleibt auch nach Artikelsuche und Artikelauswahl erhalten;
- Formular, Vorschau, Schnellmengen und Bestätigung sind ohne horizontales
  Scrollen bedienbar;
- nach der Buchung ist der neue Bestand deutlich sichtbar.

Keine öffentliche Portfreigabe einrichten. Eine feste IP beziehungsweise
DHCP-Reservierung ist für dauerhaft gedruckte QR-Codes empfehlenswert.
