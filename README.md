# Serverraum-Überwachung

Modulares Monitoring-System für Serverräume, entwickelt als IHK-Abschlussprojekt zum Fachinformatiker für Anwendungsentwicklung (2026). Die **Projektdokumentation** wurde mit **91/100 Punkten (sehr gut)** bewertet.

Das Projekt verbindet die Erfassung von Sensordaten mit MQTT-Kommunikation, einem Python-Backend, relationaler Datenhaltung und einem Browser-Dashboard.

## Architektur

| Schicht | Umsetzung im Repository |
| --- | --- |
| Sensorik | ESP32-S3, Arduino/PlatformIO und C++-Sensorklassen |
| Kommunikation | MQTT-Nachrichten zwischen Sensoren und Backend |
| Backend | FastAPI mit Uvicorn, Paho-MQTT |
| Datenhaltung | MariaDB-Schema, MySQL-Connector und SQL-Migrationen |
| Oberfläche | HTML, JavaScript, Tailwind CSS und Chart.js |
| Alarmierung | Alarm-Engine, Quittierung und E-Mail-Schnittstellen |

## Für den Code-Review

1. [Systemarchitektur](docs/Systemarchitektur-Detailliert.drawio) und [ER-Diagramm](ER-Diagramm.drawio.png) erklären den Aufbau.
2. [Sensor-Abstraktion](firmware/include/sensors/Sensor.h) und [SensorManager](firmware/include/sensors/SensorManager.h) zeigen die Firmware-Modellierung.
3. [MQTT-Client](backend/app/mqtt_client.py), [Datenbankzugriff](backend/app/db.py) und [Alarm-Engine](backend/app/alarm_engine.py) bilden die Verarbeitung.
4. [FastAPI-Anwendung](backend/app/main.py) stellt die HTTP-Schnittstellen bereit.
5. [Dashboard](frontend/index.html) und [Frontend-Module](frontend/js) setzen die Darstellung um.
6. [Backend-Tests](backend/tests) dokumentieren prüfbares Verhalten.

## Lokal vorbereiten

Voraussetzungen: Python 3, MariaDB und ein MQTT-Broker. Für die Firmware zusätzlich PlatformIO und passende ESP32-Hardware.

```bash
git clone https://github.com/Shadows-In-The-Space/serverraum-ueberwachung.git
cd serverraum-ueberwachung/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install pydantic-settings
```

`app/config.py` importiert `pydantic-settings`; diese Abhängigkeit fehlt derzeit in `requirements.txt` und wird deshalb oben ausdrücklich installiert. Datenbank-, Broker- und E-Mail-Konfiguration anhand von [config.py](backend/app/config.py), [Installationsanleitung](docs/Anhang_Installationsanleitung.md) und [Konfigurationsbeispiel](docs/Anhang_Konfiguration_Beispiel.md) lokal einrichten.

Bei vorbereiteten Diensten wird das Backend aus dem Verzeichnis `backend/` gestartet:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Die API-Dokumentation ist dann unter http://127.0.0.1:8000/docs erreichbar. Firmware-Build und Upload sind in [platformio.ini](firmware/platformio.ini) und der Installationsanleitung beschrieben.

## Qualität und Projektgrenzen

Die Architekturartefakte umfassen ER-, UML-, MVC- und Sequenzdiagramme sowie Wireframes. Das Repository enthält Implementierung, Tests und begleitende Projektdokumentation. Historische Entwürfe und Demo-Code liegen unter `docs/Archiv`.

Die Portfolio-Überarbeitung hat README, Struktur und zentrale Quelldateien abgeglichen. Sie enthält keinen neu ausgeführten Hardware-, Integrations- oder vollständigen Backend-Test. Die Anwendung ist für ein kontrolliertes Projektumfeld zu betrachten; die vorhandenen Administrations- und Konfigurationsendpunkte sind kein Nachweis einer für das öffentliche Internet geprüften Zugriffsabsicherung.

Das System ist keine zertifizierte Brandmeldeanlage.
