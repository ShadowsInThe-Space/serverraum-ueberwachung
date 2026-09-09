# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projekt-Übersicht

**Serverraum-Überwachung** — IHK-Abschlussprojekt für deCode GmbH
- ESP32-S3 Mikrocontroller mit Sensoren → MQTT (Mosquitto) → Raspberry Pi Backend → MariaDB → Echtzeit-Dashboard
- Technischer Stack: C++ (Firmware/PlatformIO), Python (FastAPI), MariaDB, Tailwind CSS (SPA)

## Architektur

```
┌─────────────┐     MQTT      ┌──────────────┐     ┌─────────┐     ┌──────────┐
│ ESP32-S3    │──────────────►│ Mosquitto    │────►│ FastAPI │────►│ MariaDB  │
│ Firmware    │               │ Broker       │     │ Backend │     │          │
└─────────────┘               └──────────────┘     └────┬────┘     └──────────┘
                                                        │
                                                        ▼
                                                  ┌──────────┐
                                                  │Dashboard │
                                                  │  (SPA)   │
                                                  └──────────┘
```

## Verzeichnisstruktur

| Verzeichnis | Beschreibung |
|-------------|--------------|
| `firmware/` | ESP32-S3 C++ Firmware (PlatformIO) — OOP-Sensorabstraktion mit Polymorphie |
| `backend/` | Python FastAPI Backend — MQTT-Client, AlarmEngine, MariaDB-Anbindung |
| `frontend/` | Single-Page-Application mit Tailwind CSS |
| `sql/` | MariaDB Schema (`schema.sql`) |
| `docs/` | Projektdokumentation (Pflichtenheft, Diagramme, Wireframes) |

## Sensortypen (Firmware)

Die Firmware implementiert OOP-Polymorphie für Sensoren:
- `Sensor` — Abstrakte Basisklasse
- `SHT31Sensor` — Temperatur & Feuchtigkeit (I2C)
- `DS18B20Sensor` — Temperatur (OneWire)
- `MQ2Sensor` — Rauchgas
- `MQ135Sensor` — Luftqualität
- `PIRSensor` — Bewegungserkennung

Jeder Sensor erbt von `Sensor` und implementiert `lesen()` für einheitliche Datenerfassung.

## Backend-Module (Python)

| Modul | Verantwortung |
|-------|--------------|
| `app/main.py` | FastAPI App, API-Endpoints, CORS |
| `app/mqtt_client.py` | MQTT-Subscriber mit Auto-Reconnect |
| `app/db.py` | MariaDB CRUD-Operationen |
| `app/alarm_engine.py` | Alarmprüfung (Schwellwerte), Benachrichtigungen |
| `app/config.py` | Konfigurationsmanagement (Pydantic) |

## Datenbank (MariaDB)

**Tabellen:** `sensoren`, `messungen`, `alarm_konfiguration`, `alarme`, `system_konfiguration`
**Views:** `v_letzte_messungen`, `v_aktive_alarme`

## Wichtige Regeln (aus AGENTS.md)

1. **Wasserfallmodell** — Keine Phase überspringen
2. **MariaDB verwenden** — Nicht SQLite, PostgreSQL oder InfluxDB
3. **MQTT via Mosquitto** — Kein WebSocket-Only oder HTTP-Polling
4. **OOP mit Polymorphie** in der Firmware (IHK-Anforderung)
5. **Code-Kommentare auf Deutsch** — IHK-Prüfer liest mit
6. **Konventionelle Commits** — feat:, fix:, docs:, refactor:

## Development Commands

### Backend starten
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Firmware kompilieren (PlatformIO)
```bash
cd firmware
pio run
```

### Firmware uploaden
```bash
pio run --target upload
```

### MQTT-Broker starten (Mosquitto)
```bash
mosquitto -c /Pfad/zu/mosquitto.conf
```

### Datenbank initialisieren
```bash
mysql -u root -p < sql/schema.sql
```

### Sensor-Simulation (Tests)
```bash
cd backend
python simulate_sensors.py
```

## API-Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `/status` | GET | Systemstatus (MQTT, DB, Alarme) |
| `/sensoren` | GET | Alle Sensoren mit letzten Messwerten |
| `/sensoren/{id}/messungen` | GET | Messungsverlauf |
| `/sensoren/{id}/statistik` | GET | Min/Max/Durchschnitt |
| `/alarme` | GET | Alarme (Filter: ?status=aktiv) |
| `/alarme/{id}/quittieren` | POST | Alarm bestätigen |
| `/konfiguration` | GET/PUT | Systemkonfiguration |
| `/alarm_konfiguration` | GET | Schwellwerte pro Sensor |

## Frontend

- **SPA** mit Fetch-API für Backend-Kommunikation
- **Tailwind CSS** für Styling
- **Echtzeit-Updates** via Polling (kein WebSocket)
- Statische Dateien werden von FastAPI unter `/static` bereitgestellt

## Dokumentation

- `docs/pflichtenheft.md` — Pflichtenheft (Anforderungen)
- `docs/09_Code_Snippets.md` — Code-Beispiele
- `docs/Systemarchitektur-Detailliert.drawio` — Systemarchitektur
- `docs/Klassendiagramm-*.drawio` — UML-Diagramme

## Testing

Backend-Tests befinden sich in `backend/tests/`. Tests für DB-Verbindung und API-Endpoints.
