---
name: warn-chmod-777
enabled: true
event: bash
pattern: chmod\s+777
action: warn
---

⚠️ **chmod 777 erkannt!**

Dies ist ein Sicherheitsrisiko - 777 gibt allen Benutzern volle Rechte.
Verwende stattdessen restriktivere Berechtigungen!
