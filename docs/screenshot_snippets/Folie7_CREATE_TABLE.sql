-- Tabelle: sensoren - speichert alle Sensoren
CREATE TABLE IF NOT EXISTS sensoren (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_typ VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    beschreibung VARCHAR(255),
    gpio_pin INT,
    einheit VARCHAR(20),
    aktiv BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
