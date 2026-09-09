/**
 * @file SensorManager.h
 * @brief Verwaltet alle Sensoren und koordiniert Messungen + MQTT-Kommunikation
 * @details Zentrale Klasse für die Sensor-Verwaltung.
 *          - Hält Array aller Sensoren (Polymorphie!)
 * - Führt zyklische Messungen durch
 * - Sendet Daten via MQTT an den Broker
 * - Prüft Schwellwerte und löst Alarme aus
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * @version 1.0
 *
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include <Arduino.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "Sensor.h"
#include "SensorData.h"
#include "DS18B20Sensor.h"
#include "MQ2Sensor.h"
#include "MQ135Sensor.h"
#include "PIRSensor.h"
#include "SHT31Sensor.h"

// Maximale Anzahl Sensoren, die verwaltet werden können
#define MAX_SENSOREN 10

/**
 * @class SensorManager
 * @brief Zentrale Verwaltungsklasse für alle Sensoren
 * @details Koordiniert alle Sensoren, führt Messungen durch und sendet Daten per MQTT.
 *
 * Wichtige OOP-Merkmale:
 * - Komposition: Enthält mehrere Sensor-Objekte (via Zeigern)
 * - Polymorphie: Alle Sensoren werden über Sensor* Basisklassen-Zeiger verwaltet
 * - Kapselung: Private Methoden für interne Logik
 *
 * Datenfluss:
 * 1. SensorManager.init() -> initialisiert alle Sensoren
 * 2. SensorManager.loop()  -> prüft ob Messung fällig, führt sie durch, sendet MQTT
 * 3. Bei Alarm           -> Trigger Callback oder direkt via MQTT senden
 */
class SensorManager
{
public:
    /**
     * @brief Konstruktor
     * @param mqttClient Referenz auf PubSubClient für MQTT-Kommunikation
     * @param mqttTopicBasis Basis-Topic für MQTT-Nachrichten (z.B. "serverraum/sensor")
     */
    SensorManager(PubSubClient& mqttClient, String mqttTopicBasis)
        : mqttClient(mqttClient), mqttTopicBasis(mqttTopicBasis)
    {
        anzahlSensoren = 0;
    }

    /**
     * @brief Destruktor
     * @details Löscht alle Sensor-Objekte um Speicher freizugeben
     */
    ~SensorManager()
    {
        for (int i = 0; i < anzahlSensoren; i++)
        {
            delete sensoren[i];
        }
    }

    /**
     * @brief Fügt einen Sensor hinzu
     * @param sensor Pointer auf Sensor-Objekt (wird in Array übernommen)
     * @return true wenn erfolgreich hinzugefügt
     *
     * @note Hier zeigt sich Polymorphie: Wir können jeden Sensor-Typ übergeben,
     *       solange er von Sensor erbt!
     */
    bool sensorHinzufuegen(Sensor* sensor)
    {
        if (anzahlSensoren >= MAX_SENSOREN)
        {
            Serial.println("[SensorManager] Fehler: Maximale Sensoranzahl erreicht!");
            return false;
        }

        sensoren[anzahlSensoren] = sensor;
        anzahlSensoren++;

        Serial.printf("[SensorManager] Sensor hinzugefügt: %s (Typ: %d)\n",
                    sensor->getMesswert().sensorId.c_str(),
                    (int)sensor->getSensorTyp());

        return true;
    }

    /**
     * @brief Initialisiert alle Sensoren
     * @return true wenn alle Sensoren erfolgreich initialisiert
     */
    bool init()
    {
        Serial.println("\n=== SensorManager Initialisierung ===");
        Serial.printf("Anzahl Sensoren: %d\n\n", anzahlSensoren);

        bool alleErfolgreich = true;

        for (int i = 0; i < anzahlSensoren; i++)
        {
            Serial.printf("Initialisiere Sensor %d/%d...\n", i + 1, anzahlSensoren);

            if (!sensoren[i]->init())
            {
                Serial.printf("FEHLER bei Sensor: %s\n",
                           sensoren[i]->getMesswert().sensorId.c_str());
                alleErfolgreich = false;
            }
        }

        Serial.println(alleErfolgreich ? "\n=== Alle Sensoren bereit! ===" : "\n=== Warnung: Nicht alle Sensoren aktiv! ===");

        return alleErfolgreich;
    }

    /**
     * @brief Haupt-Schleife: prüft Sensoren und sendet Daten
     * @details Diese Methode sollte in der Arduino loop() aufgerufen werden!
     *
     * Ablauf pro Zyklus:
     * 1. Prüfe jeden Sensor ob Messung fällig
     * 2. Führe Messung durch falls fällig
     * 3. Sende Daten via MQTT
     * 4. Prüfe auf Alarmbedingungen
     */
    void loop()
    {
        for (int i = 0; i < anzahlSensoren; i++)
        {
            // Hole Sensor-Zeiger
            Sensor* sensor = sensoren[i];

            // Prüfe ob Messung fällig (Zeitintervall abgelaufen)
            if (sensor->messungFaellig())
            {
                // Führe Messung durch
                if (sensor->messen())
                {
                    // Hole Messwert
                    SensorMesswert messwert = sensor->getMesswert();

                    // Sende via MQTT
                    sendeSensorDaten(messwert);

                    // Prüfe Schwellwerte
                    pruefeAlarm(messwert);
                }
            }
        }
    }

    /**
     * @brief Sendet Sensor-Daten via MQTT
     * @param messwert Zu sendender Messwert
     *
     * MQTT-Topic-Struktur:
     * serverraum/sensor/<sensor_id>
     * Beispiel: serverraum/sensor/temp_serverraum
     *
     * JSON-Payload:
     * {
     *   "sensor_id": "temp_serverraum",
     *   "sensor_typ": "DS18B20",
     *   "wert": 22.5,
     *   "status": "OK",
     *   "timestamp": 1234567890
     * }
     */
    void sendeSensorDaten(const SensorMesswert& messwert)
    {
        // Erstelle JSON-Dokument
        JsonDocument jsonDoc;

        // Fülle JSON mit Messwerten
        jsonDoc["sensor_id"] = messwert.sensorId;
        jsonDoc["sensor_typ"] = sensorTypToString(messwert.sensorTyp);
        jsonDoc["wert"] = messwert.wert;
        jsonDoc["status"] = sensorStatusToString(messwert.status);
        jsonDoc["timestamp"] = messwert.timestamp;

        // Erstelle Topic mit Sensor-ID
        String topic = mqttTopicBasis + "/" + messwert.sensorId;

        // Serialize zu String
        char buffer[256];
        serializeJson(jsonDoc, buffer);

        // Sende via MQTT
        if (mqttClient.publish(topic.c_str(), buffer))
        {
            Serial.printf("[MQTT] Gesendet an %s: %s\n", topic.c_str(), buffer);
        }
        else
        {
            Serial.printf("[MQTT] FEHLER beim Senden an %s!\n", topic.c_str());
        }
    }

    /**
     * @brief Sendet Heartbeat/Nachricht dass System lebt
     * @details Wichtig für Monitoring - Backend weiß dass ESP32 noch online
     */
    void sendeHeartbeat()
    {
        JsonDocument jsonDoc;
        jsonDoc["status"] = "online";
        jsonDoc["uptime_ms"] = millis();
        jsonDoc["sensor_count"] = anzahlSensoren;

        String topic = mqttTopicBasis + "/status";
        char buffer[128];
        serializeJson(jsonDoc, buffer);

        mqttClient.publish(topic.c_str(), buffer);
    }

    /**
     * @brief Prüft Messwerte gegen Schwellwerte
     * @param messwert Zu prüfender Messwert
     */
    void pruefeAlarm(const SensorMesswert& messwert)
    {
        // Hier könnten Schwellwerte geprüft werden
        // Einfaches Beispiel:

        switch (messwert.sensorTyp)
        {
            case SensorTyp::DS18B20:
                // Temperatur-Alarm (ab 28°C kritisch mit Buzzer)
                if (messwert.wert >= 28.0f)
                {
                    sendeAlarm("Temperatur kritisch! " + String(messwert.wert, 1) + "°C", messwert);
                }
                else if (messwert.wert >= 22.1f)
                {
                    sendeAlarm("Temperatur erhöht: " + String(messwert.wert, 1) + "°C", messwert);
                }
                break;

            case SensorTyp::MQ2:
                // Rauchgas-Alarm
                if (messwert.wert > 200.0f)
                {
                    sendeAlarm("Rauchgas überschritten!", messwert);
                }
                break;

            case SensorTyp::MQ135:
                // Luftqualitäts-Alarm
                if (messwert.wert > 800.0f)
                {
                    sendeAlarm("Luftqualität schlecht!", messwert);
                }
                break;

            case SensorTyp::PIR:
                // Bewegung wird separat behandelt
                break;

            case SensorTyp::SHT31:
                // SHT31 misst Temperatur und Feuchte - Alarm wenn zu warm oder zu feucht
                if (messwert.wert >= 30.0f)
                {
                    sendeAlarm("Temperatur kritisch! " + String(messwert.wert, 1) + "°C", messwert);
                }
                else if (messwert.wert >= 26.0f)
                {
                    sendeAlarm("Temperatur erhöht: " + String(messwert.wert, 1) + "°C", messwert);
                }
                break;
        }
    }

    /**
     * @brief Sendet Alarm via MQTT
     */
    void sendeAlarm(String nachricht, const SensorMesswert& messwert)
    {
        JsonDocument jsonDoc;
        jsonDoc["alarm"] = true;
        jsonDoc["nachricht"] = nachricht;
        jsonDoc["sensor_id"] = messwert.sensorId;
        jsonDoc["sensor_typ"] = sensorTypToString(messwert.sensorTyp);
        jsonDoc["wert"] = messwert.wert;
        jsonDoc["timestamp"] = messwert.timestamp;

        String topic = mqttTopicBasis + "/alarm";
        char buffer[256];
        serializeJson(jsonDoc, buffer);

        mqttClient.publish(topic.c_str(), buffer);
        Serial.printf("[ALARM] %s - %s: %.1f\n", nachricht.c_str(),
                     messwert.sensorId.c_str(), messwert.wert);
    }

    /**
     * @brief Gibt Anzahl der Sensoren zurück
     */
    int getAnzahlSensoren() const
    {
        return anzahlSensoren;
    }

private:
    /** @brief Array von Sensor-Zeigern (Polymorphie!) */
    Sensor* sensoren[MAX_SENSOREN];

    /** @brief Anzahl aktuell verwalteter Sensoren */
    int anzahlSensoren;

    /** @brief MQTT Client Referenz */
    PubSubClient& mqttClient;

    /** @brief Basis-Topic für MQTT */
    String mqttTopicBasis;

    /**
     * @brief Konvertiert SensorTyp zu String
     */
    String sensorTypToString(SensorTyp typ) const
    {
        switch (typ)
        {
            case SensorTyp::DS18B20: return "DS18B20";
            case SensorTyp::MQ2: return "MQ2";
            case SensorTyp::MQ135: return "MQ135";
            case SensorTyp::PIR: return "PIR";
            case SensorTyp::SHT31: return "SHT31";
            default: return "UNBEKANNT";
        }
    }

    /**
     * @brief Konvertiert SensorStatus zu String
     */
    String sensorStatusToString(SensorStatus status) const
    {
        switch (status)
        {
            case SensorStatus::OK: return "OK";
            case SensorStatus::FEHLER: return "FEHLER";
            case SensorStatus::TIMEOUT: return "TIMEOUT";
            case SensorStatus::NICHT_VERFUEGBAR: return "NICHT_VERFUEGBAR";
            default: return "UNBEKANNT";
        }
    }
};

#endif // SENSOR_MANAGER_H
