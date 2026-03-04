/**
 * @file Sensor.h
 * @brief Abstrakte Basisklasse für alle Sensoren (Polymorphie)
 * @details Diese Klasse definiert die gemeinsame Schnittstelle für alle Sensoren.
 *          Alle konkreten Sensor-Klassen erben von dieser Basisklasse und implementieren
 *          die virtuellen Methoden. Dies ermöglicht eine einheitliche Behandlung
 *          verschiedener Sensoren im Hauptprogramm - ein zentrales OOP-Prinzip.
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * @version 1.0
 *
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 * Prüfer: IHK Essen, Mülheim an der Ruhr, Oberhausen
 */

#ifndef SENSOR_H
#define SENSOR_H

#include <Arduino.h>
#include "SensorData.h"

/**
 * @class Sensor
 * @brief Abstrakte Basisklasse für alle Sensoren
 * @details Diese Klasse definiert das gemeinsame Interface für alle Sensor-Typen.
 *          Durch die Vererbung können alle Sensoren über einen Zeiger auf diese
 *          Basisklasse angesprochen werden - das ist Polymorphie!
 *
 * Wichtige OOP-Konzepte hier:
 * - Abstrakte Methode: 'virtual' mit '= 0' - muss von Kindklassen überschrieben werden
 * - Virtueller Destruktor: Wichtig für korrekte Speicherfreigabe bei Vererbung
 * - Kapselung: Private Member sind von außen nicht direkt zugänglich
 *
 * Beispiel für Polymorphie im Hauptprogramm:
 * @code
 * Sensor* sensoren[] = { new DHT22Sensor(...), new MQ2Sensor(...) };
 * for (auto& s : sensoren) {
 *     s->init();      // Jeder Sensor initialisiert sich selbst
 *     s->messen();    // Jeder Sensor misst auf seine Weise
 * }
 * @endcode
 */
class Sensor
{
public:
    /**
     * @brief Konstruktor
     * @param konfiguration Sensor-Konfigurationsstruktur mit GPIO-Pin, ID, etc.
     */
    explicit Sensor(const SensorKonfiguration& konfiguration)
        : konfiguration(konfiguration), letzterMessZeitpunkt(0)
    {
        // Initialisiere Messwert mit Standardwerten
        messwert.sensorId = konfiguration.sensorId;
        messwert.sensorTyp = konfiguration.sensorTyp;
        messwert.wert = 0.0f;
        messwert.status = SensorStatus::NICHT_VERFUEGBAR;
        messwert.timestamp = 0;
    }

    /**
     * @brief Konstruktor mit einzelnen Parametern
     * @param gpioPin GPIO-Pin am ESP32
     * @param sensorId Eindeutige Sensor-ID
     * @param typ Sensor-Typ
     * @param intervall Messintervall in ms
     * @param aktiviert Sensor aktiviert?
     */
    Sensor(int gpioPin, String sensorId, SensorTyp typ, unsigned long intervall, bool aktiviert)
        : letzterMessZeitpunkt(0)
    {
        konfiguration.gpioPin = gpioPin;
        konfiguration.sensorId = sensorId;
        konfiguration.sensorTyp = typ;
        konfiguration.messintervall = intervall;
        konfiguration.enabled = aktiviert;

        messwert.sensorId = sensorId;
        messwert.sensorTyp = typ;
        messwert.wert = 0.0f;
        messwert.status = SensorStatus::NICHT_VERFUEGBAR;
        messwert.timestamp = 0;
    }

    /**
     * @brief Virtueller Destruktor
     * @details Wichtig! Sorgt für korrekte Freigabe des Speichers bei abgeleiteten Klassen.
     *          Ohne 'virtual' würde nur der Basisklassen-Destruktor aufgerufen!
     */
    virtual ~Sensor() = default;

    /**
     * @brief Initialisiert den Sensor
     * @return true wenn Initialisierung erfolgreich, false bei Fehler
     * @details Diese Methode muss von jeder Kindklasse überschrieben werden.
     *          Typische Initialisierungen: Pins setzen, Bibliotheken starten, etc.
     */
    virtual bool init() = 0;

    /**
     * @brief Führt eine Messung durch
     * @return true wenn Messung erfolgreich, false bei Fehler
     * @details Diese Methode muss von jeder Kindklasse überschrieben werden.
     *          Liest den aktuellen Sensorwert aus und speichert ihn in messwert.
     */
    virtual bool messen() = 0;

    /**
     * @brief Gibt den letzten Messwert zurück
     * @return SensorMesswert Struktur mit allen Messdaten
     * @details Diese Methode ist nicht virtuell - alle Sensoren geben ihr Ergebnis
     *          in derselben Struktur zurück (Polymorphie beim Input!)
     */
    SensorMesswert getMesswert() const
    {
        return messwert;
    }

    /**
     * @brief Gibt den Sensor-Typ zurück
     * @return SensorTyp des Sensors
     */
    SensorTyp getSensorTyp() const
    {
        return konfiguration.sensorTyp;
    }

    /**
     * @brief Prüft ob der Sensor aktiviert ist
     * @return true wenn Sensor aktiviert
     */
    bool istAktiviert() const
    {
        return konfiguration.enabled;
    }

    /**
     * @brief Prüft ob eine neue Messung fällig ist
     * @return true wenn Zeitintervall abgelaufen
     */
    bool messungFaellig() const
    {
        if (!konfiguration.enabled)
        {
            return false;
        }
        unsigned long aktuelleZeit = millis();
        return (aktuelleZeit - letzterMessZeitpunkt) >= konfiguration.messintervall;
    }

protected:
    /**
     * @brief Aktualisiert den Messwert und Zeitstempel
     * @param wert Neuer Messwert
     * @param status Neuer Status
     * @details Protected - nur für Kindklassen zugänglich
     */
    void aktualisiereMesswert(float wert, SensorStatus status)
    {
        messwert.wert = wert;
        messwert.status = status;
        messwert.timestamp = millis();
        letzterMessZeitpunkt = messwert.timestamp;
    }

    /** @brief Konfiguration des Sensors */
    SensorKonfiguration konfiguration;

    /** @brief Letzter Messwert */
    SensorMesswert messwert;

    /** @brief Zeitpunkt der letzten Messung in Millisekunden */
    unsigned long letzterMessZeitpunkt;
};

#endif // SENSOR_H
