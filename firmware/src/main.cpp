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
const int PIN_MQ2 = 4;         // GPIO 4: MQ-2 (Rauchgas) - ADC1 Kanal 3
                               // WICHTIG: GPIO 1 NICHT verwenden -> TFT_RST Hardware-Konflikt!
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
DHT22Sensor* dht22Sensor   = nullptr;

// Zeiger auf alle weiteren Sensoren fuer das Dashboard
MQ2Sensor*   mq2Sensor    = nullptr;
MQ135Sensor* mq135Sensor  = nullptr;
PIRSensor*   pirSensor    = nullptr;

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

    // Warte max. 10 Sekunden auf Verbindung (kein endloser Loop!)
    int versuche = 0;
    while (WiFi.status() != WL_CONNECTED && versuche < 20)
    {
        delay(500);
        Serial.print(".");
        versuche++;
    }

    if (WiFi.status() == WL_CONNECTED)
    {
        Serial.println("\nWLAN verbunden!");
        Serial.printf("IP-Adresse: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("Signalstärke: %d dBm\n", WiFi.RSSI());
    }
    else
    {
        Serial.println("\nWLAN: Kein Netz erreichbar - System laeuft im Offline-Modus!");
    }
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

    // Nur verbinden wenn WLAN verfügbar
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("MQTT: Kein WLAN - uebersprungen.");
        return;
    }

    // Setze MQTT Server (mit Config-Werten)
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

    // Einzelner Verbindungsversuch (max. 5 Sekunden)
    Serial.print("Verbinde mit MQTT Broker " + String(MQTT_BROKER) + "...");
    mqttClient.connect(MQTT_CLIENT_ID);
    delay(1000);

    if (mqttClient.connected())
    {
        Serial.println(" OK!");
    }
    else
    {
        Serial.printf(" Fehler (rc=%d) - System laeuft ohne MQTT weiter!\n",
                     mqttClient.state());
    }
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
    mq2Sensor = mq2;                // Globalen Zeiger setzen fuer Dashboard-Zugriff
    sensorManager->sensorHinzufuegen(mq2);

    // --- MQ-135 Sensor (Luftqualität) ---
    // Analog-Sensor für CO2-Äquivalent und Luftschadstoffe
    // Pin: GPIO 2 (ADC1 Kanal 1)
    auto mq135 = new MQ135Sensor(PIN_MQ135, "luftqualitaet", 5000);
    mq135->setzeSchwellwert(800.0f);  // Alarm bei 800 ppm
    mq135Sensor = mq135;               // Globalen Zeiger setzen
    sensorManager->sensorHinzufuegen(mq135);

    // --- PIR Sensor (Bewegung) ---
    // Digitaler Bewegungsmelder
    // Pin: GPIO 6
    auto pir = new PIRSensor(PIN_PIR, "bewegung", 1000);
    pirSensor = pir;  // Globalen Zeiger setzen
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
    delay(2000);  // Laengere Pause damit Spannung stabil und Serial bereit ist

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

    // Display-Status vor WLAN zeigen
    displayManager->aktualisiereStatus("Verbinde WLAN...");

    // Verbinde mit WLAN (max. 10 Sekunden)
    verbindeWLAN();

    // WICHTIG: Display nach WiFi-Init neu starten!
    // WiFi-Funk kann GPIO1 kurz stören -> Display-Reset nötig
    displayManager->neuStarten();
    displayManager->aktualisiereStatus("Verbinde MQTT...");

    // Verbinde mit MQTT Broker
    verbindeMQTT();

    // Setze MQTT Callback für empfangene Nachrichten
    mqttClient.setCallback(mqttCallback);

    // Display-Status aktualisieren
    displayManager->aktualisiereStatus("Starte Sensoren...");

    // Initialisiere Sensoren
    initialisiereSensoren();

    // DisplayManager mit SensorManager verbinden (fuer Alarm-Visualisierung)
    // Polymorphie in Aktion: SensorManager kennt nur DisplayManager-Interface,
    // egal welcher Sensortyp den Alarm ausloest -> Display wird aktualisiert
    if (sensorManager != nullptr && displayManager != nullptr)
    {
        sensorManager->setzeDisplayManager(displayManager);
        Serial.println("[Setup] DisplayManager mit SensorManager verbunden");
    }

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
    // Prüfe WLAN-Verbindung (nur alle 30 Sekunden erneut versuchen)
    static unsigned long letzterWlanVersuch = 0;
    if (WiFi.status() != WL_CONNECTED && millis() - letzterWlanVersuch > 30000)
    {
        Serial.println("[WLAN] Verbindung verloren - versuche neu...");
        verbindeWLAN();
        letzterWlanVersuch = millis();
    }

    // Prüfe MQTT-Verbindung (nur wenn WLAN aktiv)
    if (WiFi.status() == WL_CONNECTED && !mqttClient.connected())
    {
        static unsigned long letzterMqttVersuch = 0;
        if (millis() - letzterMqttVersuch > 10000)
        {
            Serial.println("[MQTT] Verbindung verloren - versuche neu...");
            verbindeMQTT();
            letzterMqttVersuch = millis();
        }
    }

    // Bearbeite MQTT (keep-alive, callbacks) - nur wenn verbunden
    if (mqttClient.connected())
    {
        mqttClient.loop();
    }

    // Sensoren abfragen und Daten senden
    // Diese Methode prüft intern ob Zeit für neue Messung
    if (sensorManager != nullptr)
    {
        sensorManager->loop();

        // Display alle 2 Sekunden mit ALLEN Sensorwerten aktualisieren
        if (millis() - letzterDisplayUpdate >= 2000)
        {
            if (displayManager != nullptr)
            {
                // Alle Sensorwerte lesen (0.0 wenn Sensor nicht angeschlossen)
                float temp    = (dht22Sensor  && dht22Sensor->getMesswert().status  == SensorStatus::OK)
                                ? dht22Sensor->getMesswert().wert   : 0.0f;

                // Feuchte separat vom DHT22 lesen und aktualisieren
                float feuchte = 0.0f;
                if (dht22Sensor && dht22Sensor->getMesswert().status == SensorStatus::OK)
                {
                    dht22Sensor->messenFeuchte();  // Feuchtemessung durchfuehren
                    feuchte = dht22Sensor->getFeuchte();
                }

                float rauch   = (mq2Sensor    && mq2Sensor->getMesswert().status    == SensorStatus::OK)
                                ? mq2Sensor->getMesswert().wert     : 0.0f;
                float luft    = (mq135Sensor  && mq135Sensor->getMesswert().status  == SensorStatus::OK)
                                ? mq135Sensor->getMesswert().wert   : 0.0f;
                bool  pir     = (pirSensor    && pirSensor->getMesswert().status    == SensorStatus::OK)
                                ? (pirSensor->getMesswert().wert > 0.5f) : false;

                // Alle Kacheln gleichzeitig aktualisieren
                displayManager->aktualisiereAlleWerte(temp, feuchte, rauch, luft, pir);
            }
            letzterDisplayUpdate = millis();
        }
    }

    // LVGL Timer und Auto-Szenen-Wechsel (wichtig fuer Display!)
    if (displayManager != nullptr)
    {
        displayManager->lvglUpdate();
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
