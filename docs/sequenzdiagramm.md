# Sequenzdiagramm – MQTT-Datenfluss

## Übersicht

Das Sequenzdiagramm zeigt den kompletten Datenfluss vom Sensor bis zum Dashboard.

## Vollständiger Datenfluss

```mermaid
sequenceDiagram
    participant ESP32 as ESP32-S3 (Firmware)
    participant MQTT as Mosquitto Broker
    participant Backend as Python Backend
    participant DB as MariaDB
    participant Frontend as SPA Dashboard

    Note over ESP32: Initialisierung
    ESP32->>ESP32: Sensor.init()
    ESP32->>MQTT: Connect to broker

    loop Alle 30 Sekunden
        Note over ESP32: Messzyklus
        ESP32->>ESP32: Sensor.read()
        ESP32->>ESP32: Create JSON payload

        ESP32->>MQTT: Publish to topic
        MQTT->>Backend: Forward message

        Backend->>Backend: Validate JSON
        Backend->>Backend: Check thresholds

        alt Schwellwert überschritten
            Backend->>Backend: Trigger alarm
            Backend->>DB: Save alarm to database
            Backend->>Backend: Send email
            Backend->>Backend: Trigger LED/Buzzer
        end

        Backend->>DB: Insert measurement

        Note over Backend: WebSocket or Polling
        Frontend->>Backend: Request latest data
        Backend->>DB: Query latest measurements
        DB-->>Backend: Return results
        Backend-->>Frontend: JSON response

        Frontend->>Frontend: Update UI
    end
```

## Alarmierungs-Flow

```mermaid
sequenceDiagram
    participant ESP32 as ESP32-S3
    participant MQTT as Mosquitto
    participant Backend as Python Backend
    participant DB as MariaDB
    participant Email as SMTP Server
    participant LED as Warn-LED
    participant Buzzer as Buzzer

    ESP32->>MQTT: serverraum/sensor/temperatur: {wert: 35.5}
    MQTT->>Backend: Forward message
    Backend->>Backend: Parse JSON
    Backend->>DB: Get threshold config
    DB-->>Backend: threshold_max: 30.0

    alt Wert > Schwellwert
        Backend->>DB: Insert alarm (status=aktiv)
        Backend->>Email: Send SMTP email
        Backend->>LED: GPIO pin HIGH
        Backend->>Buzzer: GPIO pin HIGH (optional)
        Backend->>Frontend: WebSocket: alarm_triggered
        Frontend->>Frontend: Show alarm notification
    end
```

## API-Kommunikation

```mermaid
sequenceDiagram
    participant User as Benutzer
    participant Frontend as SPA Dashboard
    participant Backend as Python Backend
    participant DB as MariaDB

    User->>Frontend: Öffnet Dashboard
    Frontend->>Backend: GET /api/sensoren
    Backend->>DB: SELECT * FROM sensoren
    DB-->>Backend: Sensor list
    Backend-->>Frontend: JSON: [{id: 1, name: "Temperatur", ...}]

    Frontend->>Backend: GET /api/messungen?sensor_id=1&limit=100
    Backend->>DB: SELECT * FROM messungen WHERE sensor_id=1 ORDER BY timestamp DESC LIMIT 100
    DB-->>Backend: Measurement list
    Backend-->>Frontend: JSON: [{wert: 22.5, timestamp: "..."}, ...]

    Frontend->>Backend: GET /api/alarms?status=aktiv
    Backend->>DB: SELECT * FROM alarms WHERE status='aktiv'
    DB-->>Backend: Active alarms
    Backend-->>Frontend: JSON: [{id: 1, typ: "temperatur", ...}]

    User->>Frontend: Klickt "Quittieren"
    Frontend->>Backend: POST /api/alarms/1/acknowledge
    Backend->>DB: UPDATE alarms SET status='acknowledged', acknowledged_at=NOW()
    DB-->>Backend: Updated
    Backend-->>Frontend: JSON: {success: true}
```

## Datenbank-Operationen

```mermaid
sequenceDiagram
    participant Backend
    participant DB as MariaDB

    Note over Backend: Messung speichern
    Backend->>DB: INSERT INTO messungen (sensor_id, wert) VALUES (1, 22.5)
    DB-->>Backend: Last insert ID

    Note over Backend: Alarm abrufen
    Backend->>DB: SELECT * FROM alarm_konfiguration WHERE sensor_id=1
    DB-->>Backend: Threshold config

    Note over Backend: Alarm speichern
    Backend->>DB: INSERT INTO alarms (sensor_id, alarm_typ, messwert, schwellwert, status)
    DB-->>Backend: Alarm ID

    Note over Backend: Konfiguration abrufen
    Backend->>DB: SELECT * FROM system_konfiguration
    DB-->>Backend: Config key-value pairs
```
