# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektübersicht

**Serverraum-Überwachung** — IHK-Abschlussprojekt (Fachinformatiker Anwendungsentwicklung)
- Prüfling: Marc Haberald
- Auftraggeber: deCode GmbH / Herr Niklas
- Deadline: 16.03.2026 | Budget: 80 Stunden

Ein modulares Überwachungs- und Steuerungssystem für einen Serverraum mit:
- ESP32-S3-Mikrocontroller mit Sensoren → MQTT → Raspberry Pi (Backend) → Echtzeit-Dashboard

## Technischer Stack (VERBINDLICH)

| Schicht | Technologie |
|---------|-------------|
| Mikrocontroller | ESP32-S3 (Arduino-Framework, PlatformIO) |
| Sensoren | DHT/DS18B20 (Klima), MQ-2/MQ-135 (Gas), PIR (Bewegung) |
| Kommunikation | MQTT (Mosquitto-Broker), JSON-Payloads |
| Backend | Python 3.x (FastAPI oder Flask) auf Raspberry Pi |
| Datenbank | MariaDB |
| Frontend | Single-Page-Application (JavaScript ES6+, HTML, Tailwind CSS) |
| Alarmierung | E-Mail, Warn-LED, Dashboard-Benachrichtigung, Buzzer |

## Projektstruktur

```
serverraum-ueberwachung/
├── firmware/           # ESP32-S3 C++ Firmware (PlatformIO)
│   ├── platformio.ini
│   ├── src/main.cpp
│   ├── include/sensors/   # Sensor-Abstraktionsklassen (Polymorphie)
│   └── lib/
├── backend/            # Python-Backend
│   ├── app/
│   │   ├── main.py       # FastAPI/Flask Einstiegspunkt
│   │   ├── mqtt_client.py
│   │   ├── db.py
│   │   └── alarm_engine.py
│   └── requirements.txt
├── frontend/           # Dashboard SPA
│   ├── index.html
│   ├── js/
│   └── css/
├── docs/               # Projektdokumentation
├── sql/                # Datenbank-Schema
└── .github/
```

## Entwicklung

```bash
# Virtual Environment aktivieren
source .venv/bin/activate

# PlatformIO CLI (Firmware)
pio run --environment esp32-s3-devkitc-1

# Python Backend (Beispiel)
python -m backend.app.main

# Tests
pytest
```

## Architektur & Datenfluss

1. **Sensoren** (ESP32-S3) messen Temperatur, Luftfeuchtigkeit, Gas, Bewegung
2. **MQTT** publisht Readings an Mosquitto-Broker (Topic: `serverraum/sensor/#`)
3. **Backend** subscribed Topics, speichert in MariaDB, triggert Alarme
4. **Frontend** zeigt Echtzeit-Dashboard via WebSocket oder Polling

### Wichtige Module

- `alarm_engine.py`: Schwellwert-Prüfung → Alarmierung (E-Mail, LED, Buzzer)
- `mqtt_client.py`: MQTT-Subscriber mit JSON-Parsing
- `sensors/` (Firmware): Abstrakte Basisklasse `Sensor` → Polymorphie für DHT, DS18B20, MQ-*, PIR

## Code-Konventionen

- **C++**: PascalCase (Klassen), camelCase (Methoden/Variablen)
- **Python**: snake_case, Type Hints, Docstrings
- **JavaScript**: camelCase, ES6+ Modules, kein jQuery
- **SQL**: UPPER CASE Keywords, snake_case Tabellen/Spalten
- **Kommentare**: Deutsch (IHK-Prüfer liest mit)
- **Variablen/Funktionen**: IMMER selbsterklärende deutsche Namen
- **Commits**: Konventionelle Commits (`feat:`, `fix:`, `docs:`, `refactor:`)

## Regeln (ABSOLUT)

1. **Wasserfallmodell** — keine Phase überspringen
2. **MariaDB** — NICHT SQLite, PostgreSQL oder InfluxDB
3. **Tailwind CSS** — NICHT React/Vue/Angular
4. **MQTT via Mosquitto** — KEIN reines WebSocket oder HTTP-Polling
5. **OOP mit Polymorphie** in Firmware (IHK-Anforderung für Sensor-Abstraktion)
6. **Open-Source only** — keine Lizenzkosten
7. **Kein Qdrant, keine ML/AI-Features, keine Cloud-Dienste**

## Notion-Integration

| Ressource | Notion-ID |
|-----------|-----------|
| Projekt-Seite | `3172a8c3-23a2-8046-964d-ce42005fb4f3` |
| Aufgaben-Tracker DB | `3092a8c3-23a2-80c0-990f-e18bee90c536` |
| Zeitplanung | `3172a8c3-23a2-80bb-8e3d-e3c55aece027` |
| Tech-Specs | `3172a8c3-23a2-8008-8eb7-ee5dd5be5aef` |

Tasks als Blocks auf Projekt-Seite via `patch-block-children` anlegen.

## ESP32-S3 GPIO-Belegung (Tech-Specs)

**Gesperrte Pins (NICHT verwenden):**
- GPIO 26-32: Intern mit SPI-Flash & PSRAM verdrahtet → Crash
- GPIO 35, 36, 37: Beim ESP32-S3R8 intern gesperrt
- GPIO 0, 3, 45, 46: Strapping Pins (Boot-Modus)

**Empfohlene Zuordnung:**
| Sensor | Pin |
|--------|-----|
| DHT22 / DS18B20 (Temperatur/Feuchte) | GPIO 5 |
| MQ-2 (Rauchgas, analog) | ADC1 → GPIO 1 |
| MQ-135 (Luftqualität, analog) | ADC1 → GPIO 2 |
| PIR-Bewegungsmelder | GPIO 6 |
| Warn-LED | GPIO 7 |
| Buzzer | GPIO 8 |

**Spezifikationen:**
- Logikpegel: 3,3V
- ADC: 12-Bit (0-3,3V → 0-4095)
- UART0 (fest): TX=GPIO 43, RX=GPIO 44

## Projektphasen (80 Std.)

| Phase | Beschreibung | Stunden |
|-------|-------------|---------|
| I | Analyse und Definition | 8 |
| II | Planung und Entwurf | 12 |
| III | Implementierung (Firmware + Backend + Frontend) | 37 |
| IV | Qualitätssicherung und Test | 8 |
| V | Abschluss und Dokumentation | 15 |

**Phase III (Implementierung):**
- III.A: Firmware (ESP32-S3, OOP/Polymorphie, MQTT) — 11 Std.
- III.B: Backend (Python, MQTT, MariaDB, Alarm-Engine) — 14 Std.
- III.C: Frontend (SPA, Tailwind CSS, Echtzeit-Dashboard) — 12 Std.
