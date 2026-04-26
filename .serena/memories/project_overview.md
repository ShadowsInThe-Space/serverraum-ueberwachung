# Projekt-Übersicht: Serverraum-Überwachung

## Zweck
Modulares Überwachungs- und Steuerungssystem für einen Serverraum (IHK-Abschlussprojekt).
Schutz der IT-Infrastruktur eines Gaming Developer Bootcamps.

## Tech Stack
- **Mikrocontroller:** ESP32-S3 (Arduino/PlatformIO)
- **Kommunikation:** MQTT (Mosquitto)
- **Backend:** Python (FastAPI oder Flask)
- **Datenbank:** MariaDB
- **Frontend:** SPA (HTML, JavaScript ES6+, Tailwind CSS)
- **Alarmierung:** E-Mail, LED, Buzzer, Dashboard

## Struktur
- `firmware/`: ESP32-S3 Source
- `backend/`: Python API & MQTT Subscriber
- `frontend/`: Dashboard Webapp
- `docs/`: Dokumentation (Markdown, Diagramme)
- `sql/`: Datenbank-Schema
- `AGENTS.md`: Zentrale Projektregeln und Notion-IDs