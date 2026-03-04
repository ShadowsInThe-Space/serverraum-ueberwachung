"""
Serverraum-Überwachung Backend
=============================

Python Backend für ESP32-S3 basiertes Serverraum-Überwachungssystem.

Module:
- config: Konfiguration
- db: MariaDB Datenbank-Verbindung
- mqtt_client: MQTT-Subscriber
- alarm_engine: Alarmierung (E-Mail, LED, Buzzer)
- main: FastAPI REST-API

@author Marc-Dennis Haberland
@date 04.03.2026
Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
"""

__version__ = "1.0.0"
