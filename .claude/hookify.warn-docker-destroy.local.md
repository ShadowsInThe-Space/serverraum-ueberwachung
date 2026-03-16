---
name: warn-docker-destroy
enabled: true
event: bash
pattern: docker\s+system\s+prune|docker\s+volume\s+rm|docker\s+network\s+rm
action: warn
---

⚠️ **Destruktiver Docker Befehl!**

Dieser Befehl kann Daten dauerhaft löschen.
Gehe sicher, dass du weißt was du tust!
