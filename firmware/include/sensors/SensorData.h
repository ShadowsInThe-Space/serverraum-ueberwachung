/**
 * @file SensorData.h
 * @brief Datenstrukturen für Sensor-Messwerte
 * @details Definiert die gemeinsamen Datenstrukturen, die von allen Sensoren verwendet werden.
 *          Dies ermöglicht eine einheitliche Behandlung verschiedener Sensoren via Polymorphie.
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * @version 1.0
 *
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

#ifndef SENSOR_DATA_H
#define SENSOR_DATA_H

#include <Arduino.h>

/**
 * @enum SensorTyp
 * @brief Aufzählung aller unterstützter Sensor-Typen
 * @details Wird verwendet, um den Sensor-Typ zu identifizieren und korrekt zu verarbeiten.
 */
enum class SensorTyp
{
    DHT22,       ///< Digitaler Sensor für Temperatur und Luftfeuchtigkeit
    DS18B20,     ///< Digitaler 1-Wire Temperatursensor
    MQ2,         ///< Analoger Sensor für Rauchgas und brennbare Gase
    MQ135,       ///< Analoger Sensor für Luftqualität (CO2, Ammoniak, Benzol)
    PIR          ///< Passiver Infrarot-Bewegungsmelder
};

/**
 * @enum SensorStatus
 * @brief Statuscodes für Sensorzustände
 * @details Gibt an, ob der Sensor funktioniert oder Fehler aufgetreten sind.
 */
enum class SensorStatus
{
    OK,              ///< Sensor funktioniert normal
    FEHLER,          ///< Allgemeiner Sensorfehler
    TIMEOUT,         ///< Kommunikationstimeout (bei digitalen Sensoren)
    NICHT_VERFUEGBAR ///< Sensor nicht angeschlossen oder defekt
};

/**
 * @struct SensorMesswert
 * @brief Struktur für einen einzelnen Messwert eines Sensors
 * @details Enthält alle relevanten Daten eines Sensor-Messwertes in einem einheitlichen Format.
 *
 * @var SensorMesswert::sensorId
 * Eindeutige ID des Sensors (z.B. "temp_wohnzimmer")
 *
 * @var SensorMesswert::sensorTyp
 * Typ des Sensors aus der SensorTyp-Aufzählung
 *
 * @var SensorMesswert::wert
 * Numerischer Messwert (Temperatur in °C, Feuchte in %, Gas in ppm, etc.)
 *
 * @var SensorMesswert::status
 * Aktueller Status des Sensors
 *
 * @var SensorMesswert::timestamp
 * Zeitstempel der Messung in Millisekunden seit Systemstart
 */
struct SensorMesswert
{
    String sensorId;           ///< Eindeutige Sensor-ID
    SensorTyp sensorTyp;       ///< Sensor-Typ
    float wert;                ///< Messwert (Temperatur in °C, Feuchte in %, etc.)
    SensorStatus status;       ///< Sensor-Status
    unsigned long timestamp;   ///< Zeitstempel in Millisekunden
};

/**
 * @struct SensorKonfiguration
 * @brief Konfigurationsparameter für einen Sensor
 * @details Enthält alle Konfigurationswerte, die für den Sensor-Betrieb erforderlich sind.
 *
 * @var SensorKonfiguration::gpioPin
 * GPIO-Pin-Nummer am ESP32 (z.B. 5 für DHT22)
 *
 * @var SensorKonfiguration::sensorId
 * Eindeutige Identifikation des Sensors
 *
 * @var SensorKonfiguration::messintervall
 * Zeitintervall zwischen Messungen in Millisekunden
 *
 * @var SensorKonfiguration::enabled
 * Gibt an, ob der Sensor aktiviert ist
 */
struct SensorKonfiguration
{
    int gpioPin;               ///< GPIO-Pin am ESP32
    String sensorId;           ///< Eindeutige Sensor-ID
    SensorTyp sensorTyp;       ///< Typ des Sensors
    unsigned long messintervall;   ///< Messintervall in ms
    bool enabled;              ///< Sensor aktiviert?
};

#endif // SENSOR_DATA_H
