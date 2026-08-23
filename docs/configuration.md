# Konfiguration

eBauteileFuchs liest Einstellungen aus Umgebungsvariablen und optional aus einer
lokalen `.env`-Datei. Umgebungsvariablen beginnen mit
`EBAUTEILEFUCHS_`. `.env` und alle Laufzeitdaten sind durch `.gitignore`
ausgeschlossen.

| Variable | Standard | Bedeutung |
| --- | --- | --- |
| `EBAUTEILEFUCHS_APP_ENV` | `development` | `development`, `production` oder `test` |
| `EBAUTEILEFUCHS_HOST` | `0.0.0.0` | Bind-Adresse des Webservers |
| `EBAUTEILEFUCHS_PORT` | `8008` | TCP-Port 1–65535 |
| `EBAUTEILEFUCHS_DATA_DIR` | plattformabhängig | Datenbank- und späterer Dateipfad |
| `EBAUTEILEFUCHS_DATABASE_URL` | lokale SQLite-URL | optionale vollständige SQLAlchemy-URL |
| `EBAUTEILEFUCHS_LOG_LEVEL` | `INFO` | `DEBUG` bis `CRITICAL` |

Der Mouser-Schlüssel ist in `.env.example` nur als auskommentierter Platzhalter
enthalten und wird erst in M4 verwendet.

## Datenpfade

- Entwicklung und Tests: `./data`
- Windows-Produktion: `%LOCALAPPDATA%\eBauteileFuchs`
- benutzerlokales Linux: `$XDG_DATA_HOME/ebauteilefuchs` oder
  `~/.local/share/ebauteilefuchs`
- Docker: `/data`
- systemweiter Linux-Dienst ab M7: `/var/lib/ebauteilefuchs`

SQLite verwendet Foreign Keys, WAL und einen Busy-Timeout von fünf Sekunden.
Migrationen werden bewusst mit `python -m alembic upgrade head` ausgeführt und
nicht stillschweigend beim Import der Anwendung.
