/**
 * @file Folie6_AbstrakteBasisklasse.cpp
 * Abstrakte Sensor-Basisklasse für Polymorphie
 */

#include <Arduino.h>
#include "SensorData.h"

// Abstrakte Basisklasse - Polymorphie!
class Sensor {
public:
    explicit Sensor(const SensorKonfiguration& konfiguration)
        : konfiguration(konfiguration), letzterMessZeitpunkt(0) {
        messwert.sensorId = konfiguration.sensorId;
        messwert.sensorTyp = konfiguration.sensorTyp;
        messwert.wert = 0.0f;
        messwert.status = SensorStatus::NICHT_VERFUEGBAR;
    }

    // Virtueller Destruktor
    virtual ~Sensor() = default;

    // Rein virtuelle Methoden = 0 (MÜSSEN überschrieben werden!)
    virtual bool init() = 0;
    virtual bool messen() = 0;

    // Konkrete Methode (nicht virtuell)
    SensorMesswert getMesswert() const {
        return messwert;
    }

protected:
    // Protected: nur für Kindklassen
    void aktualisiereMesswert(float wert, SensorStatus status) {
        messwert.wert = wert;
        messwert.status = status;
        messwert.timestamp = millis();
        letzterMessZeitpunkt = messwert.timestamp;
    }

    SensorKonfiguration konfiguration;
    SensorMesswert messwert;
    unsigned long letzterMessZeitpunkt;
};
