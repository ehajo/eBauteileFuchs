# Raspberry Pi

eBauteileFuchs läuft auf Raspberry Pi OS mit 64-Bit-Benutzerland (ARM64) per
Docker oder nativ über systemd. Das Dockerfile enthält keine fest verdrahtete
Plattform; Docker baut das passende Image für ARM64 oder x86-64.

1. Raspberry Pi OS 64-Bit aktualisieren und Docker Engine mit dem
   Compose-Plug-in gemäß der [offiziellen Docker-Anleitung für Debian](https://docs.docker.com/engine/install/debian/)
   installieren. Danach prüfen:

   ```bash
   docker --version
   docker compose version
   ```

2. Repository auf den Pi klonen und öffnen:

   ```bash
   git clone <DEINE-REPOSITORY-URL> eBauteileFuchs
   cd eBauteileFuchs
   ```

3. Konfiguration anlegen und die feste LAN-Adresse eintragen. Eine DHCP-
   Reservierung im Router verhindert später ungültige Smartphone-QR-Codes:

   ```bash
   cp .env.example .env
   nano .env
   ```

   Beispiel: `EBAUTEILEFUCHS_PUBLIC_BASE_URL=http://192.168.1.42:8008`

4. Anwendung bauen und starten:

   ```bash
   docker compose up -d --build
   docker compose ps
   ```

5. Wenn `app` als `healthy` erscheint, im selben LAN mit dem Smartphone die
   Verbindungsseite öffnen und den dortigen QR-Code scannen. Startseite,
   Lagerplätze und einen vorhandenen QR-Code prüfen.

6. Unter **Daten** eine vollständige ZIP-Sicherung erstellen und zusätzlich
   auf ein getrenntes Speichermedium kopieren. Wiederherstellungen immer über
   den geführten Ablauf vornehmen; dieser erstellt zuvor eine Vorsicherung.

7. Aktualisieren:

   ```bash
   git pull
   docker compose up -d --build
   docker compose ps
   ```

`docker compose down` stoppt nur Container und Netzwerk. Das Datenvolume bleibt
erhalten. `docker compose down -v` löscht dagegen die Daten unwiderruflich und
ist nicht Teil des normalen Betriebs.

Für Firewall, externe Zugriffe und HTTPS gelten die Hinweise in
[Konfiguration](../configuration.md). Die Anwendung ist für ein
vertrauenswürdiges privates LAN gedacht; keine öffentliche Portfreigabe
einrichten.

Für eine native Installation ohne Docker folgt die identische
[Linux-/systemd-Anleitung](linux.md). Vor einem Update oder Restore immer eine
Sicherung unter **Daten** erstellen.
