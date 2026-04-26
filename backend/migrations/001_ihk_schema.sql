-- =============================================================================
-- Migration: IHK Pflichtenheft Schema
-- Datum: 19.04.2026
-- Zweck: DB-Schema an IHK-Dokumentation anpassen
-- =============================================================================

-- Sensoren: gpio_pin und beschreibung hinzufügen
ALTER TABLE sensoren
    ADD COLUMN gpio_pin INT DEFAULT NULL,
    ADD COLUMN beschreibung VARCHAR(255) DEFAULT NULL;

-- Messungen: einheit hinzufügen
ALTER TABLE messungen
    ADD COLUMN einheit VARCHAR(20) DEFAULT NULL;

-- =============================================================================
-- Alarm-Konfiguration (laut Pflichtenheft)
-- =============================================================================
CREATE TABLE IF NOT EXISTS alarm_konfiguration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT NOT NULL,
    alarm_typ VARCHAR(50) NOT NULL,
    schwellwert_min FLOAT DEFAULT NULL,
    schwellwert_max FLOAT DEFAULT NULL,
    alarmierung_email BOOLEAN DEFAULT FALSE,
    alarmierung_led BOOLEAN DEFAULT FALSE,
    alarmierung_buzzer BOOLEAN DEFAULT FALSE,
    alarmierung_dashboard BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensoren(id) ON DELETE CASCADE,
    UNIQUE KEY unique_sensor_alarm (sensor_id, alarm_typ)
);

-- =============================================================================
-- System-Konfiguration (laut Pflichtenheft)
-- =============================================================================
CREATE TABLE IF NOT EXISTS system_konfiguration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    konfiguration_schluessel VARCHAR(100) NOT NULL UNIQUE,
    wert TEXT NOT NULL,
    beschreibung VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =============================================================================
-- Index für Performance
-- =============================================================================
CREATE INDEX idx_messungen_sensor_id ON messungen(sensor_id);
CREATE INDEX idx_messungen_timestamp ON messungen(timestamp);
CREATE INDEX idx_alarme_status ON alarme(status);
CREATE INDEX idx_alarme_sensor_id ON alarme(sensor_id);

-- =============================================================================
-- Verifikation
-- =============================================================================
-- SELECT * FROM information_schema.COLUMNS
--   WHERE TABLE_SCHEMA = 'serverraum_ueberwachung'
--   AND TABLE_NAME IN ('sensoren', 'messungen', 'alarme',
--                      'alarm_konfiguration', 'system_konfiguration');
