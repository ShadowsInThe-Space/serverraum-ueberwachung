/**
 * @file PIRSensor.h
 * @brief Konkrete Sensor-Klasse für PIR-Bewegungsmelder (HC-SR501)
 * @details Implementiert die abstrakte Sensor-Schnittstelle für den PIR-Sensor.
 *          Der PIR (Passive Infrared) erkennt Wärmestrahlung von Menschen/Tieren.
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * @version 1.0
 *
 * Hardware: HC-SR501 PIR-Bewegungsmelder
 * Pin-Belegung: Siehe Tech-Specs (GPIO 6)
 *
 * Funktionsweise PIR:
 * - "Passiv" = Sensor sendet nichts, nur empfängt Infrarot
 * - Besteht aus Pyroelectric Element (misst IR-Strahlung)
 * - Bei Änderung der IR-Strahlung (Bewegung) wird Output auf HIGH gesetzt
 * - Empfindlich für Körperwärme (~37°C = Infrarot ~10μm Wellenlänge)
 *
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

#ifndef PIR_SENSOR_H
#define PIR_SENSOR_H

#include <Arduino.h>
#include "Sensor.h"

/**
 * @class PIRSensor
 * @brief Konkrete Implementierung für PIR-Bewegungsmelder
 * @details Erbt von der abstrakten Sensor-Klasse.
 *
 * Technische Daten HC-SR501:
 * - Erfassungswinkel: ca. 120°
 * - Erfassungsreichweite: 3-7m (einstellbar)
 * - Arbeitsspannung: 5V-20V (am ESP32: 5V über VIN)
 * - Ausgang: Digital (LOW = keine Bewegung, HIGH = Bewegung erkannt)
 * - Ansprechzeit: 0.3-3 Sekunden (einstellbar)
 * - Blockzeit: 0.5 Sekunden (Zeit zwischen zwei Detektionen)
 */
class PIRSensor : public Sensor
{
public:
    /**
     * @brief Konstruktor für PIR-Sensor
     * @param digitalPin GPIO-Pin für digitalen Eingang (PIR-Out)
     * @param sensorId Eindeutige ID für diesen Sensor
     * @param messintervall Zeit in ms zwischen Abfragen (PIR wird interrupt-basiert ausgelesen)
     *
     * @note HC-SR501 hat zwei Potis:
     *       - Links: Empfindlichkeit/Reichweite (im Uhrzeigersinn = mehr)
     *       - Rechts: Haltezeit (im Uhrzeigersinn = länger, bis zu 300s)
     *       Für Serverraum: Kurze Haltezeit (5-10 Sekunden) empfohlen!
     */
    PIRSensor(int digitalPin, String sensorId, unsigned long messintervall = 1000)
        : Sensor(digitalPin, sensorId, SensorTyp::PIR, messintervall, true)
    {
        // Initialisiere States
        bewegungErkannt = false;
        bewegungStartZeit = 0;
        letzteBewegungZeit = 0;
    }

    /**
     * @brief Initialisiert den PIR-Sensor
     * @return true wenn Initialisierung erfolgreich
     *
     * Aufgaben:
     * 1. Digitalen Pin als Eingang konfigurieren
     * 2. Interne PullDown aktivieren (oder externen Widerstand nutzen)
     * 3. Warm-up Zeit abwarten (Sensor braucht 30-60 Sekunden Einschwingzeit)
     */
    bool init() override
    {
        // Digitalen Pin als Eingang konfigurieren
        // WICHTIG: PIR gibt 5V aus! ESP32 verträgt aber nur 3.3V!
        // -> Muss mit Spannungsteiler oder Level-Shifter auf 3.3V reduziert werden
        // -> Oder: HC-SR501 auf 3.3V modifizieren (siehe Bastelprojekte)
        pinMode(konfiguration.gpioPin, INPUT);

        // Interne PullDown aktivieren (keine externe Beschaltung nötig)
        digitalWrite(konfiguration.gpioPin, LOW);

        // Wartezeit auf Sensor-Stabilisierung (warm-up)
        // In dieser Zeit kann der Sensor noch "falsch" messen!
        delay(1000);

        // Setze Startzeit
        sensorAktiviertSeit = millis();

        messwert.status = SensorStatus::OK;

        Serial.println("[PIR] Initialisiert: GPIO " + String(konfiguration.gpioPin));
        Serial.println("[PIR] Warm-up Phase: 30-60 Sekunden warten für genaue Messung!");

        return true;
    }

    /**
     * @brief Führt eine Bewegungsmessung durch
     * @return true wenn Messung erfolgreich
     *
     * Messlogik:
     * 1. Lese digitalen Pin (LOW = keine Bewegung, HIGH = Bewegung)
     * 2. Wenn HIGH -> Bewegung erkannt, Zeitstempel speichern
     * 3. Wenn LOW -> prüfe ob Bewegung vor kurzem war (Haltezeit)
     * 4. Setze messwert.wert auf 1.0 (Bewegung) oder 0.0 (keine)
     */
    bool messen() override
    {
        if (!konfiguration.enabled)
        {
            return false;
        }

        // Prüfe ob Warm-up Phase noch läuft
        if (millis() - sensorAktiviertSeit < 60000)
        {
            // Noch nicht warm - gebe Warnung alle 10 Sekunden
            if ((millis() - sensorAktiviertSeit) % 10000 < 1000)
            {
                Serial.printf("[PIR] Warm-up: %lu Sekunden...\n", (millis() - sensorAktiviertSeit) / 1000);
            }
        }

        // Lese digitalen Eingang
        // HC-SR501: HIGH = Bewegung, LOW = keine Bewegung
        int pirStatus = digitalRead(konfiguration.gpioPin);

        if (pirStatus == HIGH)
        {
            // Bewegung erkannt!
            if (!bewegungErkannt)
            {
                // Neue Bewegung (war vorher keine)
                bewegungErkannt = true;
                bewegungStartZeit = millis();
                Serial.println("[PIR] BEWEGUNG ERKANNT: " + konfiguration.sensorId);
            }
            // Aktualisiere "letzte Bewegung" Zeitstempel
            letzteBewegungZeit = millis();
        }
        else
        {
            // Kein Signal vom PIR
            // Prüfe ob Haltezeit abgelaufen (typisch 5 Sekunden am HC-SR501)
            if (bewegungErkannt && (millis() - letzteBewegungZeit) > 5000)
            {
                // Bewegung beendet
                bewegungErkannt = false;
                Serial.println("[PIR] Bewegung beendet: " + konfiguration.sensorId);
            }
        }

        // Setze Messwert (1.0 = Bewegung, 0.0 = keine Bewegung)
        float wert = bewegungErkannt ? 1.0f : 0.0f;

        // Speichere Messwert
        aktualisiereMesswert(wert, SensorStatus::OK);

        return true;
    }

    /**
     * @brief Prüft ob aktuell Bewegung erkannt ist
     * @return true wenn Bewegung erkannt
     */
    bool istBewegungErkannt() const
    {
        return bewegungErkannt;
    }

    /**
     * @brief Gibt Zeit seit letzter Bewegung zurück
     * @return Millisekunden seit letzter Bewegung (0 wenn aktuell Bewegung)
     */
    unsigned long zeitSeitLetzterBewegung() const
    {
        if (bewegungErkannt)
        {
            return 0;
        }
        return millis() - letzteBewegungZeit;
    }

    /**
     * @brief Setzt Alarm bei Bewegung (für Alarmierungslogik)
     * @param aktiv true wenn Alarm bei Bewegung ausgelöst werden soll
     */
    void setzeAlarmBeiBewegung(bool aktiv)
    {
        alarmBeiBewegung = aktiv;
    }

    /**
     * @brief Prüft ob Alarm ausgelöst werden soll
     */
    bool alarmAusloesen() const
    {
        return alarmBeiBewegung && bewegungErkannt;
    }

private:
    /** @brief true wenn aktuell Bewegung erkannt */
    bool bewegungErkannt;

    /** @brief Zeitstempel wann Bewegung erkannt wurde */
    unsigned long bewegungStartZeit;

    /** @brief Zeitstempel der letzten erkannten Bewegung */
    unsigned long letzteBewegungZeit;

    /** @brief Zeitstempel wann Sensor aktiviert wurde */
    unsigned long sensorAktiviertSeit;

    /** @brief true wenn Alarm bei Bewegung ausgelöst werden soll */
    bool alarmBeiBewegung = true;
};

#endif // PIR_SENSOR_H
