# Interne REST-API – M5

Status: M5 umgesetzt am 24. August 2026. Die API ist vor Version 1.0 intern und
kann sich zwischen Vorabversionen ändern. Die interaktive OpenAPI-Beschreibung
steht im laufenden System unter `/docs`.

## Globale Suche und Verbindung

- `GET /api/v1/search`: optionale Parameter `q`, `category_id`, `with_stock` und
  `location_scope_id`. Mehrere normalisierte Suchwörter werden mit UND über
  Stammdaten, Lieferantennummern, Eigenschaften, Notizen und aktuelle Lagerpfade
  verknüpft. Antworten enthalten neutrale Artikeldaten, Kernattribute,
  Lagerpositionen und Gesamtmengen je Einheit.
- `GET /api/v1/connection`: Computername, aktuelle Browserbasis, erkannte lokale
  IPv4-Kandidaten und ausgewählte URL. Es werden keine Netzwerkänderungen
  vorgenommen.

Der HTML-Endpunkt `GET /connection/qr.svg?base_url=...` akzeptiert ausschließlich
vollständige HTTP(S)-Basis-URLs ohne Zugangsdaten, Pfad, Query oder Fragment.

## Bestand lesen

- `GET /api/v1/inventory`: Salden; optionale Filter `article_id`, `location_id`
  und `include_zero`.
- `GET /api/v1/inventory/transactions`: letzte Bewegungen; optionale Filter
  `article_id`, `location_id` und `limit` (1 bis 250).

Saldoantworten enthalten Artikel, Lagerplatz, vollständigen Lagerpfad, Menge,
Einheit, Versionszähler und Aktualisierungszeit. Journalantworten ergänzen
Transaktionsart, Kommentar, Delta und Bestand nach der Bewegung.

## Bestand schreiben

Alle Schreibaufrufe benötigen `Idempotency-Key` als HTTP-Header. Zulässig sind 8
bis 128 druckbare ASCII-Zeichen. Ein Client erzeugt für jeden fachlich neuen
Vorgang einen neuen Schlüssel und verwendet bei Wiederholung desselben Requests
denselben Schlüssel.

| Methode und Pfad | Zweck | Wesentliche Felder |
| --- | --- | --- |
| `POST /api/v1/inventory/initial` | Anfangsbestand ohne bestehende Historie | `article_id`, `location_id`, `quantity`, `unit`, `comment` |
| `POST /api/v1/inventory/stock-in` | Einlagerung | wie oben |
| `POST /api/v1/inventory/stock-out` | Auslagerung | wie oben |
| `POST /api/v1/inventory/transfers` | atomare Umlagerung | `article_id`, `source_location_id`, `target_location_id`, `quantity`, `unit`, `comment` |
| `POST /api/v1/inventory/adjustments` | Korrektur | genau eines aus `difference` oder `target_quantity` plus Artikel/Lagerplatz |

Buchungsantworten enthalten `transaction_id`, `transaction_type`,
`idempotency_key`, `repeated` und alle zugehörigen Bewegungen. Eine identische
Wiederholung antwortet mit derselben Transaktion und `repeated: true`. Derselbe
Schlüssel mit anderem Inhalt ergibt `409 idempotency_conflict`.

## Mengen und Fehler

Mengen werden als Dezimalwerte mit höchstens acht Nachkommastellen verarbeitet.
Ein- und Auslagerungen sowie Transfers verlangen eine Menge größer als null.
Negative Folgesalden ergeben `409 insufficient_stock` mit dem Feld `available`.
Unbekannte Referenzen ergeben 404, deaktivierte Lagerplätze und konkurrierende
Schreibzugriffe 409, fehlerhafte Mengen oder Formate 422. Antworten enthalten
keine internen SQL- oder Dateipfaddetails.

Schreibzugriffe aus Browserformularen verwenden zusätzlich CSRF-Tokens. Fremde
Origins werden wie bei den bisherigen `/api/v1`-Ressourcen abgewiesen.

## Mouser und neutrale Lieferantenergebnisse

- `GET /api/v1/suppliers/mouser/status`: nur Status „eingerichtet“ sowie der aus
  Vertragsgründen deaktivierte Mouser-Cache; niemals der Schlüssel.
- `POST /api/v1/suppliers/mouser/search`: `query`, `mode` (`part_number`,
  `manufacturer_part_number`, `keyword`, `barcode`) und optional
  `force_external`. Lokale Treffer werden zuerst geliefert. Neutrale externe
  Ergebnisse enthalten nur geprüfte Felder und gemappte Eigenschaften, keine
  beliebige Mouser-Rohantwort.
- `POST /api/v1/suppliers/mouser/import`: kontrollierter Neuimport oder reine
  Zuordnung über `existing_article_id`. Benötigt `Idempotency-Key`. Die eindeutige
  Mouser-Lieferantennummer macht dieselbe Importwiederholung natürlich idempotent.
- `DELETE /api/v1/suppliers/mouser/cache`: bereinigt den allgemeinen Supplier-
  Cache. Mouser selbst schreibt wegen der veröffentlichten API-Bedingungen keine
  Einträge.

Fehlender Schlüssel und Netzwerkfehler ergeben 503, abgelehnte Authentifizierung
und ungültige Antworten 502, Rate Limits 429, fehlerhafte Eingaben 422 und sichere
Dubletten 409. Antworten und Logs enthalten keinen API-Schlüssel.
