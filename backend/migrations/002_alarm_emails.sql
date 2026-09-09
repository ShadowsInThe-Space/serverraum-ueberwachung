-- =============================================================================
-- Migration: Alarm Emails Tabelle
-- Datum: 26.04.2026
-- Zweck: Emails die bei Alarmen gesendet wurden tracken
-- =============================================================================

CREATE TABLE IF NOT EXISTS alarm_emails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alarm_id INT NOT NULL,
    empfaenger VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body TEXT,
    sende_status ENUM('erfolgreich', 'fehlgeschlagen', 'ausstehend') DEFAULT 'ausstehend',
    error_message TEXT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alarm_id) REFERENCES alarme(id) ON DELETE CASCADE,
    INDEX idx_alarm_emails_alarm_id (alarm_id),
    INDEX idx_alarm_emails_empfaenger (empfaenger),
    INDEX idx_alarm_emails_sende_status (sende_status)
);

-- Tabelle für Email-Antworten (Reply-To Tracking)
-- Wenn ein Empfaänger auf eine Alarm-Email antwortet, wird das hier gespeichert
CREATE TABLE IF NOT EXISTS alarm_email_antworten (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alarm_email_id INT NOT NULL,
    empfaenger_email VARCHAR(255) NOT NULL,
    antwort_text TEXT,
    antwort_zeitpunkt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alarm_email_id) REFERENCES alarm_emails(id) ON DELETE CASCADE,
    INDEX idx_email_antworten_alarm_email_id (alarm_email_id)
);
