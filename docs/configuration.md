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
| `EBAUTEILEFUCHS_DATA_DIR` | plattformabhängig | Datenbank, temporäre Exporte und Restore-Ablage |
| `EBAUTEILEFUCHS_BACKUP_DIR` | `<Datenordner>/backups` | lokale ZIP-Sicherungsablage |
| `EBAUTEILEFUCHS_RESTORE_UPLOAD_LIMIT_MB` | `512` | maximale Restore-Dateigröße, 1–4096 MB |
| `EBAUTEILEFUCHS_DATABASE_URL` | lokale SQLite-URL | optionale vollständige SQLAlchemy-URL |
| `EBAUTEILEFUCHS_PUBLIC_BASE_URL` | aktuelle Anfrage-URL | vollständige HTTP(S)-Basis-URL für Lagerplatz-QR-Codes |
| `EBAUTEILEFUCHS_SSL_CERTFILE` | leer | Pfad zu einem lokal vertrauenswürdigen HTTPS-Zertifikat |
| `EBAUTEILEFUCHS_SSL_KEYFILE` | leer | Pfad zum zugehörigen privaten Schlüssel |
| `EBAUTEILEFUCHS_LOG_LEVEL` | `INFO` | `DEBUG` bis `CRITICAL` |
| `EBAUTEILEFUCHS_MOUSER_API_KEY` | leer | persönlicher Schlüssel für die optionale Mouser Search API |
| `EBAUTEILEFUCHS_MOUSER_TIMEOUT_SECONDS` | `8` | Zeitlimit je Mouser-Anfrage in Sekunden (1–30) |

Der Mouser-Schlüssel wird ausschließlich aus der lokalen Umgebung oder `.env`
gelesen. Er darf weder in das Repository übernommen noch in Protokollen oder
Fehlermeldungen ausgegeben werden. Ohne Schlüssel bleiben lokale Suche,
Artikelerfassung und alle übrigen Funktionen verfügbar; nur die externe
Mouser-Suche wird deaktiviert. Einzelheiten stehen in [MOUSER.md](MOUSER.md).

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

Sicherungen liegen standardmäßig in `backups`; kurzlebige Restore-Dateien liegen
während der Prüfung in `restore-staging` und werden danach entfernt. Beide
Verzeichnisse enthalten persönliche Lagerdaten und gehören nicht ins Repository.
Einzelheiten stehen in [BACKUP_RESTORE.md](BACKUP_RESTORE.md).

## Docker

Der Compose-App-Service setzt `EBAUTEILEFUCHS_APP_ENV=production` und
`EBAUTEILEFUCHS_DATA_DIR=/data`. Der in `.env` konfigurierte Port wird sowohl
im Container als auch für die Portfreigabe verwendet. `DATABASE_URL` sollte im
Standardbetrieb leer bleiben, damit SQLite im persistenten `/data`-Volume liegt.
Eine Compose-Datei enthält keinen Mouser-Schlüssel; Docker liest ihn ausschließlich
aus der lokalen, nicht eingebauten `.env`. Die vollständige Betriebsanleitung
steht unter [installation/docker.md](installation/docker.md).

## systemd

Die native Linux-Unit lädt `/etc/ebauteilefuchs/ebauteilefuchs.env`. Die Datei
enthält mindestens Host, Port, Datenpfad, Log-Level und bei Bedarf die öffentliche
LAN-Basis-URL; der optionale Mouser-Schlüssel bleibt darin lokal. Sie muss für
root und den Dienstbenutzer lesbar, aber nicht allgemein lesbar sein. Die
Installation erzeugt eine Vorlage mit Modus `0640`; Details stehen in
[installation/linux.md](installation/linux.md).

## Basis-URL für Lagerplatz-QR-Codes

Ohne Konfiguration verwendet ein erzeugtes Etikett die Basis-URL der aktuellen
Browseranfrage. Für dauerhaft gedruckte Etiketten empfiehlt sich eine stabile,
im lokalen Netz erreichbare Adresse, beispielsweise:

```text
EBAUTEILEFUCHS_PUBLIC_BASE_URL=http://192.168.1.42:8008
```

Erlaubt sind ausschließlich vollständige HTTP- oder HTTPS-URLs ohne eingebettete
Zugangsdaten. Eine öffentliche Internetfreigabe ist nicht vorgesehen.

Unter `/connection` können erkannte lokale Adressen und eine manuelle URL
unverbindlich geprüft werden. Diese Auswahl verändert keine Konfiguration. Soll
dieselbe Adresse nach Neustarts für gedruckte Lagerplatz-QRs gelten, wird sie
weiterhin ausdrücklich über `EBAUTEILEFUCHS_PUBLIC_BASE_URL` gesetzt.

## Optionales HTTPS für Live-Kamera und PWA

Zertifikat und Schlüssel müssen immer gemeinsam konfiguriert werden. Der private
Schlüssel bleibt außerhalb des Repositorys; `.pem`- und `.key`-Dateien sind
zusätzlich ignoriert. Das Zertifikat muss zur verwendeten lokalen IP-Adresse
oder zum Hostnamen passen und seine ausstellende lokale Zertifizierungsstelle
muss auf dem Smartphone vertraut sein. Danach werden Verbindungsadressen mit
`https://` erzeugt und Live-Kamera sowie vollständige PWA-Funktionen stehen dem
Browser zur Verfügung. Der lokale Foto-Barcode-Scan benötigt diese Einrichtung
nicht und funktioniert auch beim HTTP-Aufruf im privaten LAN.
