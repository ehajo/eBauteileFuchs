# Interne REST-API – M3

Status: M3 umgesetzt am 23. August 2026. Die API ist vor Version 1.0 intern und
kann sich zwischen Vorabversionen ändern. Die interaktive OpenAPI-Beschreibung
steht im laufenden System unter `/docs`.

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
