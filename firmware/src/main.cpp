/**
 * @file main.cpp
 * @brief Serverraum-Überwachung ESP32-S3 Firmware
 *
 * @author Marc-Dennis Haberland
 * @date 16.03.2026
 *
 * Hardware:
 * - DS18B20: GPIO 4 (Temperatur)
 * - PIR: GPIO 21 (Bewegung)
 * - MQ-2: GPIO 1 (Rauchgas)
 * - SHT31: GPIO 9/6 (Temperatur + Feuchte)
 * - RGB LED: GPIO 15/7/16 (Rot/Grün/Blau)
 * - Buzzer: GPIO 17
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "config.h"
#include "sensors/SensorManager.h"
#include "sensors/DS18B20Sensor.h"
#include "sensors/PIRSensor.h"
#include "sensors/MQ2Sensor.h"
#include "sensors/SHT31Sensor.h"

// Pin-Definitionen
#define PIN_DS18B20 4
#define PIN_PIR 21
#define PIN_MQ2 1
#define PIN_SHT31_SCL 9
#define PIN_SHT31_SDA 6
#define PIN_LED_R 15
#define PIN_LED_G 7
#define PIN_LED_B 16
#define PIN_BUZZER 17

// Timing
#define HEARTBEAT_INTERVAL 60000UL

// Globale Variablen
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
SensorManager* sensorManager = nullptr;
DS18B20Sensor* ds18b20Sensor = nullptr;
SHT31Sensor* sht31Sensor = nullptr;

// =============================================================================
// HILFSFUNKTIONEN
// =============================================================================

void setLed(bool r, bool g, bool b) {
    digitalWrite(PIN_LED_R, r ? HIGH : LOW);
    digitalWrite(PIN_LED_G, g ? HIGH : LOW);
    digitalWrite(PIN_LED_B, b ? HIGH : LOW);
}

void zeigeAlarm(int typ) {
    // 0=Aus, 1=Info(Blau), 2=Warnung(Gelb), 3=Kritisch(Rot), 4=OK(Gruen)
    switch (typ) {
        case 0: setLed(false, false, false); digitalWrite(PIN_BUZZER, LOW); break;
        case 1: setLed(false, false, true); break;
        case 2: setLed(true, true, false); break;
        case 3: setLed(true, false, false); tone(PIN_BUZZER, 1000, 200); break;
        case 4: setLed(false, true, false); digitalWrite(PIN_BUZZER, LOW); break;
    }
}

void initGPIO() {
    pinMode(PIN_LED_R, OUTPUT);
    pinMode(PIN_LED_G, OUTPUT);
    pinMode(PIN_LED_B, OUTPUT);
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_LED_R, LOW);
    digitalWrite(PIN_LED_G, LOW);
    digitalWrite(PIN_LED_B, LOW);
    digitalWrite(PIN_BUZZER, LOW);
}

void verbindeWLAN() {
    Serial.printf("\nVerbinde mit WLAN: %s\n", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.printf("\nWLAN verbunden! IP: %s\n", WiFi.localIP().toString().c_str());
}

void verbindeMQTT() {
    Serial.printf("Verbinde MQTT: %s:%d\n", MQTT_BROKER, MQTT_PORT);
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    while (!mqttClient.connect(MQTT_CLIENT_ID)) {
        Serial.printf("MQTT Fehler (rc=%d), retry in 5s...\n", mqttClient.state());
        delay(5000);
    }
    Serial.println("MQTT verbunden!");
}

void initSensoren() {
    Serial.println("\n=== Sensoren initialisieren ===");

    sensorManager = new SensorManager(mqttClient, MQTT_TOPIC_BASE);

    ds18b20Sensor = new DS18B20Sensor(PIN_DS18B20, "temp_serverraum", 10000);
    sensorManager->sensorHinzufuegen(ds18b20Sensor);

    auto pirSensor = new PIRSensor(PIN_PIR, "bewegung", 10000);
    sensorManager->sensorHinzufuegen(pirSensor);

    auto mq2Sensor = new MQ2Sensor(PIN_MQ2, "rauchgas", 10000);
    mq2Sensor->setzeSchwellwert(200.0f);
    sensorManager->sensorHinzufuegen(mq2Sensor);

    sht31Sensor = new SHT31Sensor(PIN_SHT31_SCL, PIN_SHT31_SDA, "temp_sht31", 10000);
    sensorManager->sensorHinzufuegen(sht31Sensor);

    sensorManager->init();
    Serial.printf("\n%d Sensoren aktiv\n", sensorManager->getAnzahlSensoren());
}

void scanneI2C() {
    Wire.begin(PIN_SHT31_SDA, PIN_SHT31_SCL);
    Serial.println("\nI2C Scan:");
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf("  Gerät: 0x%02X\n", addr);
        }
    }
}

// =============================================================================
// ALARM LOGIK
// =============================================================================

float letzteTemperatur = 0;

void aktualisiereAlarmStatus() {
    if (ds18b20Sensor == nullptr) return;

    float temp = ds18b20Sensor->getMesswert().wert;

    if (temp >= 28.0f) {
        zeigeAlarm(3);
    } else if (temp >= 22.1f) {
        zeigeAlarm(2);
    } else if (temp > 0 && temp < 22.1f) {
        zeigeAlarm(4);
    } else {
        zeigeAlarm(0);
    }
}

// =============================================================================
// ARDUINO SETUP
// =============================================================================

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n╔════════════════════════════════════════╗");
    Serial.println("║   Serverraum-Überwachung ESP32-S3   ║");
    Serial.println("╚════════════════════════════════════════╝\n");

    initGPIO();
    verbindeWLAN();
    verbindeMQTT();
    scanneI2C();
    initSensoren();

    Serial.println("\n=== System bereit! ===\n");
    Serial.printf("LED: GPIO %d/%d/%d | Buzzer: GPIO %d\n", PIN_LED_R, PIN_LED_G, PIN_LED_B, PIN_BUZZER);
}

// =============================================================================
// ARDUINO LOOP
// =============================================================================

unsigned long letzterHeartbeat = 0;
unsigned long letzterFeuchteSenden = 0;
unsigned long letzterAlarmCheck = 0;

void loop() {
    // WLAN + MQTT prüfen
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WLAN verloren!");
        verbindeWLAN();
    }
    if (!mqttClient.connected()) {
        Serial.println("MQTT verloren!");
        verbindeMQTT();
    }
    mqttClient.loop();

    // Sensoren verarbeiten
    if (sensorManager != nullptr) {
        sensorManager->loop();

        // Feuchtigkeit senden (SHT31)
        if (sht31Sensor != nullptr && millis() - letzterFeuchteSenden >= 10000) {
            float feucht = sht31Sensor->getLuftfeuchtigkeit();
            if (feucht > 0) {
                JsonDocument doc;
                doc["sensor_id"] = "feuchte_sht31";
                doc["sensor_typ"] = "SHT31";
                doc["wert"] = feucht;
                doc["status"] = "OK";

                char buffer[256];
                serializeJson(doc, buffer);
                String topic = String(MQTT_TOPIC_BASE) + "/feuchte_sht31";
                mqttClient.publish(topic.c_str(), buffer);
            }
            letzterFeuchteSenden = millis();
        }

        // Alarm-Status aktualisieren (alle 5s)
        if (millis() - letzterAlarmCheck >= 5000) {
            aktualisiereAlarmStatus();
            letzterAlarmCheck = millis();
        }
    }

    // Heartbeat (alle 60s)
    if (millis() - letzterHeartbeat >= HEARTBEAT_INTERVAL) {
        if (sensorManager != nullptr) {
            sensorManager->sendeHeartbeat();
        }
        letzterHeartbeat = millis();
        Serial.printf("[Heartbeat] Uptime: %lu s\n", millis() / 1000);
    }

    delay(10);
}
