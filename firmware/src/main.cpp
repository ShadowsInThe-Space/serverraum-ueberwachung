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
 * Sensoren: DHT22, MQ-2, MQ-135, PIR
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
#include "sensors/DHT22Sensor.h"
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

// GPIO-Pin Belegung (laut Tech-Specs!)
const int PIN_DHT22 = 5;       // GPIO 5: DHT22 (Temperatur/Feuchte)
const int PIN_MQ2 = 1;         // GPIO 1: MQ-2 (Rauchgas) - ADC1 Kanal 0
const int PIN_MQ135 = 2;       // GPIO 2: MQ-135 (Luftqualität) - ADC1 Kanal 1
const int PIN_PIR = 6;         // GPIO 6: PIR (Bewegung)
const int PIN_LED = 7;         // GPIO 7: Warn-LED
const int PIN_BUZZER = 8;      // GPIO 8: Buzzer

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

// Direkter Zeiger auf DHT22 für Display-Aktualisierung
DHT22Sensor* dht22Sensor = nullptr;

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

    // --- DHT22 Sensor (Temperatur + Feuchte) ---
    // Misst Temperatur und Luftfeuchtigkeit
    // Pin: GPIO 5 (laut Tech-Specs)
    auto dht22 = new DHT22Sensor(PIN_DHT22, "temp_serverraum", 5000);
    dht22Sensor = dht22;  // Globalen Zeiger speichern für Display-Zugriff
    sensorManager->sensorHinzufuegen(dht22);

    // --- MQ-2 Sensor (Rauchgas) ---
    // Analog-Sensor für Rauch und brennbare Gase
    // Pin: GPIO 1 (ADC1 Kanal 0)
    auto mq2 = new MQ2Sensor(PIN_MQ2, "rauchgas", 5000);
    mq2->setzeSchwellwert(200.0f);  // Alarm bei 200 ppm
    sensorManager->sensorHinzufuegen(mq2);

    // --- MQ-135 Sensor (Luftqualität) ---
    // Analog-Sensor für CO2-Äquivalent und Luftschadstoffe
    // Pin: GPIO 2 (ADC1 Kanal 1)
    auto mq135 = new MQ135Sensor(PIN_MQ135, "luftqualitaet", 5000);
    mq135->setzeSchwellwert(800.0f);  // Alarm bei 800 ppm
    sensorManager->sensorHinzufuegen(mq135);

    // --- PIR Sensor (Bewegung) ---
    // Digitaler Bewegungsmelder
    // Pin: GPIO 6
    auto pir = new PIRSensor(PIN_PIR, "bewegung", 1000);
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
    displayManager = new DisplayManager();
    displayManager->init();
    displayManager->aktualisiereTemperatur(0.0f, 30.0f);
    displayManager->aktualisiereStatus("Starte...");

    // Kurze Pause damit Display/TFT bereit ist
    delay(500);

    // WLAN Event Handler registrieren
    WiFi.onEvent(wifiEventCallback);

    // Verbinde mit WLAN
    verbindeWLAN();

    // Verbinde mit MQTT Broker
    verbindeMQTT();

    // Setze MQTT Callback für empfangene Nachrichten
    mqttClient.setCallback(mqttCallback);

    // Initialisiere Sensoren
    initialisiereSensoren();

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
            if (displayManager != nullptr && dht22Sensor != nullptr)
            {
                // Letzten DHT22-Messwert holen (wird vom sensorManager->loop() aktualisiert)
                SensorMesswert messwert = dht22Sensor->getMesswert();

                // Nur anzeigen wenn Messung gültig war
                if (messwert.status == SensorStatus::OK)
                {
                    // Temperaturanzeige aktualisieren (Schwellwert: 30°C)
                    // Bei > 30°C → roter Alarm, darunter → grüner Normalbetrieb
                    displayManager->aktualisiereTemperatur(messwert.wert, 30.0f);

                    // MQTT-Status in der Statusleiste
                    String statusText = String(messwert.wert, 1) + "C | MQTT OK";
                    displayManager->aktualisiereStatus(statusText.c_str());
                }
                else
                {
                    displayManager->aktualisiereStatus("Sensor liest...");
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
