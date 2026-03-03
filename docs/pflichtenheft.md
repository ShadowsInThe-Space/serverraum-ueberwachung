# Pflichtenheft

**Projekt:** Serverraum-Überwachungssystem
**Projektart:** IHK-Abschlussprojekt Fachinformatiker Anwendungsentwicklung
**Prüfungsteilnehmer:** Marc-Dennis Haberland
**Auftraggeber:** deCode GmbH / Herr Niklas
**Datum:** 03.03.2026
**Version:** 1.0

---

## 1. Einleitung

### 1.1 Zweck des Dokuments
Dieses Pflichtenheft beschreibt die technische Umsetzung des Serverraum-Überwachungssystems. Es dient als verbindliche Grundlage für die Implementierungsphase und enthält alle erforderlichen Spezifikationen.

### 1.2 Referenzen
- Lastenheft (Version 1.0)
- IHK-Projektantrag

---

## 2. Systemübersicht

### 2.1 Architektur

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  ESP32-S3   │────▶│   Mosquitto │────▶│   Backend   │────▶│  MariaDB    │
│  (Sensoren) │     │   Broker    │     │  (Python)   │     │  Datenbank  │
└─────────────┘     └─────────────┘     └──────┬──────┘     └─────────────┘
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │     Frontend    │
                                      │  (SPA, Tailwind)│
                                      └─────────────────┘
```

### 2.2 Komponenten
| Komponente | Technologie |
|-----------|-------------|
| Mikrocontroller | ESP32-S3 (Arduino-Framework, PlatformIO) |
| Sensoren | DHT22, DS18B20, MQ-2, MQ-135, PIR |
| Kommunikation | MQTT (Mosquitto), JSON-Payloads |
| Backend | Python 3.x (FastAPI oder Flask) |
| Datenbank | MariaDB |
| Frontend | JavaScript ES6+, HTML, Tailwind CSS |

---

## 3. Hardware-Spezifikationen

### 3.1 ESP32-S3 GPIO-Belegung

**Gesperrte Pins (NICHT verwenden):**
- GPIO 26-32: Intern mit SPI-Flash & PSRAM verdrahtet
- GPIO 35, 36, 37: Beim ESP32-S3R8 intern gesperrt
- GPIO 0, 3, 45, 46: Strapping Pins (Boot-Modus)

**Empfohlene Zuordnung:**

| Sensor | Pin | Typ | Beschreibung |
|--------|-----|-----|--------------|
| DHT22 | GPIO 5 | Digital | Temperatur + Luftfeuchtigkeit |
| DS18B20 | GPIO 4 | Digital (OneWire) | Temperatur (alternativ) |
| MQ-2 (Rauch) | GPIO 1 | ADC | Analoger Sensor für Rauchgas |
| MQ-135 (Luft) | GPIO 2 | ADC | Analoger Sensor für Luftqualität |
| PIR | GPIO 6 | Digital | Bewegungserkennung |
| Warn-LED | GPIO 7 | Digital Output | Visuelle Alarmierung |
| Buzzer | GPIO 8 | Digital Output | Akustische Alarmierung |

**Technische Spezifikationen:**
- Logikpegel: 3,3V
- ADC: 12-Bit (0-3,3V → 0-4095)
- UART0 (fest): TX=GPIO 43, RX=GPIO 44

---

## 4. MQTT-Spezifikationen

### 4.1 Topic-Struktur

```
serverraum/sensor/temperatur    # Temperaturdaten
serverraum/sensor/luftfeuchtigkeit  # Luftfeuchtigkeitsdaten
serverraum/sensor/gas          # Gas/Rauch-Werte
serverraum/sensor/bewegung     # Bewegungserkennung
serverraum/status/online       # ESP32 Online-Status
serverraum/status/fehler       # Fehlermeldungen
```

### 4.2 JSON-Payload-Format

**Temperatur/Luftfeuchtigkeit:**
```json
{
  "sensor_id": "esp32-001",
  "typ": "dht22",
  "temperatur": 22.5,
  "luftfeuchtigkeit": 45.0,
  "einheit": {
    "temperatur": "°C",
    "luftfeuchtigkeit": "%"
  },
  "timestamp": "2026-03-03T15:30:00Z"
}
```

**Gas-Sensor:**
```json
{
  "sensor_id": "esp32-001",
  "typ": "mq2",
  "wert": 150,
  "einheit": "ppm",
  "alarm_schwellwert": 200,
  "timestamp": "2026-03-03T15:30:00Z"
}
```

**Bewegung:**
```json
{
  "sensor_id": "esp32-001",
  "typ": "pir",
  "bewegung_erkannt": true,
  "timestamp": "2026-03-03T15:30:00Z"
}
```

---

## 5. Datenbank-Spezifikationen

### 5.1 Tabellenstruktur

**Tabelle: sensoren**
| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INT AUTO_INCREMENT | Primärschlüssel |
| sensor_typ | VARCHAR(50) | Sensortyp (dht22, mq2, etc.) |
| name | VARCHAR(100) | Anzeigename |
| gpio_pin | INT | Verbundener GPIO-Pin |
| aktiv | BOOLEAN | Sensor aktiv/inaktiv |
| created_at | DATETIME | Erstellungszeitpunkt |

**Tabelle: messungen**
| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INT AUTO_INCREMENT | Primärschlüssel |
| sensor_id | INT | Fremdschlüssel zu sensoren |
| wert | DECIMAL(10,2) | Messwert |
| einheit | VARCHAR(20) | Einheit (°C, %, ppm) |
| timestamp | DATETIME | Messzeitpunkt |

**Tabelle: alarm_konfiguration**
| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INT AUTO_INCREMENT | Primärschlüssel |
| sensor_id | INT | Fremdschlüssel zu sensoren |
| alarm_typ | VARCHAR(50) | Alarmtyp |
| schwellwert_min | DECIMAL(10,2) | Unterer Schwellwert |
| schwellwert_max | DECIMAL(10,2) | Oberer Schwellwert |
| alarmierung_email | BOOLEAN | E-Mail-Alarmierung |
| alarmierung_led | BOOLEAN | LED-Alarmierung |
| alarmierung_buzzer | BOOLEAN | Buzzer-Alarmierung |

**Tabelle: alarms**
| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INT AUTO_INCREMENT | Primärschlüssel |
| sensor_id | INT | Fremdschlüssel zu sensoren |
| alarm_typ | VARCHAR(50) | Alarmtyp |
| messwert | DECIMAL(10,2) | Auslösender Messwert |
| schwellwert | DECIMAL(10,2) | Überschrittener Schwellwert |
| status | VARCHAR(20) | aktiv/acknowledged/resolved |
| created_at | DATETIME | Erstelldatum |
| acknowledged_at | DATETIME | Quittierungsdatum |

---

## 6. API-Spezifikationen

### 6.1 REST-API Endpunkte

| Methode | Pfad | Beschreibung |
|--------|------|--------------|
| GET | /api/sensoren | Alle Sensoren abrufen |
| GET | /api/sensoren/{id} | Einzelner Sensor |
| GET | /api/messungen | Letzte Messungen |
| GET | /api/messungen/{sensor_id} | Messungen pro Sensor |
| GET | /api/alarms | Aktive Alarme |
| POST | /api/alarms/{id}/acknowledge | Alarm bestätigen |
| GET | /api/konfiguration | Alarm-Konfiguration |
| PUT | /api/konfiguration | Konfiguration ändern |

### 6.2 WebSocket (optional)
Für Echtzeit-Updates im Dashboard:
- Endpoint: /ws
- Protokoll: JSON-Nachrichten über WebSocket

---

## 7. Alarmierungs-Spezifikationen

### 7.1 Schwellwerte

| Sensor | Unterer Schwellwert | Oberer Schwellwert | Alarmierung |
|--------|---------------------|--------------------|-------------|
| Temperatur | 15°C | 30°C | E-Mail, LED |
| Luftfeuchtigkeit | 30% | 70% | E-Mail, LED |
| MQ-2 (Rauch) | - | 200 ppm | E-Mail, LED, Buzzer |
| MQ-135 (Luft) | - | 100 ppm | E-Mail, LED |
| Bewegung | - | - | E-Mail, LED, Buzzer |

### 7.2 Alarmierungswege

| Alarmierung | Beschreibung |
|-------------|--------------|
| E-Mail | SMTP an konfigurierte Empfänger |
| Warn-LED | GPIO-Pin für LED schalten |
| Buzzer | GPIO-Pin für akustischen Alarm |
| Dashboard | WebSocket/Push an SPA |

---

## 8. Frontend-Spezifikationen

### 8.1 Seitenstruktur

| Seite | Beschreibung |
|-------|--------------|
| Dashboard | Übersicht aller Sensoren mit aktuellen Werten |
| Verlauf | Historische Daten mit Diagrammen |
| Alarme | Liste aktiver und vergangener Alarme |
| Einstellungen | Sensor- und Alarm-Konfiguration |

### 8.2 UI-Komponenten

- **Sensor-Karten:** Aktuelle Werte mit Farbindikator (grün/gelb/rot)
- **Linien-Diagramm:** Zeitlicher Verlauf der Messwerte
- **Alarm-Liste:** Sortierbare Tabelle mit Status
- **Konfigurations-Formulare:** CRUD für Sensoren und Schwellwerte

---

## 9. Test-Anforderungen

### 9.1 Funktionstests
- [ ] Sensordaten werden korrekt erfasst und übertragen
- [ ] Schwellwerte lösen Alarme aus
- [ ] Alle Alarmierungswege funktionieren
- [ ] Daten werden in MariaDB gespeichert
- [ ] Dashboard zeigt aktuelle Werte

### 9.2 Integrationstests
- [ ] ESP32 → MQTT → Backend → Datenbank
- [ ] Backend → E-Mail-Versand
- [ ] Backend → MariaDB → Frontend

---

## 10. Abnahmekriterien

| Kriterium | Beschreibung |
|-----------|--------------|
| K1 | Alle Sensoren erfassen Daten und senden via MQTT |
| K2 | Alarme werden bei Schwellwertüberschreitung ausgelöst |
| K3 | E-Mail-Benachrichtigungen werden versendet |
| K4 | Dashboard zeigt Echtzeitdaten |
| K5 | Daten werden in MariaDB persistiert |
| K6 | OOP-Polymorphie in Firmware implementiert |
| K7 | Code ist kommentiert (Deutsch) |
| K8 | Alle Dokumente (Lastenheft, Pflichtenheft, Diagramme) vorhanden |

---

**Genehmigung:**

| Rolle | Name | Datum | Unterschrift |
|-------|------|-------|--------------|
| Auftraggeber | Herr Niklas | | |
| Prüfungsteilnehmer | Marc-Dennis Haberald | | |
