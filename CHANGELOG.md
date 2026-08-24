# Changelog

Alle wesentlichen Änderungen an eBauteileFuchs werden in dieser Datei
dokumentiert. Das Format orientiert sich an Keep a Changelog; Versionen folgen
Semantic Versioning.

## [Unreleased]

### Added

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
