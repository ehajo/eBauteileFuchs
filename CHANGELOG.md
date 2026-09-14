# Changelog

Alle wesentlichen Änderungen an eBauteileFuchs werden in dieser Datei
dokumentiert. Das Format orientiert sich an Keep a Changelog; Versionen folgen
Semantic Versioning.

## [Unreleased]

### Added

- Lagerzweige mit vielen Schubladen lassen sich in der Hierarchie mit einer
  Aktion vollständig auswählen oder wieder abwählen; die Anzeige nennt die
  Anzahl ausgewählter Lagerplätze vor der Löschvorschau.
- Umschaltbare grafische Lagerkarte mit klaren Raum-, Regal-, Magazin- und
  Fachrastern sowie einer Hervorhebungssuche für den schnellen physischen Zugriff.
- Optionale Rasterangaben (Spalten und Reihen) je Lagerplatz für eine exakt
  passende grafische Fachanordnung; bestehende Plätze bleiben automatisch flexibel.
- Die grafische Lagerkarte zeigt je Fach bis zu fünf enthaltene Bauteile mit
  Mengen und kennzeichnet leere Fächer; weitere Inhalte werden gezählt angezeigt.

- M6-Datenverwaltung mit dokumentierten UTF-8-CSV-Exporten für Artikel,
  Eigenschaften, Lagerplätze und Bestände.
- Versionierte konsistente SQLite-ZIP-Sicherung mit JSON-Manifest,
  Schemaversion und SHA-256 sowie validierter, größenbegrenzter
  Wiederherstellung mit automatischer Vorsicherung und atomarem Austausch.

- Smartphone-Kamera-Scan für Verpackungsbarcodes auf Start- und Mouser-Suchseite;
  erkannte Werte starten automatisch die lokale Vorprüfung und anschließend die
  Mouser-Barcodesuche.
- HTTP-tauglicher Foto-Barcode-Scan mit lokal mitgeliefertem ZXing-Decoder,
  lokaler Bildauswertung und Auswahl bei mehreren Codes; Live-Scan bleibt als
  optionale HTTPS-Komfortfunktion erhalten.
- Würth-Verpackungscodes werden anhand ihrer Datenkennungen interpretiert:
  `1P` wird als Produktcode gesucht, `1T` als Lotnummer und `Q` als
  Packungsmenge erkannt; Lot und Menge gelangen nicht in die Artikelsuche.
- Optionale HTTPS-Zertifikat-/Schlüsselkonfiguration für Kamera-Scan und PWA im
  lokalen Netzwerk.
- Bereits vergebene Alembic-Revision `0007_article_barcodes` als ungenutzte
  Kompatibilitätsrevision beibehalten, damit aktualisierte Datenbanken weiterhin
  ohne Rückstempelung starten.
- Das Windows-Startskript öffnet bei automatischer Portausweichung zuverlässig
  den tatsächlich gewählten Port statt einer fest konfigurierten Basis-URL.
- M5-UND-Suche über Stammdaten, Lieferantennummern, Eigenschaften, Notizen und
  aktuelle Lagerpfade mit Kategorie-, Bestands- und Lagerbereichsfilter.
- Schnellsuche auf der Startseite, kompakte Trefferzeilen und auf echte
  Lagerbereiche begrenzte Filter statt hunderter einzelner Schubladen.
- Gemeinsame Schnellbuchung für Ein- und Auslagerung mit unmittelbar buchenden
  Schaltflächen für `−5`, `−1`, `+1` und `+5` sowie frei eingebbarer Menge.
- Standardmäßig eingeklappte Lagerplatzhierarchie und kompakte Checkboxen.
- Kompaktere Desktop- und Smartphone-Oberfläche mit kleineren, sauber
  umbrechenden Artikelüberschriften, ausgerichteter Markenleiste, konsistent
  eingebundenem Maskottchen und der freigegebenen Originaldatei
  `branding/e_rand_t.png` als Favicon.
- Magazin-Assistent mit eigenständigem Magazin-Elternknoten sowie nachträgliches
  Gruppieren ausgewählter bestehender Lagerplätze unter ein neues Magazin.
- Rekursives, revisionssicheres Löschen ausgewählter Lagerzweige mit Vorschau
  aller betroffenen Bauteile und den Entscheidungen „Ohne Lagerplatz“,
  „Lagerplatz zuweisen“ oder „Bauteil vollständig löschen“.
- Interner, in normalen Auswahllisten unsichtbarer Lagerplatz „Ohne Lagerplatz“
  über Alembic-Revision `0006_unassigned_location`.
- Versionsmarkierte statische Assets und Online-Aktualisierung des PWA-Caches,
  damit Gestaltungsänderungen nicht durch einen alten Offline-Cache verdeckt werden.
- Schnellbuchungsaktionen übertragen ihre Button-Aktion zuverlässig, bevor der
  geklickte Button zum Schutz vor Doppelübermittlung gesperrt wird.
- Lokale Netzwerkerkennung, validierte manuelle Basis-URL und Verbindungs-QR mit
  Windows-Firewall-, WLAN- und DHCP-Hinweisen.
- Installierbare PWA-App-Shell mit lokalem Manifest, Service Worker,
  Offline-Hinweisseite und Sperre von Schreibaktionen ohne Serverbestätigung.
- M4-Lieferantenschnittstelle mit isoliertem Mouser-HTTP-Client,
  defensiven Antwortmodellen und neutralem Produktmapper.
- Lokale Suche vor Mouser, Scanner-/Artikelnummern-, Herstellerartikelnummern-
  und Freitextsuche sowie explizite Auswahl bei mehreren Treffern.
- Bearbeitbare Importprüfung mit Quellenkennzeichnung, Einheiten-Normalisierung,
  freien Rohattributen, Dublettenprüfung und manueller Anlage als Fallback.
- Bewusste Mouser-Zuordnung zu vorhandenen Artikeln ohne Überschreiben lokaler
  Stammdaten, Bestände oder Lagerplätze.
- M4-REST-Ressourcen unter `/api/v1/suppliers/mouser` und generisches
  Supplier-Cache-Schema mit kontrollierter Bereinigung.
- M3-Bestandsjournal mit materialisierten Salden je Artikel, Lagerplatz und
  Einheit sowie unveränderlichen Transaktionen und Bewegungen.
- Initiale Bestände, Einlagerungen, Auslagerungen, atomare Umlagerungen und
  Differenz- beziehungsweise Zielbestandskorrekturen.
- Idempotente Buchungsendpunkte, Buchungstoken, optimistische Saldenversionen und
  SQLite-Schreibserialisierung gegen Doppel- und Negativbuchungen.
- Responsive, scanfreundliche Buchungsseiten mit Schnellmengen, Bestandsvorschau
  sowie Bestands- und Bewegungsanzeigen auf Artikel- und Lagerplatzseiten.
- M3-REST-Ressourcen unter `/api/v1/inventory` einschließlich Journalabfragen.
- M2-Artikelverwaltung mit Herstellern, Kategorien, flexiblen technischen
  Eigenschaften, Lieferantenartikelnummern und lokaler UND-Suche.
- Vierstufige Dublettenerkennung für Lieferantennummern, exakte und normalisierte
  Herstelleridentitäten sowie bewusst bestätigbare Ähnlichkeitswarnungen.
- Responsive Artikelübersicht, Detail- und Bearbeitungsformulare sowie
  entsprechende `/api/v1`-Ressourcen.
- Kompaktes Lagerplatzetikett mit 35 × 13 mm für kleine Magazin-Schubladen.
- Direktes Anlegen eines Unterplatzes aus einer Lagerplatzdetailseite und
  optionale Unterteilung jeder Magazin-Schublade in Unterfach A und B.
- M1-Lagerplatzverwaltung mit System- und eigenen Typen, Hierarchie, Pfadansicht,
  Bearbeitung und kontrollierter Deaktivierung.
- Atomarer Magazin-Assistent mit Vorschau und Voreinstellung für 60 Schubladen.
- Stabile Lagerplatz-QR-Tokens sowie universelle Einzel- und A4-Sammeletiketten
  im Standardformat 70 × 36 mm (3 × 8).
- Versionierte REST-Ressourcen für Lagerplätze, Typen, Stapelanlage und Etiketten.
- Konfigurierbare öffentliche Basis-URL für dauerhaft druckbare QR-Codes.
- M0-Projektfundament mit FastAPI, SQLite, Alembic, Jinja2 und zentraler
  Konfiguration.
- Gebrandete Startseite und Health-Check.
- Entwicklungsstarts für Windows und Linux sowie Docker-Grundlage.
- Apache-2.0-Lizenz und getrennte Markenhinweise.

### Fixed

- Die Barcode-Suche zeigt das Eingabefeld auf Smartphones in voller Breite und
  öffnet nach einem Scan die Bildschirmtastatur nicht erneut.
- Seitentitel verwenden auch bei langen Artikelbezeichnungen eine kompaktere,
  responsive Schriftgröße.
- Die Einlagerung trennt Lagerbereich und buchbaren Endlagerplatz, filtert die
  Auswahl hierarchisch und kann innerhalb des Bereichs den nächsten Platz ohne
  aktuellen Bestand vorauswählen.
- Bestandsmengen werden in der Oberfläche ohne wissenschaftliche Schreibweise
  angezeigt; beispielsweise erscheint `1E+2` jetzt als `100`.
- Technische Artikeleigenschaften bieten passende SI-Einheiten und Vorsätze als
  Auswahl an, etwa pF bis F für Kapazitäten sowie mΩ bis GΩ für Widerstände.
- Die Bestandssuche zeigt passende Artikel unmittelbar unter dem Suchfeld und
  erhält vorausgewählte Lagerplätze auch beim mobilen Einstieg über „Hier
  einlagern“.
- Beim Auslagern werden nach der Artikelauswahl nur Lagerplätze mit tatsächlich
  vorhandenem Bestand angeboten.
- Die Bestandsübersicht ist direkt über die Hauptnavigation erreichbar.
- Unbenutzte Lagerplätze können nach einer Sicherheitsabfrage gelöscht werden;
  verwendete Lagerplätze bleiben als Buchungsnachweis erhalten und können
  weiterhin deaktiviert werden.
- Kopfzeilen und Lagerplatzbäume bleiben bei vielen Aktionen sowie auf schmalen
  Bildschirmen lesbar und korrekt umgebrochen.
- Der Windows-Entwicklungsstart wählt bei belegtem Standardport verständlich den
  nächsten freien Port, statt mit einem Uvicorn-Bindefehler abzubrechen.
- Der Standardport wurde vom häufig belegten Port 8080 auf Port 8008 geändert.
