---
name: block-db-container-delete
enabled: true
event: bash
pattern: docker\s+rm.*postgres|docker\s+rm.*mysql|docker\s+rm.*mariadb|docker\s+rm.*redis|docker\s+rm.*mongodb
action: block
---

🛑 **Datenbank-Container Löschen blockiert!**

Du hast angefordert, dass Datenbank-Container NIEMALS ohne Bestätigung gelöscht werden.

Warte auf Bestätigung mit dem Wort "Lösche" bevor du fortfährst!
