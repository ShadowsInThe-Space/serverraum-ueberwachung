/**
 * @file main.cpp
 * @brief Hauptprogramm für ESP32-S3 Serverraum-Überwachung
 * @details Einstiegspunkt der Firmware.
 *          Initialisiert WLAN, MQTT, Sensoren und führt den Hauptloop aus.
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * @version 1.0
 *
 * Hardware: ESP32-S3-DevKitC-1
 * Sensoren: BME280 (T/Feuchte/Druck), DS18B20, MQ-2, MQ-135, PIR
 * Display: ST7789 170x320
 *
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 * Prüfer: IHK Essen, Mülheim an der Ruhr, Oberhausen
 *
 * ============================================================================
 * TECHNISCHER STACK (laut Projektantrag):
 * - Framework: Arduino (C++)
 * - Kommunikation: MQTT (Mosquitto-Broker)
 * - Datenformat: JSON
 * - OOP: Polymorphie für Sensor-Abstraktion
 * ============================================================================
 */

// ============================================================================
// INCLUDES
// ============================================================================

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Eigene Includes
#include "sensors/Sensor.h"
#include "sensors/SensorData.h"
#include "sensors/BME280Sensor.h"
#include "sensors/DS18B20Sensor.h"
#include "sensors/MQ2Sensor.h"
#include "sensors/MQ135Sensor.h"
#include "sensors/PIRSensor.h"
#include "sensors/SensorManager.h"
#include "DisplayManager.h"
#include "config.h"  // Externe Konfiguration

// ============================================================================
// KONFIGURATION - Aus config.h (nicht hier ändern!)
// ============================================================================

// WLAN: In include/config.h konfigurieren
// MQTT: In include/config.h konfigurieren

// GPIO-Pin Belegung (neu - kollisionsfrei)
// BME280: I2C (SDA=21, SCL=47) - s.u. in BME280Sensor.h
// DS18B20: GPIO 18 (1-Wire Bus)
const int PIN_DS18B20 = 18;   // GPIO 18: DS18B20 (1-Wire Temperatursensor)
const int PIN_MQ2 = 15;        // GPIO 15: MQ-2 (Rauchgas) - ADC
const int PIN_MQ135 = 16;      // GPIO 16: MQ-135 (Luftqualität) - ADC
const int PIN_PIR = 17;        // GPIO 17: PIR (Bewegung)
const int PIN_LED = 45;        // GPIO 45: Warn-LED
const int PIN_BUZZER = 21;     // GPIO 21: Buzzer

// Timing
const unsigned long HEARTBEAT_INTERVAL = 60000;  // Heartbeat alle 60 Sekunden

// ============================================================================
// GLOBALE VARIABLEN
// ============================================================================

// WiFi Client für MQTT
WiFiClient wifiClient;

// MQTT Client (arbeitet mit WiFiClient zusammen)
PubSubClient mqttClient(wifiClient);

// Sensor Manager - verwaltet alle Sensoren!
SensorManager* sensorManager = nullptr;

// Display Manager - verwaltet das TFT Display!
DisplayManager* displayManager = nullptr;

// Direkter Zeiger auf Sensoren für Display-Aktualisierung
BME280Sensor* bme280Sensor = nullptr;
DS18B20Sensor* ds18b20Sensor = nullptr;
MQ2Sensor* mq2Sensor = nullptr;
MQ135Sensor* mq135Sensor = nullptr;
PIRSensor* pirSensor = nullptr;

// Timer für Heartbeat
unsigned long letzterHeartbeat = 0;

// Timer für Display Updates
unsigned long letzterDisplayUpdate = 0;

// ============================================================================
// FUNKTIONEN
// ============================================================================

/**
 * @brief Verbindet mit WLAN
 * @details Initialisiert WLAN und wartet bis Verbindung steht.
 *          Zeigt Fortschritt über Serial an.
 */
void verbindeWLAN()
{
    Serial.println("\n=== WLAN Verbindung ===");

    // Starte WLAN-Verbindung (mit Config-Werten)
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    // Warte auf Verbindung
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
 * @details Stellt Verbindung zum Mosquitto-Broker her.
 *          MQTT ist das Herzstück der Kommunikation!
 *
 * Warum MQTT?
 * - Leichtgewichtig und effizient
 * - Publisher/Subscriber-Modell (asynchron)
 * - QoS (Quality of Service) einstellbar
 * - Ideal für IoT und Sensoren
 */
void verbindeMQTT()
{
    Serial.println("\n=== MQTT Verbindung ===");

    // Setze MQTT Server (mit Config-Werten)
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

    // Subscribe auf Topics falls nötig
    // z.B. für Steuerbefehle vom Backend
    // mqttClient.subscribe("serverraum/steuerung/#");
}

/**
 * @brief Callback für MQTT-Nachrichten
 * @details Wird aufgerufen wenn Nachricht empfangen wird.
 *          Hier können Steuerbefehle vom Backend verarbeitet werden.
 */
void mqttCallback(char* topic, byte* payload, unsigned int length)
{
    Serial.printf("[MQTT] Nachricht empfangen auf Topic: %s\n", topic);

    // Null-terminiere Payload für String-Verarbeitung
    payload[length] = '\0';
    String nachricht = String((char*)payload);

    Serial.printf("Inhalt: %s\n", nachricht.c_str());

    // Beispiel: LED schalten
    // if (String(topic) == "serverraum/steuerung/led")
    // {
    //     if (nachricht == "an")
    //         digitalWrite(PIN_LED, HIGH);
    //     else
    //         digitalWrite(PIN_LED, LOW);
    // }
}

/**
 * @brief Initialisiert alle Sensoren
 * @details Erstellt Sensor-Objekte und fügt sie dem Manager hinzu.
 *
 * Hier zeigt sich unsere OOP-Polymorphie:
 * - Wir erstellen verschiedene Sensor-Typen
 * - Alle werden dem selben Manager hinzugefügt
 * - Der Manager behandelt alle gleich!
 */
void initialisiereSensoren()
{
    Serial.println("\n=== Sensoren initialisieren ===");

    // Erstelle Sensor Manager
    sensorManager = new SensorManager(mqttClient, MQTT_TOPIC_BASE);

    // --- BME280 Sensor (Temperatur + Feuchte + Druck) ---
    // I2C: SDA=GPIO 8, SCL=GPIO 9, Adresse=0x76
    auto bme280 = new BME280Sensor(8, "temp_serverraum", 5000);
    bme280Sensor = bme280;  // Globalen Zeiger speichern für Display-Zugriff
    sensorManager->sensorHinzufuegen(bme280);

    // --- DS18B20 Sensor (Temperatursensor 1-Wire) ---
    // Pin: GPIO 18 (1-Wire Bus)
    auto ds18b20 = new DS18B20Sensor(PIN_DS18B20, "temp_ds18b20", 2000);
    ds18b20Sensor = ds18b20;  // Globalen Zeiger speichern für Display-Zugriff
    sensorManager->sensorHinzufuegen(ds18b20);

    // --- MQ-2 Sensor (Rauchgas) ---
    // Analog-Sensor für Rauch und brennbare Gase
    // Pin: GPIO 15 (ADC)
    auto mq2 = new MQ2Sensor(PIN_MQ2, "rauchgas", 5000);
    mq2->setzeSchwellwert(200.0f);  // Alarm bei 200 ppm
    mq2Sensor = mq2;
    sensorManager->sensorHinzufuegen(mq2);

    // --- MQ-135 Sensor (Luftqualität) ---
    // Analog-Sensor für CO2-Äquivalent und Luftschadstoffe
    // Pin: GPIO 16 (ADC)
    auto mq135 = new MQ135Sensor(PIN_MQ135, "luftqualitaet", 5000);
    mq135->setzeSchwellwert(800.0f);  // Alarm bei 800 ppm
    mq135Sensor = mq135;
    sensorManager->sensorHinzufuegen(mq135);

    // --- PIR Sensor (Bewegung) ---
    // Digitaler Bewegungsmelder
    // Pin: GPIO 17
    auto pir = new PIRSensor(PIN_PIR, "bewegung", 1000);
    pirSensor = pir;
    sensorManager->sensorHinzufuegen(pir);

    // Initialisiere alle Sensoren (polymorph!)
    sensorManager->init();

    Serial.printf("\n=== %d Sensoren initialisiert ===\n\n",
                 sensorManager->getAnzahlSensoren());
}

/**
 * @brief Callback für WLAN-Ereignisse
 * @details Behandelt WLAN-Verbindungsprobleme.
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
 *          Initialisiert Serial, WLAN, MQTT und Sensoren.
 */
void setup()
{
    // Serielle Kommunikation starten (für Debug-Ausgabe)
    Serial.begin(115200);
    delay(1000);

    // Willkommensnachricht
    Serial.println("\n\n");
    Serial.println("╔═══════════════════════════════════════════════════════╗");
    Serial.println("║   SERVERRAUM-ÜBERWACHUNG - ESP32-S3 Firmware        ║");
    Serial.println("║   IHK-Abschlussprojekt | Marc-Dennis Haberland      ║");
    Serial.println("╚═══════════════════════════════════════════════════════╝\n");

    // Display initialisieren (VOR WLAN - wichtig für Stabilität!)
    // Display deaktiviert wegen LVGL/TFT_eSPI Crash - muss separat debuggt werden
    displayManager = nullptr;
    Serial.println("=== Display deaktiviert (Crash-Gefahr) ===");

    // Kurze Pause
    delay(500);

    // === Sensoren INITIALISIEREN (VOR WLAN - für Debug-Ausgabe) ===
    initialisiereSensoren();

    // WLAN Event Handler registrieren
    WiFi.onEvent(wifiEventCallback);

    // Verbinde mit WLAN
    verbindeWLAN();

    // Verbinde mit MQTT Broker
    verbindeMQTT();

    // Setze MQTT Callback für empfangene Nachrichten
    mqttClient.setCallback(mqttCallback);

    // LED und Buzzer als Ausgang konfigurieren
    pinMode(PIN_LED, OUTPUT);
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_LED, LOW);
    digitalWrite(PIN_BUZZER, LOW);

    // Heartbeat Timer initialisieren
    letzterHeartbeat = millis();

    // Display Timer initialisieren
    letzterDisplayUpdate = millis();

    Serial.println("\n=== System bereit! ===\n");
}

/**
 * @brief Arduino Loop-Funktion
 * @details Wird kontinuierlich aufgerufen.
 *          Führt Sensor-Messungen durch und pflegt MQTT-Verbindung.
 */
void loop()
{
    // Prüfe WLAN-Verbindung
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("[WLAN] Verbindung verloren!");
        verbindeWLAN();
    }

    // Prüfe MQTT-Verbindung
    if (!mqttClient.connected())
    {
        Serial.println("[MQTT] Verbindung verloren!");
        verbindeMQTT();
    }

    // Bearbeite MQTT (keep-alive, callbacks)
    mqttClient.loop();

    // Sensoren abfragen und Daten senden
    // Diese Methode prüft intern ob Zeit für neue Messung
    if (sensorManager != nullptr)
    {
        sensorManager->loop();

        // Display aktualisieren (alle 2 Sekunden)
        if (millis() - letzterDisplayUpdate >= 2000)
        {
            if (displayManager != nullptr)
            {
                // DS18B20 Messwert holen (priorisiert)
                float temperatur = 0.0f;
                if (ds18b20Sensor != nullptr)
                {
                    SensorMesswert ds18b20Messwert = ds18b20Sensor->getMesswert();
                    if (ds18b20Messwert.status == SensorStatus::OK)
                    {
                        temperatur = ds18b20Messwert.wert;
                    }
                }

                // Fallback auf BME280 wenn DS18B20 nicht verfügbar
                if (temperatur == 0.0f && bme280Sensor != nullptr)
                {
                    SensorMesswert bmeMesswert = bme280Sensor->getMesswert();
                    if (bmeMesswert.status == SensorStatus::OK)
                    {
                        temperatur = bmeMesswert.wert;
                    }
                }

                // Feuchtigkeit von BME280
                float feuchte = 0.0f;
                if (bme280Sensor != nullptr)
                {
                    feuchte = bme280Sensor->getFeuchtigkeit();
                }

                // MQ2, MQ135 und PIR Werte holen
                float rauch = mq2Sensor ? mq2Sensor->getMesswert().wert : 0.0f;
                float luft = mq135Sensor ? mq135Sensor->getMesswert().wert : 0.0f;
                bool pir = pirSensor ? (pirSensor->getMesswert().wert > 0.5f) : false;

                // Sensor-Status prüfen
                bool sensorOk = (temperatur > 0.0f) || (feuchte > 0.0f);

                // Alle Sensorwerte an DisplayManager übergeben
                if (displayManager != nullptr) {
                    displayManager->aktualisiereAlleWerte(
                        temperatur,    // Temperatur (DS18B20 oder BME280)
                        feuchte,       // Feuchtigkeit (BME280)
                        rauch,        // Rauch (MQ2)
                        luft,         // Luftqualität (MQ135)
                        pir            // Bewegung (PIR)
                    );
                }

                // MQTT-Status in der Statusleiste
                String statusText;
                if (sensorOk)
                {
                    statusText = String(temperatur, 1) + "C | " + String(feuchte, 0) + "% | OK";
                }
                else
                {
                    statusText = "Sensor liest...";
                }
                if (displayManager != nullptr) {
                    displayManager->aktualisiereStatus(statusText.c_str());
                }
            }
            letzterDisplayUpdate = millis();
        }
    }

    // LVGL Timer callback (wichtig für Display!)
    if (displayManager != nullptr)
    {
        displayManager->timerCallback();
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
