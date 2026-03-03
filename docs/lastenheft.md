# Lastenheft

**Projekt:** Serverraum-Überwachungssystem
**Projektart:** IHK-Abschlussprojekt Fachinformatiker Anwendungsentwicklung
**Prüfungsteilnehmer:** Marc-Dennis Haberland
**Auftraggeber:** deCode GmbH / Herr Niklas
**Datum:** 03.03.2026
**Version:** 1.0

---

## 1. Projektübersicht

### 1.1 Projektname
Modulares Überwachungs- und Steuerungssystem für einen Serverraum

### 1.2 Projektziel
Entwicklung einer zuverlässigen, leistungsfähigen und kosteneffizienten Überwachungslösung, die speziell auf die Anforderungen der Gaming-Infrastruktur zugeschnitten ist und Unabhängigkeit von Cloud-Diensten externer Anbieter gewährleistet.

### 1.3 Projektumfeld
- **Auftraggeber:** deCode GmbH, vertreten durch Herrn Niklas
- **Einsatzort:** Serverraum im Altbau des Gaming Developer Bootcamps
- **Benutzer:** IT-Administratoren, Betreiber des Bootcamps
- **Prüfungsinstanz:** IHK Essen, Mülheim an der Ruhr, Oberhausen

---

## 2. Funktionale Anforderungen

### 2.1 Sensordatenerfassung (F-001 bis F-006)

| ID | Anforderung | Beschreibung | Priorität |
|----|-------------|-------------|-----------|
| F-001 | Firmware-Entwicklung | Stabile C++-Firmware für ESP32-S3 | Muss |
| F-002 | Klimadaten erfassen | Temperatur und Luftfeuchtigkeit messen | Muss |
| F-003 | Brandindikatoren erfassen | Gas- und Rauchkonzentration messen | Muss |
| F-004 | Bewegung erfassen | PIR-Bewegungsmelder für Einbruchschutz | Muss |
| F-005 | Datenübertragung | Übertragung via MQTT-Protokoll | Muss |
| F-006 | OOP-Polymorphie | Objektorientierte Programmierung mit Polymorphie zur Sensor-Abstraktion | Muss |

### 2.2 Einbruchschutz (F-010 bis F-011)

| ID | Anforderung | Beschreibung | Priorität |
|----|-------------|-------------|-----------|
| F-010 | Bewegungsmelder | Infrarot-Bewegungsmelder (PIR) | Muss |
| F-011 | Sofortige Alarmierung | Direkte Benachrichtigung bei Bewegungserkennung | Muss |

### 2.3 Verarbeitungsschicht (F-020 bis F-023)

| ID | Anforderung | Beschreibung | Priorität |
|----|-------------|-------------|-----------|
| F-020 | Python-Backend | Python-Backend auf Raspberry Pi | Muss |
| F-021 | Datenvalidierung | Validierung eingehender Sensordaten | Muss |
| F-022 | Grenzwertüberwachung | Prüfung gegen definierte Schwellwerte | Muss |
| F-023 | Alarm-Engine | Logik zur Auslösung von Alarmen | Muss |

### 2.4 Datenspeicherung (F-030 bis F-032)

| ID | Anforderung | Beschreibung | Priorität |
|----|-------------|-------------|-----------|
| F-030 | MariaDB-Datenbank | Relationale Datenbank (MariaDB) | Muss |
| F-031 | Dauerhafte Speicherung | Persistenz aller Sensordaten | Muss |
| F-032 | Historische Daten | Speicherung für vorausschauende Wartung | Muss |

### 2.5 Dashboard (F-040 bis F-044)

| ID | Anforderung | Beschreibung | Priorität |
|----|-------------|-------------|-----------|
| F-040 | Echtzeit-Dashboard | Single-Page-Application | Muss |
| F-041 | JavaScript | ES6+ Modernes JavaScript | Muss |
| F-042 | Tailwind CSS | CSS-Framework für Styling | Muss |
| F-043 | Echtzeit-Anzeige | Live-Darstellung aller Sensordaten | Muss |
| F-044 | Alarm-Anzeige | Visuelle Darstellung aktiver Alarme | Muss |

### 2.6 Alarmierung (F-050 bis F-053)

| ID | Anforderung | Beschreibung | Priorität |
|----|-------------|-------------|-----------|
| F-050 | E-Mail-Alarmierung | SMTP-basierte E-Mail-Benachrichtigung | Muss |
| F-051 | Warn-LED | Visuelle Alarmierung durch LED | Muss |
| F-052 | Dashboard-Alarm | Benachrichtigung im Web-Dashboard | Muss |
| F-053 | Buzzer | Akustische Alarmierung | Kann |

---

## 3. Nicht-funktionale Anforderungen

### 3.1 Technische Anforderungen

| ID | Anforderung | Beschreibung | Priorität |
|----|-------------|-------------|-----------|
| NF-001 | Open-Source | Keine Lizenzkosten durch Open-Source-Technologien | Muss |
| NF-002 | Cloud-Unabhängigkeit | Keine Abhängigkeit von externen Cloud-Diensten | Muss |
| NF-003 | MQTT-Protokoll | Kommunikation über MQTT | Muss |
| NF-004 | ESP32-S3 | Mikrocontroller ESP32-S3 | Muss |
| NF-005 | Raspberry Pi | Zentrale Verarbeitungseinheit | Muss |

### 3.2 Qualitätsanforderungen

| ID | Anforderung | Beschreibung | Priorität |
|----|-------------|-------------|-----------|
| NF-010 | Zuverlässigkeit | 24/7 Betrieb ohne Ausfall | Muss |
| NF-011 | Reaktionszeit | Alarmierung innerhalb von 5 Sekunden | Muss |
| NF-012 | Datenbank-Performance | Echtzeit-Abfragen ohne Verzögerung | Muss |
| NF-013 | Dokumentation | Vollständige IHK-Dokumentation | Muss |

---

## 4. Projektabgrenzung

### 4.1 Nicht im Projektumfang

- Bauliche Maßnahmen oder Kabelverlegung
- Zertifizierung als Brandmeldeanlage nach VdS-Richtlinien
- Hardware-Beschaffung (wird vom Auftraggeber gestellt)

---

## 5. Lieferumfang

1. **Firmware:** ESP32-S3 C++-Quellcode mit PlatformIO
2. **Backend:** Python-Anwendung (FastAPI oder Flask)
3. **Frontend:** SPA mit JavaScript ES6+ und Tailwind CSS
4. **Datenbank:** MariaDB-Schema
5. **Dokumentation:**
   - Lastenheft (dieses Dokument)
   - Pflichtenheft
   - UML-Diagramme (Klassendiagramm, Sequenzdiagramm)
   - ER-Diagramm
   - IHK-Bericht

---

## 6. Projektphasen

| Phase | Beschreibung | Stunden |
|-------|-------------|---------|
| I | Analyse und Definition | 8 |
| II | Planung und Entwurf | 12 |
| III | Implementierung | 37 |
| IV | Qualitätssicherung und Test | 8 |
| V | Abschluss und Dokumentation | 15 |
| **Gesamt** | | **80** |

---

## 7. Annahmen und Abhängigkeiten

- Der Auftraggeber stellt folgende Hardware bereit:
  - ESP32-S3-Mikrocontroller
  - Raspberry Pi
  - Sensoren (DHT22/DS18B20, MQ-2, MQ-135, PIR)
- MQTT-Broker (Mosquitto) wird lokal betrieben
- MariaDB wird auf dem Raspberry Pi gehostet
- Zugriff auf das lokale Netzwerk ist gegeben

---

## 8. Genehmigung

| Rolle | Name | Datum | Unterschrift |
|-------|------|-------|--------------|
| Auftraggeber | Herr Niklas | | |
| Prüfungsteilnehmer | Marc-Dennis Haberald | | |
