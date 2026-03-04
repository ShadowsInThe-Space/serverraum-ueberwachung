# AGENTS.md – Projektweite Anweisungen

## Projekt

**IHK-Abschlussprojekt: Serverraum-Überwachung**
Fachinformatiker Anwendungsentwicklung | IHK Essen, Mülheim an der Ruhr, Oberhausen
Prüfling: Marc Haberland | Auftraggeber: deCode GmbH / Herr Niklas
Vorgehensmodell: Erweitertes Wasserfallmodell | Budget: 80 Stunden | Deadline: 16.03.2026

---

## Beschreibung

Konzeption und Entwicklung eines modularen Überwachungs- und Steuerungssystems für einen Serverraum.
ESP32-S3-Mikrocontroller mit Sensoren → MQTT → Raspberry Pi (Backend) → Echtzeit-Dashboard.
Absicherung der IT-Infrastruktur eines Gaming Developer Bootcamps in einem Altbau.

---

## Technischer Stack (VERBINDLICH — nicht ändern!)

| Schicht | Technologie | Sprache |
|---|---|---|
| Mikrocontroller | ESP32-S3 (Arduino-Framework, PlatformIO) | C++ (OOP, Polymorphie) |
| Sensoren | Klima (DHT/DS18B20), Gas (MQ-2/MQ-135), PIR-Bewegungsmelder | — |
| Kommunikation | MQTT (Mosquitto-Broker) | JSON-Payloads |
| Zentraleinheit | Raspberry Pi | — |
| Backend | FastAPI oder Flask | Python 3.x |
| Datenbank | MariaDB (normalisiertes ER-Modell) | SQL |
| Frontend | Single-Page-Application | JavaScript ES6+, HTML, Tailwind CSS |
| Alarmierung | E-Mail, Warn-LED, Dashboard-Benachrichtigung, Buzzer | — |
| IDE | VS Code unter Linux (KDE Neon) + PlatformIO | — |

---

## Projektphasen (80 Std.)

| # | Phase | Stunden |
|---|---|---|
| I | Analyse und Definition | 8 |
| II | Planung und Entwurf | 12 |
| III | Implementierung (Firmware + Backend + Frontend) | 37 |
| IV | Qualitätssicherung und Test | 8 |
| V | Abschluss und Dokumentation | 15 |

---

## Projektstruktur (geplant)

```
serverraum-ueberwachung/
├── firmware/                 # ESP32-S3 C++ Firmware (PlatformIO)
│   ├── platformio.ini
│   ├── src/
│   │   └── main.cpp
│   ├── include/
│   │   └── sensors/          # Sensor-Abstraktionsklassen (Polymorphie)
│   └── lib/
├── backend/                  # Python-Backend für Raspberry Pi
│   ├── app/
│   │   ├── main.py           # FastAPI/Flask Einstiegspunkt
│   │   ├── mqtt_client.py    # MQTT-Subscriber
│   │   ├── db.py             # MariaDB-Anbindung
│   │   └── alarm_engine.py   # Alarmierungslogik
│   └── requirements.txt
├── frontend/                 # Dashboard SPA
│   ├── index.html
│   ├── js/
│   └── css/
├── docs/                     # Projektdokumentation
│   ├── lastenheft.md
│   ├── pflichtenheft.md
│   ├── er-diagramm.png
│   ├── uml-klassendiagramm.png
│   ├── sequenzdiagramm-mqtt.png
│   └── wireframes/
├── sql/                      # Datenbank-Schema
│   └── schema.sql
├── .github/agents/           # Custom Copilot Agents
│   └── Teacher.agent.md
├── AGENTS.md                 # Diese Datei
├── README.md
└── .gitignore
```

---

## Notion-Integration

| Ressource | Notion-ID |
|---|---|
| Projekt-Seite (IHK-Abschluss) | `3172a8c3-23a2-8046-964d-ce42005fb4f3` |
| Aufgaben-Tracker DB | `3092a8c3-23a2-80c0-990f-e18bee90c536` |
| Projekte DB | `3172a8c3-23a2-80c3-bf5e-c45fda1ef2c9` |
| Bugs DB | `3162a8c3-23a2-8033-b9c3-f32ccfb87ee8` |

Notion-Tasks werden als Blocks auf der Projekt-Seite via `patch-block-children` angelegt (nicht `post-page`, da Serialisierungs-Bug mit `parent`-Objekten).

---

## Regeln (ABSOLUT)

1. **Nichts implementieren** was nicht im genehmigten IHK-Projektantrag steht
2. **Nichts weglassen** was im Projektantrag steht
3. **Wasserfallmodell einhalten** — keine Phase überspringen
4. **Kein Qdrant**, keine KI/ML-Features, keine Cloud-Dienste
5. **Open-Source only** — keine Lizenzkosten
6. **MariaDB** verwenden, nicht SQLite, PostgreSQL oder InfluxDB
7. **Tailwind CSS** für Frontend, kein React/Vue/Angular
8. **MQTT via Mosquitto**, kein WebSocket-Only oder HTTP-Polling
9. Code muss **kommentiert** sein — IHK-Prüfer liest mit
10. Firmware nutzt **OOP mit Polymorphie** zur Sensor-Abstraktion (IHK-Anforderung)

---

## Projektabgrenzung

**NICHT Teil des Projekts:**
- Bauliche Maßnahmen oder Kabelverlegung
- Zertifizierung als Brandmeldeanlage (VdS)
- Hardware-Beschaffung (stellt der Auftraggeber)

---

## Code-Konventionen

- **C++ (Firmware):** PascalCase für Klassen, camelCase für Methoden/Variablen
- **Python (Backend):** snake_case, Type Hints, Docstrings
- **JavaScript (Frontend):** camelCase, ES6+ Modules, kein jQuery
- **SQL:** UPPER CASE Keywords, snake_case für Tabellen/Spalten
- **Commits:** Konventionelle Commits (feat:, fix:, docs:, refactor:)
- **Sprache:** Code-Kommentare auf Deutsch (IHK-Doku), IMMER selbsterklärende Variablen und Funktionsnamen auf Deutsch
