# Sicherheitsrichtlinie

## Meldung einer Schwachstelle

Bitte veröffentliche mögliche Sicherheitslücken nicht als öffentliches Issue.
Nutze stattdessen die private GitHub-Funktion **Report a vulnerability** im
offiziellen Repository. Vor der ersten öffentlichen Veröffentlichung muss der
Projektinhaber diesen privaten Meldeweg in den Repository-Einstellungen
aktivieren und testen.

Bitte beschreibe reproduzierbare Schritte, betroffene Versionen und mögliche
Auswirkungen. Keine echten API-Schlüssel, Sicherungen oder Lagerdaten mitsenden.

## Sicherheitsgrenzen

eBauteileFuchs ist für ein vertrauenswürdiges lokales Netzwerk bestimmt. Es
besitzt in Version 0.1 keine Benutzerkonten oder Rollen und darf nicht ohne
zusätzliche Schutzmaßnahmen öffentlich ins Internet freigegeben werden.

Geheimnisse werden nur aus der lokalen Umgebung oder `.env` gelesen. Sie dürfen
nicht in Issues, Logs, Screenshots, Datenbanken, Backups oder Commits gelangen.
Browser-Schreibvorgänge verwenden CSRF- und Origin-Schutz; der optionale
Mouser-Schlüssel wird nicht angezeigt oder protokolliert.
