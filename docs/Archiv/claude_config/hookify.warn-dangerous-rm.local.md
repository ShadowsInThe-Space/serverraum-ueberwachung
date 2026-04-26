---
name: warn-dangerous-rm
enabled: true
event: bash
pattern: rm\s+-rf|rm\s+-r\s+-f
action: warn
---

⚠️ **Gefährlicher rm -rf Befehl erkannt!**

Du hast angefordert vor rm -rf Befehlen gewarnt zu werden.
Bitte überprüfe ob der Pfad korrekt ist!
