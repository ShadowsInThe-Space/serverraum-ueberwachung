/**
 * @file MQ2Sensor.h
 * @brief Konkrete Sensor-Klasse für MQ-2 (Rauchgas und brennbare Gase)
 * @details Implementiert die abstrakte Sensor-Schnittstelle für den MQ-2-Gassensor.
 *          Der MQ-2 detektiert Rauch, Methan, Propan, Butan und andere brennbare Gase.
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * @version 1.0
 *
 * Hardware: MQ-2 Gas-Sensor
 * Pin-Belegung: Siehe Tech-Specs (GPIO 1, ADC)
 *
 * Funktionsweise MQ-2:
 * - Der Sensor hat einen Heizelement, das konstant auf Betriebstemperatur gehalten wird
 * - Bei Kontakt mit Gasen ändert sich der Widerstand des Halbleiters
 * - Dieser Widerstand wird via ADC (Analog-Digital-Converter) gemessen
 * - Höherer ADC-Wert = mehr Gas in der Luft
 *
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

#ifndef MQ2_SENSOR_H
#define MQ2_SENSOR_H

#include <Arduino.h>
#include "Sensor.h"

/**
 * @class MQ2Sensor
 * @brief Konkrete Implementierung für MQ-2-Gassensor
 * @details Erbt von der abstrakten Sensor-Klasse.
 *
 * Technische Daten MQ-2:
 * - Detektiert: Rauch, Methan (CH4), Propan (C3H8), Butan (C4H10), Wasserstoff (H2)
 * - Betriebsspannung: 5V (am ESP32 über VIN oder extern)
 * - Ausgang: Analoger Spannungswert (0-5V, am ESP32 0-3.3V via Spannungsteiler)
 * - Heizelement: ~800mW im Betrieb
 *
 * Kalibrierung:
 * - Der Sensor muss 24-48 Stunden "einbrennen" für stabile Werte
 * - Empfindlichkeit wird durch Vorwiderstand (RL) bestimmt
 * - Typischer RL: 4.7kOhm bis 10kOhm
 */
class MQ2Sensor : public Sensor
{
public:
    /**
     * @brief Konstruktor für MQ-2-Sensor
     * @param adcPin ADC-Pin am ESP32 (GPIO 1 für Kanal 0)
     * @param sensorId Eindeutige ID für diesen Sensor
     * @param messintervall Zeit in ms zwischen Messungen
     *
     * @note MQ-2 braucht Aufwärmzeit (preheat) von ca. 20 Sekunden nach Einschalten!
     */
    MQ2Sensor(int adcPin, String sensorId, unsigned long messintervall = 5000)
        : Sensor(adcPin, sensorId, SensorTyp::MQ2, messintervall, true)
    {
        // Initialisiere Basiswerte
        luftwert = 0;
        rauchwert = 0;
        aufwaermzeitStart = 0;
        istAufgewaermt = false;
    }

    /**
     * @brief Initialisiert den MQ-2-Sensor
     * @return true wenn Initialisierung erfolgreich
     *
     * Aufgaben:
     * 1. ADC-Pin als Eingang konfigurieren
     * 2. Aufwärmphase starten (Sensor braucht Strom für Heizelement)
     * 3. Basis-Luftwert (Ro) kalibrieren
     */
    bool init() override
    {
        // ADC-Pin als Eingang ohne Pullup (ESP32 ADC1)
        pinMode(konfiguration.gpioPin, INPUT);

        // Starte Aufwärmphase
        // WICHTIG: MQ-2 braucht 20-60 Sekunden Aufwärmzeit für genaue Messungen!
        // In dieser Zeit heizt das Heizelement den Sensor auf Betriebstemperatur
        aufwaermzeitStart = millis();
        istAufgewaermt = false;

        // Setze Standard-Messwert
        messwert.status = SensorStatus::OK;

        Serial.println("[MQ2] Initialisiert: ADC-Pin GPIO " + String(konfiguration.gpioPin));
        Serial.println("[MQ2] Aufwärmphase gestartet - bitte warten...");

        return true;
    }

    /**
     * @brief Führt eine Rauchgas-Messung durch
     * @return true wenn Messung erfolgreich
     *
     * Messablauf:
     * 1. ADC-Wert einlesen (0-4095 bei 12-Bit ADC)
     * 2. ADC-Wert in Spannung umrechnen
     * 3. Widerstand des Sensors berechnen (Spannungsteiler-Formel)
     * 4. ppm-Wert berechnen (basierend auf Kalibrierungskurve)
     */
    bool messen() override
    {
        if (!konfiguration.enabled)
        {
            return false;
        }

        // Prüfe ob Aufwärmzeit abgeschlossen (mindestens 20 Sekunden)
        unsigned long aufwaermDauer = millis() - aufwaermzeitStart;
        if (!istAufgewaermt && aufwaermDauer < 20000)
        {
            // Noch nicht aufgeheizt - gebe rohen ADC-Wert aus
            if (aufwaermDauer % 5000 < 1000)
            {
                Serial.printf("[MQ2] Aufwärmen: %lu Sekunden...\n", aufwaermDauer / 1000);
            }
            // Messung trotzdem durchführen, aber mit Warnung
        }
        else if (!istAufgewaermt)
        {
            istAufgewaermt = true;
            Serial.println("[MQ2] Aufwärmphase abgeschlossen!");
        }

        // 1. ADC-Wert einlesen (0-4095 bei 12-Bit)
        // ADC mit 12 Bit Auflösung = 4096 Stufen (0 bis 4095)
        int adcWert = analogRead(konfiguration.gpioPin);

        // 2. Spannung berechnen (ESP32: 3.3V Referenz)
        float spannung = (adcWert / 4095.0f) * 3.3f;

        // 3. Sensor-Widerstand berechnen (Spannungsteiler mit RL = 10kOhm)
        // Formel: Rs = (Vc - Vout) / Vout * RL
        float widerstand = (3.3f - spannung) / spannung * 10000.0f;

        // 4. ppm berechnen (vereinfachte Kalibrierungskurve)
        // Genaue Kurve muss empirisch bestimmt werden!
        // Typische Formel: ppm = a * (Rs/Ro)^b
        float ppm = berechnePPM(widerstand);

        // Wert in messwert speichern
        aktualisiereMesswert(ppm, SensorStatus::OK);

        // Debug-Ausgabe
        Serial.printf("[MQ2] %s: ADC=%d, Spannung=%.2fV, Widerstand=%.0f Ohm, ppm=%.0f\n",
                     konfiguration.sensorId.c_str(), adcWert, spannung, widerstand, ppm);

        return true;
    }

    /**
     * @brief Kalibriert den Sensor mit Frischluft (saubere Luft)
     * @details Muss in sauberer Umgebung aufgerufen werden!
     *          Speichert den Widerstand bei 0 ppm als Referenz (Ro)
     */
    void kalibrieren()
    {
        Serial.println("[MQ2] Kalibrierung gestartet - bitte in frischer Luft warten!");

        // Mehrere Messungen über 5 Sekunden mitteln
        float summe = 0;
        for (int i = 0; i < 50; i++)
        {
            int adcWert = analogRead(konfiguration.gpioPin);
            float spannung = (adcWert / 4095.0f) * 3.3f;
            float widerstand = (3.3f - spannung) / spannung * 10000.0f;
            summe += widerstand;
            delay(100);
        }

        luftwert = summe / 50.0f;
        Serial.printf("[MQ2] Kalibrierung abgeschlossen: Ro = %.0f Ohm\n", luftwert);
    }

    /**
     * @brief Setzt den Schwellwert für Alarmierung
     * @param schwelle ppm-Wert, bei dem Alarm ausgelöst wird
     */
    void setzeSchwellwert(float schwelle)
    {
        alarmSchwelle = schwelle;
    }

    /**
     * @brief Prüft ob Alarm ausgelöst werden soll
     * @return true wenn ppm über Schwellwert
     */
    bool alarmAusloesen() const
    {
        return messwert.wert > alarmSchwelle;
    }

private:
    /** @brief Widerstand des Sensors bei frischer Luft (Ro) */
    float luftwert;

    /** @brief Aktueller ppm-Wert für Rauch */
    float rauchwert;

    /** @brief Zeitpunkt zu dem Aufwärmung begann */
    unsigned long aufwaermzeitStart;

    /** @brief true wenn Aufwärmphase abgeschlossen */
    bool istAufgewaermt;

    /** @brief Schwellwert für Alarmierung (ppm) */
    float alarmSchwelle = 200.0f;  // Typischer Wert für Rauchalarm

    /**
     * @brief Berechnet ppm aus Widerstand
     * @param widerstand Aktueller Sensor-Widerstand in Ohm
     * @return Geschätzte Gaskonzentration in ppm
     *
     * @note Dies ist eine vereinfachte Berechnung!
     *       Für genaue Messungen muss die Kalibrierungskurve des Sensors
     *       vermessen und in eine Lookup-Tabelle überführt werden.
     *
     * Typische Kennlinie MQ-2:
     * - 200 ppm: Reines Propangas
     * - 500 ppm: Stadtgas
     * - 1000 ppm: Zigarettenrauch
     * - 2000 ppm: Holzfeuer
     */
    float berechnePPM(float widerstand)
    {
        // Vereinfachte Berechnung basierend auf typischer Kennlinie
        // Verhältnis Rs/Ro bestimmt die Gaskonzentration

        if (luftwert <= 0)
        {
            // Keine Kalibrierung - verwende Standardkurve
            // Typischer Bereich: 100-10000 Ohm in sauberer Luft
            widerstand = 10000.0f;
        }

        float verhaeltnis = widerstand / luftwert;

        // Vereinfachte Umrechnung (Polynomial approximation)
        // MQ-2 Kennlinie: ppm = 613.9 * (Rs/Ro)^-2.074
        float ppm = 613.9f * pow(verhaeltnis, -2.074f);

        // Begrenze auf physikalisch sinnvollen Bereich
        ppm = constrain(ppm, 0.0f, 10000.0f);

        return ppm;
    }
};

#endif // MQ2_SENSOR_H
