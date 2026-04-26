# MCP Server Fix - 03.03.2026

## Problem
GitHub und Notion MCP-Server befanden sich in einer Boot-Loop (Endlosschleife).

## Ursache
ESM/CommonJS-Konflikt in beiden MCP-Server-package.json:
- `package.json` hatte `"type": "commonjs"` 
- `tsconfig.json` hatte `"module": "ESNext"`

TypeScript kompilierte zu ESM (`import`-Statements), aber Node.js konnte die Datei nicht laden → `SyntaxError: Cannot use import statement outside a module` → Crash → Endlosschleife

## Lösung
In beiden `package.json` Dateien:
- `"type": "commonjs"` → `"type": "module"`

Betroffene Dateien:
- `/home/sonny/.local/share/Kilo-Code/MCP/github-server/package.json`
- `/home/sonny/.local/share/Kilo-Code/MCP/notion-server/package.json`

## Verifikation
Server starten jetzt erfolgreich:
- GitHub MCP: `GitHub MCP Server läuft auf stdio`
- Notion MCP: `Notion MCP Server läuft auf stdio`
