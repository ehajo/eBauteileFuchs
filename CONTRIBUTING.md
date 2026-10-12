# Mitwirken an eBauteileFuchs

Danke für dein Interesse. Bitte lies zuerst [AGENTS.md](AGENTS.md),
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) und die relevanten Dokumente unter
`docs/`.

## Lokale Prüfung

Verwende Python 3.12. Vor einem Pull Request müssen mindestens folgende Befehle
erfolgreich sein:

```text
ruff format --check .
ruff check .
pytest
```

Für Änderungen an Docker zusätzlich den Testcontainer ausführen. Für
Migrationen sind Upgrade- und Downgrade-Tests erforderlich.

## Regeln für Beiträge

- Fachlogik bleibt von Web-, API- und Persistenzadaptern getrennt.
- Neue Funktionen benötigen verständliche deutsche Produkttexte und passende
  Tests für Erfolg und Fehlerfälle.
- Beispiele, Screenshots und Tests verwenden ausschließlich synthetische Daten.
- Niemals `.env`, Zugangsdaten, Datenbanken, Backups, Exporte oder persönliche
  Lagerdaten committen.
- Änderungen an Logo, Maskottchen oder eHaJo-/eBauteileFuchs-Branding benötigen
  vorherige Zustimmung. Für Forks eigenes Branding verwenden.

Beiträge zum Programmcode erfolgen unter Apache-2.0, soweit nicht schriftlich
etwas anderes vereinbart wurde. Details zu Branding stehen in
[TRADEMARKS.md](TRADEMARKS.md).
