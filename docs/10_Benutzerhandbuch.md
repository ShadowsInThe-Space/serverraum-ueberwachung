# Benutzerhandbuch – Serverraum-Überwachung

> Version: 1.0 | Stand: April 2026

---

## Inhaltsverzeichnis

1. [Systemübersicht](#1-systemübersicht)
2. [Erste Schritte](#2-erste-schritte)
3. [Dashboard bedienen](#3-dashboard-bedienen)
4. [Alarme verwalten](#4-alarme-verwalten)
5. [Sensoren konfigurieren](#5-sensoren-konfigurieren)
6. [Grenzwerte anpassen](#6-grenzwerte-anpassen)
7. [Benachrichtigungen einrichten](#7-benachrichtigungen-einrichten)
8. [Wartung & Troubleshooting](#8-wartung--troubleshooting)

---

## 1. Systemübersicht

### 1.1 Was wird überwacht?

Das System überwacht kontinuierlich die klimatischen Bedingungen im Serverraum:

| Sensor | Misst | Normalbereich |
|--------|-------|---------------|
| 🌡️ Temperatur | Serverraum-Temperatur | 18°C – 26°C |
| 💧 Feuchtigkeit | Luftfeuchtigkeit | 40% – 60% |
| 🔥 Gas (MQ-2) | Luftqualität / Rauchgase | < 500 ppm |
| 👤 Bewegung | Präsenz im Serverraum | – |

### 1.2 Komponenten

```
┌─────────────────────────────────────────────────────────────┐
│                      SERVERRAUM                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ ESP32   │  │ Sensoren │  │  LED    │  │ Buzzer  │       │
│  │ S3      │◄─┤ DS18B20 │  │ (Alarm) │  │ (Alarm) │       │
│  │         │  │ SHT31   │  └────▲────┘  └────▲────┘       │
│  │         │  │ MQ-2    │       │            │              │
│  │    WiFi │◄─┤ PIR     │       │            │              │
│  └────┬────┘  └─────────┘       │            │              │
│       │ MQTT                     │            │              │
└───────┼──────────────────────────┼────────────┼──────────────┘
        │                          │            │
        ▼                          ▼            ▼
   ┌─────────────────────────────────────────┐
   │              BACKEND (Raspberry Pi)       │
   │  ┌──────────┐  ┌──────────┐  ┌───────┐ │
   │  │ MQTT     │  │ Alarm    │  │ MariaDB│ │
   │  │ Broker   │  │ Engine   │  │   DB   │ │
   │  └────┬─────┘  └────┬─────┘  └───┬───┘ │
   │       │            │            │       │
   │       │    ┌───────┴───────┐    │       │
   │       └───►│  FastAPI      │◄───┘       │
   │            │  REST API     │            │
   │            └───────┬───────┘            │
   └────────────────────┼────────────────────┘
                        │
                        ▼
            ┌─────────────────────────┐
            │   Dashboard (Web-UI)    │
            │   localhost:3001        │
            └─────────────────────────┘
```

---

## 2. Erste Schritte

### 2.1 Dashboard öffnen

1. Browser öffnen (Chrome, Firefox, Edge empfohlen)
2. Adresse eingeben: `http://localhost:3001` (lokal) oder `http://serverraum.local` (Netzwerk)
3. Login mit Benutzerdaten (Standard: `admin` / `admin123`)

### 2.2 Startansicht

Nach dem Login siehst du die **Übersicht** mit:
- 4 Status-Karten (System, Temperatur, Feuchtigkeit, Alarme)
- 24-Stunden-Chart der Temperatur
- Letzte Alarme

---

## 3. Dashboard bedienen

### 3.1 Navigation

Das Dashboard hat 4 Tabs:

| Tab | Funktion |
|-----|----------|
| **Übersicht** | Zusammenfassung aller Werte |
| **Sensoren** | Detaillierte Sensordaten |
| **Alarme** | Alarmhistorie und -verwaltung |
| **Einstellungen** | Systemkonfiguration |

### 3.2 Übersicht (Tab 1)

**Status-Karten:**
- ⚡ **System**: Zeigt ob alle Komponenten online sind
- 🌡️ **Temperatur**: Aktueller + Grenzwert
- 💧 **Feuchtigkeit**: Aktueller + Grenzwert  
- 🚨 **Alarme**: Anzahl offener Alarme

**Diagramme:**
- Verlaufsdiagramm (24h)
- Balkendiagramm (Sensor-Status)

### 3.3 Sensoren (Tab 2)

**Sensortabelle:**

| Spalte | Bedeutung |
|--------|----------|
| Name | Sensorsystemname |
| Typ | Temperatur, Feuchtigkeit, Gas, Bewegung |
| Wert | Aktueller Messwert |
| Status | ✅ OK / 🟡 Warnung / 🔴 Kritisch |
| Grenzwerte | Min/Max für diesen Sensor |

**Detailansicht:**
1. Sensor in Tabelle anklicken
2. Rechts erscheint Detailpanel mit:
   - Letzter Wert + Zeitstempel
   - Durchschnitt (24h)
   - Minimum / Maximum
   - Verlaufsdiagramm

---

## 4. Alarme verwalten

### 4.1 Alarmtypen

| Symbol | Typ | Bedeutung |
|--------|-----|----------|
| 🔴 | KRITISCH | Grenzwert stark überschritten, sofort handeln! |
| 🟡 | WARNUNG | Grenzwert in der Nähe, beobachten |
| ⚪ | INFO | Systemmeldung (z.B. Neustart) |

### 4.2 Alarmtabelle

**Spalten:**
- Schweregrad
- Sensor (welcher Sensor hat ausgelöst)
- Wert (gemessener Wert)
- Zeitpunkt
- Status (Offen / Quittiert)

**Filteroptionen:**
- Alle Alarme
- Nur offene
- Letzte 24 Stunden
- Nach Schweregrad

### 4.3 Alarm quittieren

**Warum Quittieren?**
- Signalisiert: "Ich habe den Alarm zur Kenntnis genommen"
- Alarme verschwinden nicht einfach, sie werden dokumentiert

**So geht's:**
1. Tab "Alarme" öffnen
2. Alarm auswählen
3. Button **[Quittieren]** klicken
4. Bestätigung: Alarm wechselt zu "✓ Quittiert"

**Wichtig:** Quittieren ≠ Löschen. Der Alarm bleibt in der Historie.

### 4.4 E-Mail bei Alarm

Wenn ein Alarm ausgelöst wird:
1. E-Mail wird automatisch an konfigurierte Empfänger gesendet
2. Betreff enthält: Schweregrad, Sensor, Wert
3. E-Mail enthält: Alle Details + Zeitstempel

---

## 5. Sensoren konfigurieren

### 5.1 Sensor hinzufügen

> ⚠️ Nur für Administratoren

1. **Einstellungen** → **Sensoren** → **[Neuer Sensor]**
2. Felder ausfüllen:
   - Name (z.B. "Rack_Temp_3")
   - Typ (Temperatur/Feuchtigkeit/Gas/Bewegung)
   - Pin (GPIO am ESP32)
   - Einheit (°C, %, ppm)
3. **[Speichern]** klicken
4. ESP32 startet automatisch neu

### 5.2 Sensor deaktivieren

1. Sensor in Tabelle auswählen
2. **Aktiv**-Häkchen entfernen
3. **[Speichern]**

Deaktivierte Sensoren erscheinen in der Übersicht mit grauem Icon.

---

## 6. Grenzwerte anpassen

### 6.1 Standardwerte

| Sensor | Minimum | Maximum | Warnung |
|--------|---------|---------|---------|
| Temperatur | 18°C | 26°C | ±2°C |
| Feuchtigkeit | 40% | 60% | ±5% |
| Gas (MQ-2) | – | 500 ppm | 400 ppm |

### 6.2 Grenzwerte ändern

1. **Einstellungen** → **Grenzwerte**
2. Für jeden Sensor Min/Max eintragen
3. **[Speichern]**

**Warnung:** Zu enge Grenzwerte → viele Fehlalarme
**Warnung:** Zu weite Grenzwerte → kritische Zustände werden nicht erkannt

### 6.3 Empfehlung

- **Hardware-spezifisch:** Herstellerangaben beachten
- **Saisonal anpassen:** Im Sommer höhere Temperatur tolerieren
- **Testen:** Nach Änderung Grenzwerte testen

---

## 7. Benachrichtigungen einrichten

### 7.1 E-Mail-Benachrichtigung

1. **Einstellungen** → **Benachrichtigungen**
2. ✅ "E-Mail bei Alarm" aktivieren
3. Empfänger eintragen (kommagetrennt)
4. SMTP-Daten (wenn nicht automatisch erkannt):
   - SMTP-Server
   - Port (Standard: 587)
   - Benutzername / Passwort
5. **[Test-E-Mail senden]** → Bestätigung abwarten
6. **[Speichern]**

### 7.2 Hardware-Alarm (LED/Buzzer)

Optional kann bei Alarm auch Hardware ausgelöst werden:

| Option | Beschreibung |
|--------|--------------|
| LED | Rote LED blinkt bei Alarm |
| Buzzer | Akustisches Signal bei kritischen Alarmen |

**Konfiguration:**
1. **Einstellungen** → **Hardware**
2. GPIO-Pins eintragen (falls nicht automatisch erkannt)
3. Buzzer nur für KRITISCHE Alarme ✅

---

## 8. Wartung & Troubleshooting

### 8.1 Status prüfen

**Systemgesundheit** (ganz unten auf jeder Seite):
```
Systemversion: 1.0.0
ESP32 Firmware: v1.2.3
Letzter Neustart: vor 3 Tagen
```

**Health-Endpoint:**
```bash
curl http://localhost:3001/api/health
```

Erwartete Antwort:
```json
{
  "status": "healthy",
  "mqtt": true,
  "db": true
}
```

### 8.2 Häufige Probleme

#### Problem: "Sensor wird nicht angezeigt"

| Ursache | Lösung |
|---------|--------|
| Sensor nicht verkabelt | Verkabelung prüfen (siehe Pin-Belegung) |
| Falscher Pin | Pin in Sensor-Konfiguration prüfen |
| ESP32 nicht verbunden | WiFi-Status prüfen |

#### Problem: "Keine neuen Messwerte"

1. ESP32 neustarten: `sudo systemctl restart serverraum-esp32`
2. MQTT-Verbindung prüfen: `mosquitto_pub -t "test" -m "ping"`
3. Backend-Logs prüfen: `journalctl -u serverraum-backend -f`

#### Problem: "E-Mail kommt nicht an"

1. SMTP-Einstellungen prüfen
2. Spam-Ordner checken
3. Test-E-Mail senden (Button in Einstellungen)
4. Firewall-Regeln prüfen (Port 587 muss offen sein)

#### Problem: "Dashboard lädt nicht"

1. Backend prüfen: `sudo systemctl status serverraum-backend`
2. Neustart: `sudo systemctl restart serverraum-backend`
3. Port prüfen: `sudo netstat -tlnp | grep 3001`

### 8.3 Logs finden

| Komponente | Log-Datei |
|------------|------------|
| Backend | `/var/log/serverraum/backend.log` |
| ESP32 | Serielle Konsole (115200 Baud) |
| MQTT | `/var/log/mosquitto/mosquitto.log` |
| Nginx | `/var/log/nginx/error.log` |

### 8.4 Backup

**Datenbank sichern:**
```bash
mysqldump -u root -p serverraum > backup_$(date +%Y%m%d).sql
```

**Konfiguration sichern:**
```bash
cp /opt/serverraum/config/config.yaml ~/backup_config.yaml
```

### 8.5 Updates

**Backend aktualisieren:**
```bash
cd /opt/serverraum
git pull
pip install -r requirements.txt
sudo systemctl restart serverraum-backend
```

**ESP32 firmware aktualisieren:**
1. Neue `.bin` hochladen via Web-Interface (oder)
2. Über Arduino IDE neu flashen

---

## Anhang: Tastenkürzel

| Tastenkürzel | Funktion |
|--------------|----------|
| `F5` | Seite aktualisieren |
| `Esc` | Modal/Dialog schließen |
| `Enter` | Auswahl bestätigen |

---

## Kontakt & Support

Bei Problemen oder Fragen:

- **Dokumentation:** `/opt/serverraum/docs/`
- **Issue Tracker:** github.com/shadowsinthespace/serverraum-ueberwachung/issues
- **E-Mail:** admin@shadowsinthe.space

---

*Letztes Update: April 2026 – Version 1.0*
