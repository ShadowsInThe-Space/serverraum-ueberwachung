# Installationsanleitung – Serverraum-Überwachung

## Übersicht

Diese Anleitung beschreibt die vollständige Installation des Serverraum-Überwachungssystems.

---

## Systemanforderungen

### Hardware

| Komponente | Anforderung |
|------------|-------------|
| Raspberry Pi | Modell 4B oder besser, 4GB RAM |
| Speicherkarte | 16GB+ microSD (Class 10) |
| ESP32 | ESP32-S3 DevKit oder kompatibel |
| Sensoren | DS18B20, SHT31, MQ-2, PIR HC-SR501 |
| Netzwerk | 100MBit/s Ethernet oder WiFi 2.4GHz |

### Software

| Komponente | Version |
|------------|---------|
| Raspberry Pi OS | Debian 12 (Bookworm) |
| Python | 3.11+ |
| MariaDB | 10.11+ |
| Mosquitto | 2.0+ |
| Docker | 24.0+ (optional) |
| Node.js | 18+ (optional, für Frontend-Build) |

---

## Installation Schritt für Schritt

### Phase 1: Raspberry Pi vorbereiten

**1.1 Raspberry Pi OS installieren**

```bash
# Raspberry Pi Imager herunterladen und starten
# OS: Raspberry Pi OS (64-bit) Lite (kein Desktop)
# Storage: SD-Karte auswählen
# Settings konfigurieren:
#   - Hostname: serverraum
#   - SSH enabled
#   - Username: pi / Password: (sicheres Passwort)
#   - WiFi konfigurieren (falls kein Ethernet)
```

**1.2 Grundlegende Pakete installieren**

```bash
# SSH-Verbindung herstellen
ssh pi@serverraum.local

# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Basispakete installieren
sudo apt install -y \
    git \
    curl \
    wget \
    vim \
    htop \
    net-tools \
    python3-pip \
    python3-venv \
    ufw
```

### Phase 2: Datenbank (MariaDB)

**2.1 MariaDB installieren**

```bash
sudo apt install -y mariadb-server mariadb-client

# MariaDB starten und aktivieren
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Sicherheitskonfiguration
sudo mysql_secure_installation
```

**2.2 Datenbank und Benutzer erstellen**

```bash
sudo mysql -u root -p
```

```sql
-- Datenbank erstellen
CREATE DATABASE serverraum CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Benutzer erstellen
CREATE USER 'serverraum'@'localhost' IDENTIFIED BY 'DEIN_SICHERES_PASSWORT';

-- Rechte vergeben
GRANT ALL PRIVILEGES ON serverraum.* TO 'serverraum'@'localhost';
FLUSH PRIVILEGES;

-- Datenbank wechseln
USE serverraum;

-- Tabellen erstellen
CREATE TABLE sensors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    typ VARCHAR(50) NOT NULL,
    einheit VARCHAR(20) NOT NULL,
    grenzwert_min FLOAT DEFAULT NULL,
    grenzwert_max FLOAT DEFAULT NULL,
    aktiv BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE measurements (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT NOT NULL,
    wert FLOAT NOT NULL,
    zeitstempel DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensors(id) ON DELETE CASCADE,
    INDEX idx_sensor_time (sensor_id, zeitstempel)
);

CREATE TABLE alarms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT NOT NULL,
    typ VARCHAR(20) NOT NULL,
    nachricht TEXT,
    wert FLOAT NOT NULL,
    zeitstempel DATETIME DEFAULT CURRENT_TIMESTAMP,
    quittiert BOOLEAN DEFAULT FALSE,
    quittiert_von VARCHAR(100) DEFAULT NULL,
    quittiert_zeit DATETIME DEFAULT NULL,
    FOREIGN KEY (sensor_id) REFERENCES sensors(id) ON DELETE CASCADE,
    INDEX idx_quittiert (quittiert),
    INDEX idx_zeitstempel (zeitstempel)
);

-- Standard-Sensoren einfügen
INSERT INTO sensors (name, typ, einheit, grenzwert_min, grenzwert_max) VALUES
('Server_Temp', 'temperature', '°C', 18.0, 26.0),
('Server_Feucht', 'humidity', '%', 40.0, 60.0),
('Gas_Sensor', 'gas', 'ppm', NULL, 500.0),
('Bewegung', 'motion', '', NULL, NULL);

EXIT;
```

### Phase 3: MQTT Broker (Mosquitto)

**3.1 Mosquitto installieren**

```bash
sudo apt install -y mosquitto mosquitto-clients

# Mosquitto starten und aktivieren
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

**3.2 Konfiguration**

```bash
sudo nano /etc/mosquitto/conf.d/serverraum.conf
```

```conf
listener 1883
allow_anonymous true

# Persistence
persistence true
persistence_location /var/lib/mosquitto/

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_dest stdout
```

```bash
sudo systemctl restart mosquitto
```

**3.3 Test**

```bash
# In einem Terminal: Subscriber starten
mosquitto_sub -t "sensor/#" -v

# In anderem Terminal: Test-Nachricht senden
mosquitto_pub -t "sensor/test/1" -m '{"value": 25.5}'
```

### Phase 4: Backend installieren

**4.1 Projekt klonen**

```bash
cd /opt
sudo git clone https://github.com/shadowsinthespace/serverraum-ueberwachung.git
cd serverraum-ueberwachung
```

**4.2 Python Environment**

```bash
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r backend/requirements.txt
```

**requirements.txt:**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pymysql==1.1.0
paho-mqtt==1.6.1
python-dotenv==1.0.0
pydantic==2.5.0
**4.3 Konfiguration**

```bash
nano backend/.env
```

```env
# Datenbank
DB_HOST=localhost
DB_PORT=3306
DB_NAME=serverraum
DB_USER=serverraum
DB_PASSWORD=DEIN_SICHERES_PASSWORT

# MQTT
MQTT_BROKER=localhost
MQTT_PORT=1883

# SMTP (E-Mail)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alarms@example.com
SMTP_PASSWORD=DEIN_EMAIL_PASSWORT
SMTP_FROM=serverraum@example.com
SMTP_TO=admin@example.com

```

**4.4 Systemd Service erstellen**

```bash
sudo nano /etc/systemd/system/serverraum-backend.service
```

```ini
[Unit]
Description=Serverraum Backend API
After=network.target mariadb.service mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/serverraum-ueberwachung/backend
Environment="PATH=/opt/serverraum-ueberwachung/venv/bin"
ExecStart=/opt/serverraum-ueberwachung/venv/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable serverraum-backend
sudo systemctl start serverraum-backend
```

**4.5 Test**

```bash
curl http://localhost:8001/api/health
# Erwartet: {"status":"healthy","mqtt":true,"db":true}
```

### Phase 5: Frontend (optional)

**5.1 Node.js installieren**

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

**5.2 Frontend bauen**

```bash
cd /opt/serverraum-ueberwachung/frontend
npm install
npm run build
```

**5.3 Nginx konfigurieren**

```bash
sudo apt install -y nginx

sudo nano /etc/nginx/sites-available/serverraum
```

```nginx
server {
    listen 80;
    server_name serverraum.local;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/serverraum /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## ESP32 Firmware flashen

### Hardware verkabeln

| ESP32 Pin | Sensor | Kabel |
|-----------|--------|-------|
| 3.3V | Alle Sensoren (VIN) | Rot |
| GND | Alle Sensoren (GND) | Schwarz |
| GPIO 21 | DS18B20 Data | Gelb/Grün |
| GPIO 22 | SCL (SHT31) | Blau |
| GPIO 21 | SDA (SHT31) | Weiß |
| GPIO 34 | AO (MQ-2) | Grün |
| GPIO 35 | Digital Out (PIR) | Violett |
| GPIO 2 | LED (optional) | Grün |

### Firmware hochladen

```bash
cd /opt/serverraum-ueberwachung/firmware

# Bibliotheken installieren (Arduino IDE oder PlatformIO)
# - PubSubClient
# - ArduinoJson
# - DallasTemperature
# - Adafruit_SHT31
# - OneWire

# ESP32 mit USB verbinden und flashen
pio run -e esp32dev -t upload
```

---

## Erster Start

1. **ESP32 einschalten** – LED sollte blinken
2. **Dashboard öffnen:** `http://serverraum.local:3001`
3. **Login:** admin / admin123 (bitte sofort ändern!)
4. **Sensoren prüfen:** Tab "Sensoren" – alle sollten Werte zeigen
5. **Alarm testen:** Grenzwert temporär niedrig setzen → Alarm sollte erscheinen

---

## Updates

```bash
cd /opt/serverraum-ueberwachung
git pull

# Backend
source venv/bin/activate
pip install -r backend/requirements.txt
sudo systemctl restart serverraum-backend

# Frontend
cd frontend && npm install && npm run build
```

---

## Deinstallation

```bash
# Backend stoppen und entfernen
sudo systemctl stop serverraum-backend
sudo systemctl disable serverraum-backend
sudo rm /etc/systemd/system/serverraum-backend.service

# Datenbank (optional - DATEN VERLOREN!)
sudo mysql -u root -p
DROP DATABASE serverraum;

# Projektordner
sudo rm -rf /opt/serverraum-ueberwachung
```

