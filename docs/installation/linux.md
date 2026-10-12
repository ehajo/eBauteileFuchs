# Linux-Server und systemd

Für x86-64-Linux und Raspberry Pi OS ist Docker weiterhin die einfachste
Betriebsform. Diese Anleitung beschreibt zusätzlich die native Installation als
systemd-Dienst ohne Root-Ausführung der Anwendung.

## Native Installation

1. Python 3.12 samt `venv`, Git und ein geeignetes Zielverzeichnis installieren.
2. Repository nach `/opt/ebauteilefuchs` klonen. Dieses Beispiel verwendet
   bewusst keinen privaten Benutzerpfad:

   ```bash
   sudo git clone <REPOSITORY-URL> /opt/ebauteilefuchs
   sudo chown -R "$USER" /opt/ebauteilefuchs
   cd /opt/ebauteilefuchs
   ./scripts/install-linux.sh
   ```

3. Den systemd-Dienst einrichten:

   ```bash
   sudo ./scripts/install-systemd.sh
   sudoedit /etc/ebauteilefuchs/ebauteilefuchs.env
   sudo systemctl restart ebauteilefuchs
   ./scripts/service-status.sh
   ```

Die Environment-Datei ist nur für root und den Dienstbenutzer lesbar. Dort
`EBAUTEILEFUCHS_PUBLIC_BASE_URL` auf die dauerhafte LAN-Adresse setzen und den
optionalen Mouser-Schlüssel ausschließlich dort eintragen. Die Daten liegen
standardmäßig in `/var/lib/ebauteilefuchs`; der Dienstbenutzer besitzt nur dort
Schreibrechte.

Der Dienst startet nach dem Netzwerk, führt vor dem Webstart kontrolliert
`alembic upgrade head` aus und startet bei Fehlern neu. Journal-Ausgaben:

```bash
sudo journalctl -u ebauteilefuchs -f
```

## Update, Backup und Wiederherstellung

Vor jedem Update unter **Daten** eine Sicherung erstellen. Danach:

```bash
cd /opt/ebauteilefuchs
sudo ./scripts/update-linux.sh
```

Die Anwendung führt Migrationen kontrolliert aus. Backup und Restore sind über
die Oberfläche bevorzugt, weil sie konsistente SQLite-Snapshots und eine
Vorsicherung erzeugt. Für administrative Abläufe stehen zusätzlich
`scripts/backup.py` und `scripts/restore.py DATEI.zip --confirm` bereit. Der
Restore ersetzt Daten; vorher Dienst stoppen und Sicherung prüfen.

## Deinstallation

```bash
sudo systemctl disable --now ebauteilefuchs
sudo rm /etc/systemd/system/ebauteilefuchs.service
sudo systemctl daemon-reload
```

Das Datenverzeichnis `/var/lib/ebauteilefuchs`, `/etc/ebauteilefuchs` und das
Repository werden absichtlich nicht automatisch gelöscht. Erst nach geprüfter
Sicherung dürfen sie bewusst manuell entfernt werden.

Für Docker-Befehle, Volume und Testcontainer siehe
[Docker-Betrieb](docker.md). Native Entwicklung bleibt mit
`scripts/start-dev.sh` möglich.
