# Troubleshooting / Fehleranalyse – Serverraum-Überwachung

## Diagnose-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM-KOMponenten                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [ESP32]  ──WiFi/MQTT──►  [MQTT Broker]  ──►  [Backend]   │
│      │                          │                     │      │
│      │                          │                     │      │
│   Sensoren                  Mosquitto              FastAPI  │
│      │                          │                     │      │
│      │                          │                     │      │
│      ▼                          ▼                     ▼      │
│  [Hardware]               [Logs/Port]           [Dashboard]  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Fehler 1: ESP32 verbindet sich nicht mit WiFi

### Symptom
LED blinkt dauerhaft rot, keine Daten im Dashboard.

### Diagnose

```bash
# Serielle Ausgabe prüfen (115200 Baud)
screen /dev/ttyUSB0 115200
# oder
pio device monitor
```

### Mögliche Ursachen & Lösungen

| Ursache | Diagnose | Lösung |
|---------|----------|--------|
| Falsche WiFi-Daten | "WiFi connect failed" | SSID/Passwort in `config.h` prüfen |
| WiFi nicht erreichbar | "No route to host" | Router/Access Point prüfen |
| Signal zu schwach | RSSI < -80 dBm | ESP32 näher an AP bringen |
| IP-Konflikt | "DHCP failed" | Reserve IP im Router oder statische IP |

### Lösung

```cpp
// In src/config.h
const char* WIFI_SSID = "DEIN_WLAN_NAME";
const char* WIFI_PASSWORD = "DEIN_WLAN_PASSWORT";

// Für statische IP (optional):
// #define USE_STATIC_IP
// IPAddress localIP(192, 168, 1, 100);
// IPAddress gateway(192, 168, 1, 1);
// IPAddress subnet(255, 255, 255, 0);
```

---

## Fehler 2: MQTT-Verbindung fehlgeschlagen

### Symptom
```
[MQTT] Connecting to broker... failed, rc=-2
```

### Diagnose

```bash
# MQTT Broker Status
systemctl status mosquitto

# MQTT Logs
journalctl -u mosquitto -f

# Port prüfen
sudo netstat -tlnp | grep 1883
```

### Mögliche Ursachen & Lösungen

| Ursache | Diagnose | Lösung |
|---------|----------|--------|
| Broker läuft nicht | `systemctl status mosquitto` zeigt "inactive" | `sudo systemctl start mosquitto` |
| Falsche IP/Port | Broker nicht auf angegebener Adresse | IP = localhost, Port = 1883 |
| Firewall blockiert | Port 1883 nicht offen | `sudo ufw allow 1883` |
| Auth-Problem | "Connection refused" | `allow_anonymous true` in mosquitto.conf |

### Lösung

```bash
# Mosquitto neu starten
sudo systemctl restart mosquitto

# Test-Nachricht senden
mosquitto_pub -t "test" -m "hello" -h localhost -p 1883
mosquitto_sub -t "test" -v
```

---

## Fehler 3: Sensordaten werden nicht gespeichert

### Symptom
Dashboard zeigt "N/A" oder veraltete Werte.

### Diagnose

```bash
# Backend Logs prüfen
journalctl -u serverraum-backend -f

# API direkt aufrufen
curl http://localhost:8001/api/sensors
```

### Mögliche Ursachen & Lösungen

| Ursache | Diagnose | Lösung |
|---------|----------|--------|
| Backend läuft nicht | `curl` gibt "Connection refused" | `sudo systemctl start serverraum-backend` |
| DB-Verbindung fehlgeschlagen | Logs zeigen "MySQL Connection Error" | DB-Credentials in `.env` prüfen |
| Falsche Topic-Namen | ESP32 published auf falschem Topic | Topic-Struktur: `sensor/{typ}/{name}` |
| MQTT-Callback feuert nicht | `on_message` wird nie aufgerufen | `client.loop()` in ESP32 loop() prüfen |

### Lösung

```bash
# Datenbank-Verbindung testen
mysql -u serverraum -p -h localhost serverraum

# Tabelle prüfen
SELECT * FROM measurements ORDER BY zeitstempel DESC LIMIT 5;
```

---

## Fehler 4: Alarm wird nicht ausgelöst

### Symptom
Wert überschreitet Grenzwert, aber kein Alarm erscheint.

### Diagnose

```bash
# Alarm-Tabelle prüfen
mysql -u serverraum -p -h localhost serverraum
SELECT * FROM alarms ORDER BY zeitstempel DESC LIMIT 10;
```

### Mögliche Ursachen & Lösungen

| Ursache | Diagnose | Lösung |
|---------|----------|--------|
| AlarmEngine bekommt keine Daten | Backend-Logs prüfen | MQTT-Callback muss AlarmEngine aufrufen |
| Grenzwert nicht gesetzt | `sensors`-Tabelle prüfen | `grenzwert_min/max` setzen |
| Sensor als "inaktiv" markiert | `aktiv = FALSE` | `aktiv = TRUE` setzen |
| E-Mail-Config fehlt | SMTP-Verbindungsfehler | `.env` SMTP-Daten prüfen |

### Lösung

```sql
-- Grenzwerte setzen
UPDATE sensors SET grenzwert_min = 18.0, grenzwert_max = 26.0 WHERE name = 'Server_Temp';

-- Sensor aktivieren
UPDATE sensors SET aktiv = TRUE WHERE id = 1;
```

---

## Fehler 5: Dashboard lädt nicht

### Symptom
Browser zeigt "Connection refused" oder Timeout.

### Diagnose

```bash
# Backend erreichbar?
curl http://localhost:8001/api/health

# Port 3001 offen?
sudo netstat -tlnp | grep 3001
```

### Mögliche Ursachen & Lösungen

| Ursache | Diagnose | Lösung |
|---------|----------|--------|
| Backend nicht gestartet | `curl` gibt "Connection refused" | `sudo systemctl start serverraum-backend` |
| Falscher Port | Port stimmt nicht überein | Port in Backend = 3001, nicht 8001 |
| Nginx Fehler | `nginx error.log` prüfen | Config neu laden: `sudo nginx -t && sudo systemctl reload nginx` |
| CORS-Problem | Browser-Konsole zeigt CORS-Fehler | Backend CORS-Origin konfigurieren |

### Lösung

```bash
# Backend neustarten
sudo systemctl restart serverraum-backend

# Logs prüfen
journalctl -u serverraum-backend -n 50 -f
```

---

## Fehler 6: E-Mail wird nicht gesendet

### Symptom
Alarm erscheint in DB, aber keine E-Mail kommt an.

### Diagnose

```bash
# Backend Logs auf SMTP-Fehler prüfen
journalctl -u serverraum-backend | grep -i smtp
```

### Mögliche Ursachen & Lösungen

| Ursache | Diagnose | Lösung |
|---------|----------|--------|
| Falsche SMTP-Daten | "SMTP authentication failed" | Benutzername/Passwort prüfen |
| Firewall/Port | "Connection timed out" | Port 587 oder 465 öffnen |
| Spam-Filter | E-Mail in Spam-Ordner | Absender als vertrauenswürdig markieren |
| TLS/SSL-Problem | "SSL_CTX_load_verify_locations" | SSL-Zertifikate installieren |

### Lösung

```python
# Test-Skript
from alarm import AlarmEngine
alarm = AlarmEngine(smtp_config={...})
alarm._send_alert_email({...}, 30.5, "CRITICAL")
```

---

## Fehler 7: ESP32 startet nicht

### Symptom
ESP32 zeigt keine Reaktion, LED leuchtet nicht.

### Mögliche Ursachen & Lösungen

| Ursache | Lösung |
|---------|--------|
| Stromversorgung zu schwach | 3.3V >= 500mA Netzteil verwenden |
| USB-Kabel defekt | Kabel mit Datenleitungen (nicht nur Ladekabel) |
| Flash fehlgeschlagen | Erneut flashen mit `pio run -t upload` |
| Bootloader beschädigt | Mit esptool flashen: `esptool.py erase_flash` |

### Lösung

```bash
# Vollständiger Reboot
esptool.py --port /dev/ttyUSB0 erase_flash
pio run -e esp32dev -t upload
pio device monitor
```

---

## Log-Dateien Übersicht

| Komponente | Log-Datei / Befehl |
|------------|---------------------|
| Backend | `journalctl -u serverraum-backend -f` |
| ESP32 | `pio device monitor` oder `screen /dev/ttyUSB0 115200` |
| MQTT | `tail -f /var/log/mosquitto/mosquitto.log` |
| Nginx | `tail -f /var/log/nginx/error.log` |
| MariaDB | `tail -f /var/log/mysql/error.log` |

---

## Quick-Check Liste

```
□ ESP32: LED zeigt正常的 (kein Fehler-Blinken)?
□ ESP32: Serielle Ausgabe zeigt "WiFi connected"?
□ ESP32: Serielle Ausgabe zeigt "MQTT connected"?
□ MQTT Broker: `systemctl status mosquitto` = active?
□ Backend: `curl http://localhost:8001/api/health` = healthy?
□ Datenbank: Messwerte werden in Tabelle geschrieben?
□ Dashboard: Sensordaten aktuell (< 1 Minute alt)?
```

---

## Support kontaktieren

Wenn das Problem nicht behoben werden kann:

1. Logs sammeln: `journalctl --since "1 hour ago" > system.log`
2. Config teilen: `cat backend/.env` (Passwörter entfernen!)
3. Issue erstellen: github.com/shadowsinthespace/serverraum-ueberwachung/issues
