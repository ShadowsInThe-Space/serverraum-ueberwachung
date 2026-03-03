# ER-Diagramm – Datenbankmodell

## Übersicht

Das ER-Diagramm zeigt die Struktur der MariaDB-Datenbank mit allen Tabellen und Beziehungen.

```mermaid
erDiagram
    SENSOREN ||--o{ MESSUNGEN : "hat"
    SENSOREN ||--|| ALARM_KONFIGURATION : "hat"
    SENSOREN ||--o{ ALARMS : "ausgeloest"
    SYSTEM_KONFIGURATION ||--o{ ALARMS : "nicht"

    SENSOREN {
        int id PK
        string sensor_typ
        string name
        string beschreibung
        int gpio_pin
        string einheit
        bool aktiv
        datetime created_at
        datetime updated_at
    }

    MESSUNGEN {
        int id PK
        int sensor_id FK
        decimal wert
        datetime timestamp
    }

    ALARM_KONFIGURATION {
        int id PK
        int sensor_id FK UK
        string alarm_typ
        decimal schwellwert_min
        decimal schwellwert_max
        bool alarmierung_email
        bool alarmierung_led
        bool alarmierung_buzzer
        bool alarmierung_dashboard
        datetime created_at
        datetime updated_at
    }

    ALARMS {
        int id PK
        int sensor_id FK
        string alarm_typ
        decimal messwert
        decimal schwellwert
        string nachricht
        string status
        datetime created_at
        datetime acknowledged_at
        datetime resolved_at
    }

    SYSTEM_KONFIGURATION {
        int id PK
        string konfiguration_schluessel UK
        string wert
        string beschreibung
        datetime created_at
        datetime updated_at
    }
```

## Tabellenerklärung

### sensoren
Enthält Informationen über alle verbundenen Sensoren:
- `sensor_typ`: Art des Sensors (dht22, mq2, mq135, pir)
- `gpio_pin`: GPIO-Pin am ESP32
- `einheit`: Maßeinheit (°C, %, ppm)

### messungen
Speichert alle Messwerte:
- `sensor_id`: Verweis auf den Sensor
- `wert`: Messwert
- `timestamp`: Zeitpunkt der Messung

### alarm_konfiguration
Definiert Schwellwerte und Alarmierungseinstellungen:
- `sensor_id`: Verweis auf den Sensor
- `schwellwert_min/max`: Grenzwerte für Alarmauslösung
- `alarmierung_*`: Konfiguration der Alarmierungswege

### alarms
Speichert ausgelöste Alarme:
- `sensor_id`: Verweis auf den Sensor
- `status`: Alarmstatus (aktiv, acknowledged, resolved)
- `messwert`: Auslösender Messwert
- `schwellwert`: Überschrittener Grenzwert

### system_konfiguration
Globale Systemeinstellungen:
- `konfiguration_schluessel`: Einstellungsschlüssel
- `wert`: Einstellungswert

## Beziehungen

| Beziehung | Typ | Beschreibung |
|-----------|-----|--------------|
| sensoren → messungen | 1:n | Ein Sensor hat viele Messungen |
| sensoren → alarm_konfiguration | 1:1 | Ein Sensor hat genau eine Alarmkonfiguration |
| sensoren → alarms | 1:n | Ein Sensor kann viele Alarme auslösen |

## Normalisierung

Das Datenbank-Schema ist in **3. Normalform (3NF)**:
- Jede Tabelle hat einen Primärschlüssel
- Keine transitiven Abhängigkeiten
- Atomare Attributwerte
- Saubere Trennung von Entitäten
