# Empfohlene Befehle

## Git & Worktrees
- `git status` - Status prüfen.
- `git worktree add -b <branch> <path>` - Neuen Worktree für Features erstellen.
- `git commit -m "<type>: <description>"` - Änderungen committen.

## Firmware (PlatformIO)
- `pio run` - Build.
- `pio run -t upload` - Flash auf ESP32.
- `pio device monitor` - Serieller Monitor.

## Backend (Python)
- `uvicorn app.main:app --reload` - FastAPI starten (falls genutzt).
- `pip install -r requirements.txt` - Abhängigkeiten installieren.

## Frontend
- `npx tailwindcss -i ./src/input.css -o ./dist/output.css --watch` - Tailwind Build.
- `python3 -m http.server` - Einfacher lokaler Test-Server.