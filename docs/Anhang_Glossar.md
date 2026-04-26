# Glossar – Serverraum-Überwachung

## A

**API (Application Programming Interface)**
Schnittstelle, über die Software-Komponenten miteinander kommunizieren. In diesem Projekt: REST-API des Backends.

**Arduino**
Open-Source-Mikrocontroller-Plattform. ESP32 basiert auf Arduino-Konzept.

---

## B

**Backend**
Serverseitige Software, die Daten verarbeitet und die API bereitstellt. Hier: Python/FastAPI auf Raspberry Pi.

**Broadcast**
Nachricht, die an alle Teilnehmer im Netzwerk gesendet wird.

---

## C

**CSV (Comma-Separated Values)**
Dateiformat zum Speichern tabellarischer Daten.

---

## D

**Dashboard**
Web-basierte Benutzeroberfläche zur Anzeige und Steuerung des Systems.

**DNS (Domain Name System)**
Übersetzt Domainnamen in IP-Adressen (z.B. serverraum.local → 192.168.1.100).

**Docker**
Container-Technologie zur einfachen Bereitstellung von Anwendungen.

---

## E

**ESP32**
Kleiner Mikrocontroller mit WiFi. Hier: ESP32-S3 als zentrale Steuereinheit.

**ESP32-S3**
Neuere Variante des ESP32 mit verbesserten Sicherheitsfunktionen.

**Ethernet**
Kabelgebundenes Netzwerk (RJ45-Anschluss).

---

## F

**FastAPI**
Modernes Python-Framework für REST-APIs. Schnell, typsicher, automatisch dokumentiert.

**Firmware**
Software, die auf Mikrocontrollern läuft (hier: ESP32).

**Firewall**
System zum Schutz vor unbefugtem Netzwerkzugriff.

---

## G

**Grenzwert (Threshold)**
Definierter Minimal- oder Maximalwert. Wird ein Grenzwert überschritten, löst das System einen Alarm aus.

**GPIO (General Purpose Input/Output)**
Frei programmierbare Anschlüsse am Mikrocontroller für Sensoren/Aktoren.

---

## H

**HTTP (Hypertext Transfer Protocol)**
Protokoll für Datenübertragung im Web.

**HTML (HyperText Markup Language)**
Sprache zur Strukturierung von Webseiten.

---

## I

**I2C (Inter-Integrated Circuit)**
Serielles Bus-System zur Kommunikation zwischen Mikrocontrollern und Sensoren.

**IoT (Internet of Things)**
Netzwerk aus physischen Geräten mit eingebetteter Elektronik, die Daten austauschen.

---

## J

**JSON (JavaScript Object Notation)**
Leichtgewichtiges Datenformat für Datenaustausch zwischen Client und Server.

---

## L

**LED (Light Emitting Diode)**
Leuchtdiode. Hier als Alarm-Indikator verwendet.

---

## M

**MariaDB**
Open-Source-Datenbanksystem. Fork von MySQL.

**Mikrocontroller**
Kleiner Computer auf einem Chip. Verarbeitet Sensor-Daten und steuert Aktoren.

**MQTT (Message Queuing Telemetry Transport)**
Leichtgewichtiges Protokoll für IoT-Geräte. Publisher/Subscriber-Modell.

**MySQL**
Beliebtes relationales Datenbanksystem.

---

## N

**NAS (Network Attached Storage)**
Netzwerkspeicher für zentrale Datenhaltung.

**NGINX**
Webserver und Reverse Proxy.

---

## O

**OneWire**
Bus-System für Kommunikation mit Temperatursensoren (z.B. DS18B20).

---

## P

**PIN (Personal Identification Number)**
Nicht verwendet. Gemeint ist hier: GPIO-Pin.

**Polling**
Wiederholtes Abfragen von Daten in regelmäßigen Intervallen.

**Protocol**
Definiertes Regelwerk für die Kommunikation zwischen Geräten.

**Pub/Sub (Publish/Subscribe)**
Kommunikationsmuster: Sender (Publisher) senden Nachrichten an Topics; Empfänger (Subscriber) erhalten alle Nachrichten dieser Topics.

**PUT**
HTTP-Methode zum Aktualisieren von Daten.

---

## R

**REST (Representational State Transfer)**
Architekturstil für Web-APIs. Verwendet HTTP-Methoden (GET, POST, PUT, DELETE).

**RJ45**
Standard-Netzwerkanschluss (Ethernet).

---

## S

**Sensor**
Messgerät zur Erfassung physikalischer Größen (Temperatur, Feuchtigkeit, etc.).

**SMTPS (Simple Mail Transfer Protocol Secure)**
Verschlüsselte Variante von SMTP für E-Mail-Versand.

**SPL (Structured Programming Language)**
C-Bibliothek für ESP32.

**SQL (Structured Query Language)**
Sprache für Datenbankabfragen.

**Subscriber**
Empfänger, der MQTT-Nachrichten eines bestimmten Topics empfängt.

---

## T

**TCP (Transmission Control Protocol)**
Zuverlässiges Transportprotokoll im Internet.

**TLS (Transport Layer Security)**
Verschlüsselungsprotokoll für sichere Datenübertragung.

**Topic**
Kanal in MQTT, an dem Nachrichten veröffentlicht werden (z.B. "sensor/temperature/1").

---

## U

**URI (Uniform Resource Identifier)**
Adresse einer Ressource im Web.

**URL (Uniform Resource Locator)**
Vollständige Adresse einer Webressource.

**USB (Universal Serial Bus)**
Standard-Schnittstelle für Datenübertragung.

---

## V

**Virtualenv**
Python-Tool zur Isolation von Projektabhängigkeiten.

---

## W

**WiFi**
Drahtloses Netzwerkprotokoll.

**Wire**
Englisch für "Draht" oder "Kabel".

---

## Definitionen (alphabetisch)

| Begriff | Definition |
|---------|------------|
| Alarm | Systemmeldung bei Überschreitung von Grenzwerten |
| AlarmEngine | Software-Komponente zur Alarmverwaltung |
| Broker | Server, der MQTT-Nachrichten vermittelt |
| Datenbank | Strukturierte Sammlung von Daten |
|ESP32 | Mikrocontroller mit WiFi |
| Frontend | Client-seitige Anwendung (Dashboard) |
| GPIO | Anschlüsse am Mikrocontroller |
| Grenzwert | Schwellwert für Alarm-Auslösung |
| Hardware | Physikalische Komponenten |
| IoT | Internet of Things – vernetzte Geräte |
| JSON | Datenformat für API-Kommunikation |
| MariaDB | Datenbanksystem |
| Messwert | Einzelne Sensormessung |
| MQTT | Protokoll für IoT-Datenübertragung |
| Pin | Anschluss am Mikrocontroller |
| Publish | Nachricht senden (MQTT) |
| Raspberry Pi | Kleincomputer als Server |
| REST-API | Programmierschnittstelle |
| Sensor | Messgerät |
| Subscribe | Nachrichten empfangen (MQTT) |
| Temperatursensor | Sensor zur Messung der Temperatur |
