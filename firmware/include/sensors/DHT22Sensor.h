/**
 * @file DHT22Sensor.h
 * @brief Konkrete Sensor-Klasse für DHT22 (Temperatur und Luftfeuchtigkeit)
 * @details Implementiert die abstrakte Sensor-Schnittstelle für den DHT22-Sensor.
 *          Der DHT22 ist ein digitaler Sensor, der über einen einzigen Datenpin
 *          sowohl Temperatur als auch Luftfeuchtigkeit misst.
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * @version 1.0
 *
 * Hardware: DHT22 (auch AM2302 genannt)
 * Pin-Belegung: Siehe Tech-Specs (GPIO 5)
 *
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

#ifndef DHT22_SENSOR_H
#define DHT22_SENSOR_H

#include <Arduino.h>
#include <DHT.h>  // Adafruit DHT Bibliothek
#include "Sensor.h"

/**
 * @class DHT22Sensor
 * @brief Konkrete Implementierung für DHT22-Sensor
 * @details Erbt von der abstrakten Sensor-Klasse und implementiert die virtuellen Methoden.
 *          Der DHT22 misst:
 *          - Temperatur: -40°C bis +80°C, Genauigkeit ±0.5°C
 *          - Luftfeuchtigkeit: 0-100% rF, Genauigkeit ±2% rF
 *
 * Wichtige OOP-Aspekte:
 * - Vererbung: Erweitert die Basisklasse Sensor
 * - Polymorphie: Kann über Sensor* Zeiger verwendet werden
 * - Komposition: Nutzt DHT-Bibliothek für Hardware-Kommunikation
 */
class DHT22Sensor : public Sensor
{
public:
    /**
     * @brief Konstruktor für DHT22-Sensor
     * @param pin GPIO-Pin am ESP32, an dem der DHT22 angeschlossen ist
     * @param sensorId Eindeutige ID für diesen Sensor (z.B. "temp_serverraum")
     * @param messintervall Zeit in ms zwischen zwei Messungen (Standard: 2000ms)
     *
     * @note Der DHT22 benötigt mindestens 2 Sekunden zwischen Messungen!
     */
    DHT22Sensor(int pin, String sensorId, unsigned long messintervall = 2000)
        : Sensor(pin, sensorId, SensorTyp::DHT22, messintervall, true)
    {
        // Erstelle DHT-Instanz mit dem konfigurierten Pin
        // DHT22 ist der Sensortyp, 20 ist die Sample-Rate in Millisekunden
        dhtSensor = new DHT(pin, DHT22, 20);
    }

    /**
     * @brief Destruktor
     * @details Gibt den reservierten Speicher für die DHT-Instanz frei
     */
    ~DHT22Sensor() override
    {
        delete dhtSensor;
    }

    /**
     * @brief Initialisiert den DHT22-Sensor
     * @return true wenn Initialisierung erfolgreich
     * @details Startet die DHT-Bibliothek und prüft, ob Sensor antwortet
     *
     * Funktionsweise:
     * 1. DHT-Bibliothek initialisieren
     * 2. Wartezeit für Sensor-Stabilisierung
     * 3. Erste "fiktive" Messung durchführen (Sensor aufwecken)
     */
    bool init() override
    {
        // Starte den DHT-Sensor
        dhtSensor->begin();

        // Warte 1 Sekunde auf Sensor-Stabilisierung
        // Wichtig: Der DHT22 braucht nach dem Einschalten Zeit!
        delay(1000);

        // Führe erste Messung durch (Aufweck-Sequenz)
        // Dies ist notwendig, damit die erste echte Messung valide Daten liefert
        float testTemperatur = dhtSensor->readTemperature();

        // Prüfe ob Messwert gültig (kein NaN = Sensor antwortet)
        if (isnan(testTemperatur))
        {
            // Sensor antwortet nicht - setze Fehlerstatus
            messwert.status = SensorStatus::FEHLER;
            Serial.println("[DHT22] Fehler: Sensor antwortet nicht an GPIO " + String(konfiguration.gpioPin));
            return false;
        }

        // Alles OK - initialisiere mit Standardwerten
        messwert.status = SensorStatus::OK;
        Serial.println("[DHT22] Initialisiert: GPIO " + String(konfiguration.gpioPin) + ", ID: " + konfiguration.sensorId);
        return true;
    }

    /**
     * @brief Führt eine Temperatur-Messung durch
     * @return true wenn Messung erfolgreich
     *
     * Technische Details:
     * - Liest Temperatur vom DHT22 aus
     * - Konvertiert Byte-Daten in Float-Wert
     * - Prüft auf Kommunikationsfehler
     */
    bool messen() override
    {
        if (!konfiguration.enabled)
        {
            return false;
        }

        // Lese Temperatur in Celsius
        float temperatur = dhtSensor->readTemperature();

        // Prüfe auf Fehler (isnan = Not a Number = Kommunikationsfehler)
        if (isnan(temperatur))
        {
            aktualisiereMesswert(0.0f, SensorStatus::TIMEOUT);
            Serial.println("[DHT22] Timeout bei Sensor: " + konfiguration.sensorId);
            return false;
        }

        // Messwert aktualisieren
        aktualisiereMesswert(temperatur, SensorStatus::OK);

        // Debug-Ausgabe
        Serial.printf("[DHT22] %s: %.1f°C\n", konfiguration.sensorId.c_str(), temperatur);

        return true;
    }

    /**
     * @brief Führt eine Luftfeuchtigkeits-Messung durch
     * @return true wenn Messung erfolgreich
     */
    bool messenFeuchte()
    {
        if (!konfiguration.gpioPin)
        {
            return false;
        }

        // Lese Luftfeuchtigkeit
        float feuchte = dhtSensor->readHumidity();

        // Prüfe auf Fehler
        if (isnan(feuchte))
        {
            return false;
        }

        // Speichere Feuchte separat (in float-Member)
        // Dies ermöglicht Abruf über getFeuchte()
        this->feuchte = feuchte;

        Serial.printf("[DHT22] %s: %.1f%%\n", konfiguration.sensorId.c_str(), feuchte);
        return true;
    }

    /**
     * @brief Gibt die aktuelle Luftfeuchtigkeit zurück
     * @return Feuchte in Prozent (0-100)
     */
    float getFeuchte() const
    {
        return feuchte;
    }

private:
    /** @brief Zeiger auf DHT-Bibliotheksinstanz */
    DHT* dhtSensor;

    /** @brief Letzter gemessener Feuchtigkeitswert */
    float feuchte = 0.0f;
};

#endif // DHT22_SENSOR_H
