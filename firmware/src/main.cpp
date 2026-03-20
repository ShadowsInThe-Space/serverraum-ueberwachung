/**
 * @file main.cpp
 * @brief Hauptprogramm für Serverraum-Überwachung mit ESP32-S3
 * @details Implementiert WLAN/MQTT-Kommunikation und Sensor-Messungen.
 *          Verwendet DS18B20 Temperatursensor und PIR-Bewegungssensor.
 *
 * @author Marc-Dennis Haberland
 * @date 16.03.2026
 * @version 2.0
 *
 * Hardware:
 * - DS18B20 Temperatursensor an GPIO 5 (1-Wire Bus)
 * - PIR Bewegungssensor an GPIO 21
 *
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "config.h"  // WLAN- und MQTT-Konfiguration
#include "sensors/SensorManager.h"
#include "sensors/DS18B20Sensor.h"
#include "sensors/PIRSensor.h"
#include "sensors/MQ2Sensor.h"
#include "sensors/SHT31Sensor.h"

// ============================================================================
// PIN-KONFIGURATION
// ============================================================================

// GPIO-Pin Belegung
const int PIN_DS18B20 = 4;    // GPIO 4: DS18B20 (1-Wire Bus)
const int PIN_PIR = 21;       // GPIO 21: PIR (Bewegungsmelder)
const int PIN_MQ2 = 1;        // GPIO 1: MQ-2 (Rauchgas) - ADC1 Kanal 0
const int PIN_SHT31_SCL = 8;  // GPIO 8: SHT31 I2C SCL
const int PIN_SHT31_SDA = 9;  // GPIO 9: SHT31 I2C SDA

// RGB LED Pins (Alarm-Anzeige) - getauscht für bessere Farben
const int PIN_LED_ROT = 15;   // GPIO 15: Rote LED
const int PIN_LED_GRUEN = 7;  // GPIO 7: Grüne LED
const int PIN_LED_BLAU = 16;  // GPIO 16: Blaue LED

// Buzzer Pin
const int PIN_BUZZER = 17;    // GPIO 17: Buzzer

// Timing
const unsigned long HEARTBEAT_INTERVAL = 60000;  // Heartbeat alle 60 Sekunden

// ============================================================================
// GLOBALE VARIABLEN
// ============================================================================

// WiFi Client für MQTT
WiFiClient wifiClient;

// MQTT Client
PubSubClient mqttClient(wifiClient);

// Sensor Manager - verwaltet alle Sensoren
SensorManager* sensorManager = nullptr;

// DS18B20 Sensor Zeiger für direkten Zugriff
DS18B20Sensor* ds18b20Sensor = nullptr;

// SHT31 Sensor Zeiger für direkten Zugriff
SHT31Sensor* sht31Sensor = nullptr;

// Timer für Heartbeat
unsigned long letzterHeartbeat = 0;

// Timer für Sensor-Messungen
unsigned long letzterSensorUpdate = 0;

// ============================================================================
// RGB LED ALARM-FUNKTIONEN
// ============================================================================

/**
 * @brief Initialisiert die RGB LED Pins
 */
void initialisiereRGBLED()
{
    pinMode(PIN_LED_ROT, OUTPUT);
    pinMode(PIN_LED_GRUEN, OUTPUT);
    pinMode(PIN_LED_BLAU, OUTPUT);

    // Alle LEDs aus
    digitalWrite(PIN_LED_ROT, LOW);
    digitalWrite(PIN_LED_GRUEN, LOW);
    digitalWrite(PIN_LED_BLAU, LOW);

    Serial.println("[LED] RGB LED initialisiert an GPIO 7/15/16");
}

/**
 * @brief Setzt LED-Farbe
 * @param rot HIGH/LOW
 * @param gruen HIGH/LOW
 * @param blau HIGH/LOW
 */
void setzeLED(bool rot, bool gruen, bool blau)
{
    digitalWrite(PIN_LED_ROT, rot ? HIGH : LOW);
    digitalWrite(PIN_LED_GRUEN, gruen ? HIGH : LOW);
    digitalWrite(PIN_LED_BLAU, blau ? HIGH : LOW);
}

/**
 * @brief Zeigt Alarm-Status an
 * @param alarmTyp: 0=Aus, 1=Info, 2=Warnung, 3=Kritisch
 */
void zeigeAlarmStatus(int alarmTyp)
{
    switch (alarmTyp)
    {
        case 0: // Aus
            setzeLED(false, false, false);
            digitalWrite(PIN_BUZZER, LOW);
            break;
        case 1: // Info (Blau)
            setzeLED(false, false, true);
            break;
        case 2: // Warnung (Gelb = Rot+Grün)
            setzeLED(true, true, false);
            break;
        case 3: // Kritisch (Rot) - mit Ton
            setzeLED(true, false, false);
            // Piepton bei kritisch
            tone(PIN_BUZZER, 1000, 200);
            break;
        case 4: // OK (Grün)
            setzeLED(false, true, false);
            digitalWrite(PIN_BUZZER, LOW);
            break;
    }
}

/**
 * @brief Initialisiert den Buzzer
 */
void initialisiereBuzzer()
{
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_BUZZER, LOW);
    Serial.println("[Buzzer] initialisiert an GPIO " + String(PIN_BUZZER));
}

// ============================================================================
// FUNKTIONEN
// ============================================================================

/**
 * @brief Verbindet mit WLAN
 * @details Initialisiert WLAN und wartet bis Verbindung steht.
 */
void verbindeWLAN()
{
    Serial.println("\n=== WLAN Verbindung ===");

    // WLAN starten
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    // Auf Verbindung warten
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }

    // Verbindung erfolgreich
    Serial.println("\nWLAN verbunden!");
    Serial.printf("IP-Adresse: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("Signalstärke: %d dBm\n", WiFi.RSSI());
}

/**
 * @brief Verbindet mit MQTT Broker
 * @details Stellt Verbindung zum MQTT-Broker her.
 */
void verbindeMQTT()
{
    Serial.println("\n=== MQTT Verbindung ===");

    // MQTT Server setzen
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

    // Verbindungsversuch
    while (!mqttClient.connected())
    {
        Serial.print("Verbinde mit MQTT Broker " + String(MQTT_BROKER) + "...");

        if (mqttClient.connect(MQTT_CLIENT_ID))
        {
            Serial.println(" OK!");
        }
        else
        {
            Serial.printf(" Fehler (rc=%d), versuche erneut in 5 Sekunden...\n",
                         mqttClient.state());
            delay(5000);
        }
    }
}

/**
 * @brief Callback für MQTT-Nachrichten
 * @details Wird aufgerufen wenn Nachricht empfangen wird.
 */
void mqttCallback(char* topic, byte* payload, unsigned int length)
{
    Serial.printf("[MQTT] Nachricht empfangen auf Topic: %s\n", topic);

    // Payload null-terminieren
    payload[length] = '\0';
    String nachricht = String((char*)payload);

    Serial.printf("Inhalt: %s\n", nachricht.c_str());
}

/**
 * @brief Globaler I2C-Scan beim Boot
 */
void scanneI2CBus()
{
    delay(500);  // Warte bis Serielle bereit
    Serial.println("\n=== GLOBALER I2C SCAN ===");
    Wire.begin(PIN_SHT31_SDA, PIN_SHT31_SCL);
    Wire.setClock(100000);
    delay(100);

    int gefunden = 0;
    for (uint8_t addr = 1; addr < 127; addr++)
    {
        Wire.beginTransmission(addr);
        uint8_t error = Wire.endTransmission();
        if (error == 0)
        {
            Serial.printf(">>> I2C Gerät gefunden: 0x%02X\n", addr);
            gefunden++;
        }
    }
    Serial.printf("I2C-Scan beendet: %d Geräte gefunden\n\n", gefunden);
}

/**
 * @brief Initialisiert alle Sensoren
 * @details Erstellt Sensor-Objekte und fügt sie dem Manager hinzu.
 */
void initialisiereSensoren()
{
    Serial.println("\n=== Sensoren initialisieren ===");

    // Sensor Manager erstellen
    sensorManager = new SensorManager(mqttClient, MQTT_TOPIC_BASE);

    // --- DS18B20 Sensor (Temperatur) ---
    // Pin: GPIO 5 (1-Wire Bus)
    // Messintervall: 10000ms (10 Sekunden)
    ds18b20Sensor = new DS18B20Sensor(PIN_DS18B20, "temp_serverraum", 10000);
    sensorManager->sensorHinzufuegen(ds18b20Sensor);

    // --- PIR Sensor (Bewegung) ---
    // Pin: GPIO 21
    // Messintervall: 10000ms (10 Sekunden)
    auto pirSensor = new PIRSensor(PIN_PIR, "bewegung", 10000);
    sensorManager->sensorHinzufuegen(pirSensor);

    // --- MQ-2 Sensor (Rauchgas) ---
    // Pin: GPIO 1 (ADC1 Kanal 0)
    // Messintervall: 10000ms (10 Sekunden)
    auto mq2Sensor = new MQ2Sensor(PIN_MQ2, "rauchgas", 10000);
    mq2Sensor->setzeSchwellwert(200.0f);  // Alarm bei 200 ppm
    sensorManager->sensorHinzufuegen(mq2Sensor);

    // --- SHT31 Sensor (Temperatur + Feuchtigkeit) ---
    // Pins: GPIO 8 (SCL), GPIO 9 (SDA)
    // Messintervall: 10000ms (10 Sekunden)
    sht31Sensor = new SHT31Sensor(PIN_SHT31_SCL, PIN_SHT31_SDA, "temp_sht31", 10000);
    sensorManager->sensorHinzufuegen(sht31Sensor);

    // Alle Sensoren initialisieren
    sensorManager->init();

    Serial.printf("\n=== %d Sensoren initialisiert ===\n\n",
                 sensorManager->getAnzahlSensoren());
}

/**
 * @brief WLAN-Event-Handler
 * @details Behandelt WLAN-Verbindungsereignisse.
 */
void wifiEventCallback(WiFiEvent_t event)
{
    switch (event)
    {
        case ARDUINO_EVENT_WIFI_STA_START:
            Serial.println("[WLAN] Station gestartet");
            break;
        case ARDUINO_EVENT_WIFI_STA_CONNECTED:
            Serial.println("[WLAN] Verbunden mit AP");
            break;
        case ARDUINO_EVENT_WIFI_STA_GOT_IP:
            Serial.printf("[WLAN] IP erhalten: %s\n",
                        WiFi.localIP().toString().c_str());
            break;
        case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
            Serial.println("[WLAN] Verbindung verloren - versuche neu...");
            WiFi.reconnect();
            break;
        default:
            break;
    }
}

// ============================================================================
// ARDUINO HAUPTFUNKTIONEN
// ============================================================================

/**
 * @brief Arduino Setup-Funktion
 * @details Wird einmalig beim Start aufgerufen.
 */
void setup()
{
    // Serielle Kommunikation starten
    Serial.begin(115200);
    delay(1000);

    // Willkommensnachricht
    Serial.println("\n\n");
    Serial.println("╔═══════════════════════════════════════════════════════╗");
    Serial.println("║   SERVERRAUM-ÜBERWACHUNG - ESP32-S3 Firmware        ║");
    Serial.println("║   Version 2.1 | Alle Sensoren aktiv             ║");
    Serial.println("╚═══════════════════════════════════════════════════════╝\n");

    // WLAN Event Handler registrieren
    WiFi.onEvent(wifiEventCallback);

    // Mit WLAN verbinden
    verbindeWLAN();

    // Mit MQTT verbinden
    verbindeMQTT();

    // MQTT Callback setzen
    mqttClient.setCallback(mqttCallback);

    // I2C Bus scannen
    scanneI2CBus();

    // Sensoren initialisieren
    initialisiereSensoren();

    // RGB LED initialisieren
    initialisiereRGBLED();
    initialisiereBuzzer();

    // Heartbeat Timer initialisieren
    letzterHeartbeat = millis();
    letzterSensorUpdate = millis();

    Serial.println("\n=== System bereit! ===\n");
    Serial.println("Sensoren:");
    Serial.printf("  - DS18B20: GPIO %d (Temperatur)\n", PIN_DS18B20);
    Serial.printf("  - SHT31: GPIO %d/%d (Temperatur + Feuchtigkeit)\n", PIN_SHT31_SCL, PIN_SHT31_SDA);
    Serial.printf("  - PIR: GPIO %d (Bewegung)\n", PIN_PIR);
    Serial.printf("  - MQ-2: GPIO %d (Rauchgas)\n", PIN_MQ2);
    Serial.printf("  - RGB LED: GPIO %d/%d/%d (Rot/Grün/Blau)\n", PIN_LED_ROT, PIN_LED_GRUEN, PIN_LED_BLAU);
    Serial.printf("  - Buzzer: GPIO %d\n", PIN_BUZZER);
    Serial.println("\nMQTT Topics:");
    Serial.printf("  - Basis: %s\n", MQTT_TOPIC_BASE);
}

/**
 * @brief Arduino Loop-Funktion
 * @details Wird kontinuierlich aufgerufen.
 */
void loop()
{
    // WLAN-Verbindung prüfen
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("[WLAN] Verbindung verloren!");
        verbindeWLAN();
    }

    // MQTT-Verbindung prüfen
    if (!mqttClient.connected())
    {
        Serial.println("[MQTT] Verbindung verloren!");
        verbindeMQTT();
    }

    // MQTT keep-alive
    mqttClient.loop();

    // Sensoren abfragen und Daten senden
    if (sensorManager != nullptr)
    {
        sensorManager->loop();

        // Einfache Alarm-Logik basierend auf Temperatur
        // Diese kann spter vom Backend per MQTT überschrieben werden
        static float letzteTemperatur = 0;
        static unsigned long letzterAlarmCheck = 0;

        if (millis() - letzterAlarmCheck >= 5000)  // Alle 5 Sekunden
        {
            // Aktuellen Messwert holen
            if (ds18b20Sensor != nullptr)
            {
                float temp = ds18b20Sensor->getMesswert().wert;
                Serial.printf("[ALARM] Temperatur: %.2f°C\n", temp);
                letzteTemperatur = temp;
            }
            else
            {
                Serial.println("[ALARM] Kein DS18B20 Sensor!");
            }

            // Alarm-Status setzen (neue Schwellwerte)
            // < 22°C: Grün (OK)
            // 22.1 - 27.9°C: Gelb (Warnung)
            // >= 28°C: Rot + Buzzer (Kritisch)
            if (letzteTemperatur >= 28.0f)
            {
                // Kritisch: Rot + Buzzer
                zeigeAlarmStatus(3);
                Serial.printf("[ALARM] Kritisch: %.1f°C\n", letzteTemperatur);
            }
            else if (letzteTemperatur >= 22.1f)
            {
                // Warnung: Gelb
                zeigeAlarmStatus(2);
                Serial.printf("[ALARM] Warnung: %.1f°C\n", letzteTemperatur);
            }
            else if (letzteTemperatur > 0 && letzteTemperatur < 22.1f)
            {
                // OK: Grün
                zeigeAlarmStatus(4);
            }
            else
            {
                // Unbekannt: Aus
                zeigeAlarmStatus(0);
            }

            letzterAlarmCheck = millis();
        }
    }

    // Heartbeat senden (alle 60 Sekunden)
    if (millis() - letzterHeartbeat >= HEARTBEAT_INTERVAL)
    {
        if (sensorManager != nullptr)
        {
            sensorManager->sendeHeartbeat();
        }
        letzterHeartbeat = millis();
        Serial.printf("[Heartbeat] Uptime: %lu Sekunden\n", millis() / 1000);
    }

    // Kurze Pause um ESP32 nicht zu überlasten
    delay(10);
}
