-- =====================================================
-- Serverraum-Überwachung Datenbank-Schema
-- MariaDB
-- Version: 1.0
-- Datum: 03.03.2026
-- =====================================================

-- Datenbank erstellen (falls nicht vorhanden)
CREATE DATABASE IF NOT EXISTS serverraum_ueberwachung
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE serverraum_ueberwachung;

-- =====================================================
-- Tabelle: sensoren
-- Speichert Informationen über alle verbundenen Sensoren
-- =====================================================
CREATE TABLE IF NOT EXISTS sensoren (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_typ VARCHAR(50) NOT NULL COMMENT 'Sensortyp: dht22, ds18b20, mq2, mq135, pir',
    name VARCHAR(100) NOT NULL COMMENT 'Anzeigename des Sensors',
    beschreibung VARCHAR(255) COMMENT 'Optionale Beschreibung',
    gpio_pin INT COMMENT 'GPIO-Pin am ESP32',
    einheit VARCHAR(20) COMMENT 'Einheit des Messwerts: °C, %, ppm',
    aktiv BOOLEAN DEFAULT TRUE COMMENT 'Sensor aktiv/inaktiv',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sensor_typ (sensor_typ),
    INDEX idx_aktiv (aktiv)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Tabelle: messungen
-- Speichert alle Sensordaten-Messungen
-- =====================================================
CREATE TABLE IF NOT EXISTS messungen (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT NOT NULL COMMENT 'Fremdschlüssel zu sensoren',
    wert DECIMAL(10,2) NOT NULL COMMENT 'Messwert',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensoren(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_sensor_id (sensor_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Tabelle: alarm_konfiguration
-- Speichert Schwellwerte und Alarmierungseinstellungen pro Sensor
-- =====================================================
CREATE TABLE IF NOT EXISTS alarm_konfiguration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT NOT NULL UNIQUE COMMENT 'Fremdschlüssel zu sensoren (eindeutig)',
    alarm_typ VARCHAR(50) NOT NULL COMMENT 'Alarmtyp: temperatur, luftfeuchtigkeit, gas, bewegung',
    schwellwert_min DECIMAL(10,2) COMMENT 'Unterer Schwellwert',
    schwellwert_max DECIMAL(10,2) COMMENT 'Oberer Schwellwert',
    alarmierung_email BOOLEAN DEFAULT FALSE COMMENT 'E-Mail-Alarmierung aktiv',
    alarmierung_led BOOLEAN DEFAULT FALSE COMMENT 'LED-Alarmierung aktiv',
    alarmierung_buzzer BOOLEAN DEFAULT FALSE COMMENT 'Buzzer-Alarmierung aktiv',
    alarmierung_dashboard BOOLEAN DEFAULT TRUE COMMENT 'Dashboard-Alarmierung aktiv',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensoren(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_sensor_id (sensor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Tabelle: alarme
-- Speichert ausgelöste Alarme (ACHTUNG: "alarme" nicht "alarms"!)
-- =====================================================
CREATE TABLE IF NOT EXISTS alarme (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT NOT NULL COMMENT 'Fremdschlüssel zu sensoren',
    alarm_typ VARCHAR(50) NOT NULL COMMENT 'Alarmtyp',
    wert DECIMAL(10,2) NOT NULL COMMENT 'Auslösender Messwert',
    schwellwert DECIMAL(10,2) COMMENT 'Überschrittener Schwellwert',
    nachricht VARCHAR(255) COMMENT 'Optionale Alarmnachricht',
    status VARCHAR(20) DEFAULT 'aktiv' COMMENT 'Status: aktiv, quittiert, geloest',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    quittiert_at DATETIME NULL COMMENT 'Zeitpunkt der Quittierung',
    INDEX idx_sensor_id (sensor_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Tabelle: system_konfiguration
-- Speichert globale Systemeinstellungen
-- =====================================================
CREATE TABLE IF NOT EXISTS system_konfiguration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    konfiguration_schluessel VARCHAR(100) NOT NULL UNIQUE COMMENT 'Konfigurationsschlüssel',
    wert TEXT COMMENT 'Konfigurationswert',
    beschreibung VARCHAR(255) COMMENT 'Beschreibung der Einstellung',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_schluessel (konfiguration_schluessel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Initiale Konfigurationsdaten
-- =====================================================

-- MQTT-Konfiguration
INSERT INTO system_konfiguration (konfiguration_schluessel, wert, beschreibung) VALUES
    ('mqtt_broker_host', 'localhost', 'MQTT-Broker Hostname'),
    ('mqtt_broker_port', '1883', 'MQTT-Broker Port'),
    ('mqtt_topic_prefix', 'serverraum/sensor', 'MQTT-Topic-Präfix'),
    ('email_smtp_host', '', 'SMTP-Server Hostname'),
    ('email_smtp_port', '587', 'SMTP-Server Port'),
    ('email_absender', '', 'E-Mail-Absenderadresse'),
    ('email_empaenger', '', 'E-Mail-Empfänger (kommasepariert)'),
    ('esp32_device_id', 'esp32-001', 'ESP32 Geräte-ID')
ON DUPLICATE KEY UPDATE wert = VALUES(wert);

-- =====================================================
-- Initiale Sensoren
-- =====================================================
INSERT INTO sensoren (sensor_typ, name, beschreibung, gpio_pin, einheit) VALUES
    ('dht22', 'Temperatur & Feuchte', 'DHT22 Sensor für Temperatur und Luftfeuchtigkeit', 5, '°C/%'),
    ('mq2', 'Rauchgas', 'MQ-2 Rauchgassensor', 1, 'ppm'),
    ('mq135', 'Luftqualität', 'MQ-135 Luftqualitätssensor', 2, 'ppm'),
    ('pir', 'Bewegung', 'PIR-Bewegungsmelder', 6, 'bool')
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- =====================================================
-- Initiale Alarm-Konfiguration
-- =====================================================
INSERT INTO alarm_konfiguration (sensor_id, alarm_typ, schwellwert_min, schwellwert_max,
    alarmierung_email, alarmierung_led, alarmierung_buzzer, alarmierung_dashboard)
SELECT
    id,
    CASE
        WHEN sensor_typ = 'dht22' THEN 'temperatur'
        WHEN sensor_typ = 'mq2' THEN 'gas'
        WHEN sensor_typ = 'mq135' THEN 'luftqualitaet'
        WHEN sensor_typ = 'pir' THEN 'bewegung'
    END,
    CASE
        WHEN sensor_typ = 'dht22' THEN 15.00
        ELSE NULL
    END,
    CASE
        WHEN sensor_typ = 'dht22' THEN 30.00
        WHEN sensor_typ = 'mq2' THEN 200.00
        WHEN sensor_typ = 'mq135' THEN 100.00
        ELSE NULL
    END,
    TRUE, TRUE, FALSE, TRUE
FROM sensoren
WHERE sensor_typ IN ('dht22', 'mq2', 'mq135', 'pir')
ON DUPLICATE KEY UPDATE alarm_typ = VALUES(alarm_typ);

-- =====================================================
-- Views für einfache Abfragen
-- =====================================================

-- Letzte Messung pro Sensor
CREATE OR REPLACE VIEW v_letzte_messungen AS
SELECT
    s.id AS sensor_id,
    s.sensor_typ,
    s.name,
    s.einheit,
    m.wert,
    m.timestamp AS messzeitpunkt
FROM sensoren s
LEFT JOIN (
    SELECT sensor_id, wert, timestamp,
           ROW_NUMBER() OVER (PARTITION BY sensor_id ORDER BY timestamp DESC) AS rn
    FROM messungen
) m ON s.id = m.sensor_id AND m.rn = 1
WHERE s.aktiv = TRUE;

-- Aktive Alarme
CREATE OR REPLACE VIEW v_aktive_alarme AS
SELECT
    a.id,
    a.sensor_id,
    s.name AS sensor_name,
    a.alarm_typ,
    a.wert AS messwert,
    a.schwellwert,
    a.nachricht,
    a.status,
    a.created_at
FROM alarme a
JOIN sensoren s ON a.sensor_id = s.id
WHERE a.status = 'aktiv'
ORDER BY a.created_at DESC;

-- =====================================================
-- End of Schema
-- =====================================================
