# Konfigurationsbeispiele – Serverraum-Überwachung

Diese Datei zeigt die vollständige Konfiguration des Systems anhand von Beispielwerten.

---

## 1. Backend: .env

**Pfad:** `backend/.env`

```env
# ===========================================
# Datenbank-Konfiguration
# ===========================================
DB_HOST=localhost
DB_PORT=3306
DB_NAME=serverraum
DB_USER=serverraum
DB_PASSWORD=s3cur3P@ssw0rd2024!

# ===========================================
# MQTT-Broker
# ===========================================
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_KEEPALIVE=60
MQTT_CLIENT_ID=serverraum-backend

# ===========================================
# SMTP (E-Mail-Benachrichtigungen)
# ===========================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=serverraum-alarm@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_FROM=serverraum-alarm@gmail.com
SMTP_TO=admin@shadowsinthe.space,technik@shadowsinthe.space

# ===========================================
# Server-Konfiguration
# Server-Konfiguration
# ===========================================
HOST=0.0.0.0
PORT=3001
DEBUG=false
LOG_LEVEL=INFO

# ===========================================
# Sicherheit
# ===========================================
SECRET_KEY=dein-geheimer-schluessel-min-32-zeichen
CORS_ORIGINS=http://localhost:3001,http://serverraum.local
```

---

## 2. Backend: config.yaml (alternativ)

**Pfad:** `backend/config.yaml`

```yaml
# ===========================================
# Serverraum-Überwachung - Konfiguration
# ===========================================

system:
  name: "Serverraum-Überwachung"
  location: "Raum B-213"
  timezone: "Europe/Berlin"
  debug: false

# -------------------------------------------
# Datenbank
# -------------------------------------------
database:
  host: "localhost"
  port: 3306
  name: "serverraum"
  user: "serverraum"
  password: "${DB_PASSWORD}"  # Aus Environment
  
  # Connection Pool
  pool:
    size: 5
    max_overflow: 10
    pool_timeout: 30
    pool_recycle: 3600

# -------------------------------------------
# MQTT Broker
# -------------------------------------------
mqtt:
  broker: "localhost"
  port: 1883
  keepalive: 60
  client_id: "serverraum-backend"
  
  # Topics die subscribed werden sollen
  subscribe_topics:
    - "sensor/temperature/#"
    - "sensor/humidity/#"
    - "sensor/gas/#"
    - "sensor/motion/#"
    - "system/status/#"

# -------------------------------------------
# Sensoren (Definition)
# -------------------------------------------
sensors:
  - id: 1
    name: "Server_Temp"
    type: "temperature"
    pin: 21
    unit: "°C"
    enabled: true
    thresholds:
      min: 18.0
      max: 26.0
      warning_margin: 2.0

  - id: 2
    name: "Server_Feucht"
    type: "humidity"
    pin: 22
    unit: "%"
    enabled: true
    thresholds:
      min: 40.0
      max: 60.0
      warning_margin: 5.0

  - id: 3
    name: "Gas_Sensor"
    type: "gas"
    pin: 34
    unit: "ppm"
    enabled: true
    thresholds:
      min: null    # Kein Minimum relevant
      max: 500.0
      warning_margin: 100.0

  - id: 4
    name: "Bewegung"
    type: "motion"
    pin: 35
    unit: ""
    enabled: true
    thresholds:
      # Bewegung hat keine Grenzwerte
      # Nur Protokollierung

# -------------------------------------------
# Alarm-Konfiguration
# -------------------------------------------
alarm:
  # E-Mail-Benachrichtigung
  email:
    enabled: true
    smtp:
      host: "smtp.gmail.com"
      port: 587
      use_tls: true
      use_ssl: false
      username: "${SMTP_USER}"
      password: "${SMTP_PASSWORD}"
    from: "serverraum-alarm@gmail.com"
    recipients:
      - "admin@shadowsinthe.space"
      - "technik@shadowsinthe.space"
    
    # Wann E-Mail senden?
    send_on:
      - "WARNING"
      - "CRITICAL"
      - "INFO"
    
    # Cooldown (Sekunden) - keine doppelten E-Mails
    cooldown: 300

  # Hardware-Alarm (LED/Buzzer)
  hardware:
    enabled: true
    led_pin: 2
    buzzer_pin: 4
    
    # Nur bei diesem Schweregrad
    led_on_severity: ["WARNING", "CRITICAL"]
    buzzer_on_severity: ["CRITICAL"]

  # Alarm-Persistenz
  history:
    keep_days: 90    # Alte Alarme nach X Tagen löschen
    auto_quittiere_after_hours: null  # Keine automatische Quittierung

# -------------------------------------------
# Frontend / Web
# -------------------------------------------
frontend:
  host: "0.0.0.0"
  port: 3001
  
  # Polling-Intervalle (Millisekunden)
  poll:
    sensors: 30000    # 30 Sekunden
    alarms: 10000     # 10 Sekunden
    health: 60000     # 1 Minute
  
  # Chart-Konfiguration
  charts:
    history_hours: 24
    refresh_interval: 60000

# -------------------------------------------
# Logging
# -------------------------------------------
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # Log-Dateien
  files:
    - path: "/var/log/serverraum/backend.log"
      max_bytes: 10485760  # 10MB
      backup_count: 5
```

---

## 3. ESP32: config.h

**Pfad:** `firmware/src/config.h`

```cpp
#ifndef CONFIG_H
#define CONFIG_H

// ==========================================
// WiFi-Konfiguration
// ==========================================
#define WIFI_SSID "MeinWLAN"
#define WIFI_PASSWORD "MeinWLANPasswort"

// Optional: Statische IP
// #define USE_STATIC_IP
#ifdef USE_STATIC_IP
    #define STATIC_IP 192,168,178,51
    #define GATEWAY   192,168,178,1
    #define SUBNET    255,255,255,0
    #define DNS       192,168,178,1
#endif

// ==========================================
// MQTT-Konfiguration
// ==========================================
#define MQTT_BROKER "192.168.178.50"  // Raspberry Pi IP
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "ESP32_Serverraum"
#define MQTT_KEEPALIVE 60

// MQTT Topics
#define MQTT_TOPIC_PREFIX "sensor"
#define MQTT_TOPIC_TEMP "sensor/temperature/Server_Temp"
#define MQTT_TOPIC_HUM "sensor/humidity/Server_Feucht"
#define MQTT_TOPIC_GAS "sensor/gas/Gas_Sensor"
#define MQTT_TOPIC_MOTION "sensor/motion/Bewegung"
#define MQTT_TOPIC_STATUS "system/status/ESP32"

// ==========================================
// Sensor-Pins
// ==========================================
#define PIN_DS18B20 21      // OneWire für DS18B20
#define PIN_SHT31_SCL 22    // I2C Clock
#define PIN_SHT31_SDA 21    // I2C Data (gleicher Pin wie OneWire)
#define PIN_MQ2_AO 34       // Analog Output
#define PIN_PIR 35          // Digital Output
#define PIN_LED 2           // Onboard LED
#define PIN_BUZZER 4        // Buzzer (optional)

// ==========================================
// Timing
// ==========================================
#define PUBLISH_INTERVAL 30000    // 30 Sekunden
#define HEARTBEAT_INTERVAL 300000 // 5 Minuten
#define RECONNECT_DELAY 5000      // 5 Sekunden
#define WIFI_RECONNECT_DELAY 10000 // 10 Sekunden

// ==========================================
// Sensor-spezifisch
// ==========================================
// DS18B20
#define ONE_WIRE_BUS PIN_DS18B20

// SHT31
#define SHT31_ADDRESS 0x44

// MQ-2
#define MQ2_HEATED_SECONDS 60    // Aufwärmzeit

// PIR
#define PIR_DEBOUNCE_MS 2000      // 2 Sekunden Entprellung

#endif
```

---

## 4. Docker: docker-compose.yml

**Pfad:** `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  # -----------------------------------------
  # MariaDB Datenbank
  # -----------------------------------------
  database:
    image: mariadb:10.11
    container_name: serverraum-db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: serverraum
      MYSQL_USER: serverraum
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "127.0.0.1:3306:3306"  # Nur lokal!
    networks:
      - serverraum-net
    healthcheck:
      test: ["CMD", "healthcheck.sh"]
      interval: 10s
      timeout: 5s
      retries: 5

  # -----------------------------------------
  # Mosquitto MQTT Broker
  # -----------------------------------------
  mqtt:
    image: eclipse-mosquitto:2.0
    container_name: serverraum-mqtt
    restart: unless-stopped
    ports:
      - "127.0.0.1:1883:1883"  # Nur lokal!
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
      - mqtt_data:/mosquitto/data
      - mqtt_logs:/mosquitto/log
    networks:
      - serverraum-net
    healthcheck:
      test: ["CMD", "mosquitto_sub", "-t", "$$SYS/#", "-C", "1", "-i", "healthcheck", "-W", "3"]
      interval: 10s
      timeout: 5s
      retries: 3

  # -----------------------------------------
  # Backend API
  # -----------------------------------------
  backend:
    build:
      context: ../
      dockerfile: docker/Dockerfile.backend
    container_name: serverraum-backend
    restart: unless-stopped
    environment:
      - DB_HOST=database
      - DB_PORT=3306
      - DB_NAME=serverraum
      - DB_USER=serverraum
      - DB_PASSWORD=${DB_PASSWORD}
      - MQTT_BROKER=mqtt
      - MQTT_PORT=1883
    depends_on:
      database:
        condition: service_healthy
      mqtt:
        condition: service_healthy
    networks:
      - serverraum-net

  # -----------------------------------------
  # Nginx Reverse Proxy + Frontend
  # -----------------------------------------
  nginx:
    image: nginx:alpine
    container_name: serverraum-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ../frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - backend
    networks:
      - serverraum-net

# -----------------------------------------
# Netzwerke
# -----------------------------------------
networks:
  serverraum-net:
    driver: bridge

# -----------------------------------------
# Volumes
# -----------------------------------------
volumes:
  db_data:
  mqtt_data:
  mqtt_logs:
```

---

## 5. Nginx: nginx.conf

**Pfad:** `docker/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    gzip on;

    # Server
    server {
        listen 80;
        server_name serverraum.local;

        # Redirect zu HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name serverraum.local;

        # SSL-Zertifikat (Let's Encrypt empfohlen)
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security Headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Frontend (statische Dateien)
        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        # API-Proxy zum Backend
        location /api/ {
            proxy_pass http://backend:3001/api/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket Support (falls benötigt)
            proxy_webSocket on;
        }

        # Health-Endpoint
        location /health {
            proxy_pass http://backend:3001/api/health;
            proxy_http_version 1.1;
            access_log off;
        }
    }
}
```

---

## 6. Mosquitto: mosquitto.conf

**Pfad:** `docker/mosquitto.conf`

```conf
# ==========================================
# Mosquitto Konfiguration
# ==========================================

# Allgemein
listener 1883
allow_anonymous true
max_connections -1

# Persistence
persistence true
persistence_location /mosquitto/data/
persistence_file mosquitto.db
persistence_max_file_size 10mb

# Logging
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
log_type error
log_type warning
log_type notice
log_type information

# Connection Limits
max_keepalive 65535
max_inflight_messages 20
max_queued_messages 1000

# Message Size
message_size_limit 0
max_queued_bytes 0

# Security (Produktion!)
# allow_anonymous false
# password_file /mosquitto/config/passwd
```

---

## 7. Firewall-Regeln (UFW)

**Befehle:**

```bash
# Status prüfen
sudo ufw status

# Standard-Policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH erlauben (wichtig! Vor dem Aktivieren!)
sudo ufw allow 22/tcp comment 'SSH'

# HTTP/HTTPS
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Interne Dienste blockieren (nur lokaler Zugriff!)
# Diese sind bereits die Standardeinstellungen
# MariaDB: 3306/tcp - Keine Freigabe nach außen!
# Mosquitto: 1883/tcp - Keine Freigabe nach außen!

# Firewall aktivieren
sudo ufw enable

# Status anzeigen
sudo ufw status verbose
```

**Auszug: `sudo ufw status`**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
3306/tcp                   DENY        Anywhere
1883/tcp                  DENY        Anywhere
```
