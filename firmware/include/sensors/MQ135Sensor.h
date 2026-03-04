/**
 * @file MQ135Sensor.h
 * @brief Konkrete Sensor-Klasse für MQ-135 (Luftqualität / Giftgase)
 * @details Implementiert die abstrakte Sensor-Schnittstelle für den MQ-135-Gassensor.
 *          Der MQ-135 detektiert CO2, Ammoniak, Benzol, Alkohol und Rauch.
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * @version 1.0
 *
 * Hardware: MQ-135 Gas-Sensor
 * Pin-Belegung: Siehe Tech-Specs (GPIO 2, ADC)
 *
 * Funktionsweise MQ-135:
 * - Ähnlich wie MQ-2, aber auf andere Gase optimiert
 * - Hauptsächlich für Luftqualitäts-Messung in Innenräumen
 * - Sensitivität: NH3, NOx, CO2, Alkohol, Benzol, Rauch
 *
 * WICHTIG: MQ-135 misst NICHT direkt CO2 in ppm!
 *          Er misst die Leitfähigkeitsänderung des Halbleiters.
 *          Die Umrechnung in "ppm CO2-äquivalent" ist eine Schätzung!
 *
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

#ifndef MQ135_SENSOR_H
#define MQ135_SENSOR_H

#include <Arduino.h>
#include "Sensor.h"

/**
 * @class MQ135Sensor
 * @brief Konkrete Implementierung für MQ-135-Luftqualitätssensor
 * @details Erbt von der abstrakten Sensor-Klasse.
 *
 * Technische Daten MQ-135:
 * - Detektiert: CO2 (Schätzung), Ammoniak (NH3), NOx, Benzol, Alkohol, Rauch
 * - Betriebsspannung: 5V
 * - Heizelement: ~800mW
 * - Arbeitsbereich: -10°C bis +45°C
 *
 * Typische Werte (in sauberer Luft):
 * - Widerstand (Rs): 2-20 kOhm (abhängig von Luftfeuchtigkeit!)
 * - Empfindlichkeit: 10-200 kOhm pro ppm Gas
 */
class MQ135Sensor : public Sensor
{
public:
    /**
     * @brief Konstruktor für MQ-135-Sensor
     * @param adcPin ADC-Pin am ESP32 (GPIO 2 für Kanal 1)
     * @param sensorId Eindeutige ID für diesen Sensor
     * @param messintervall Zeit in ms zwischen Messungen
     */
    MQ135Sensor(int adcPin, String sensorId, unsigned long messintervall = 5000)
        : Sensor(adcPin, sensorId, SensorTyp::MQ135, messintervall, true)
    {
        // Basiswerte initialisieren
        luftwert = 0;
        istKalibriert = false;
        aufwaermzeitStart = 0;
    }

    /**
     * @brief Initialisiert den MQ-135-Sensor
     * @return true wenn Initialisierung erfolgreich
     */
    bool init() override
    {
        // ADC-Pin als Eingang konfigurieren
        pinMode(konfiguration.gpioPin, INPUT);

        // Aufwärmphase starten
        // MQ-135 braucht etwa 24-48 Stunden "Einbrennzeit" für optimale Genauigkeit!
        // Nach dem ersten Einschalten: mindestens 5 Minuten aufwärmen
        aufwaermzeitStart = millis();

        messwert.status = SensorStatus::OK;

        Serial.println("[MQ135] Initialisiert: ADC-Pin GPIO " + String(konfiguration.gpioPin));
        Serial.println("[MQ135] Hinweis: Erste Messungen nach 5 Min Aufwärmzeit sind aussagekräftig");

        return true;
    }

    /**
     * @brief Führt eine Luftqualitäts-Messung durch
     * @return true wenn Messung erfolgreich
     *
     * Messung:
     * 1. ADC-Wert einlesen
     * 2. Widerstand berechnen
     * 3. ppm-Äquivalent berechnen (verschiedene Gase)
     */
    bool messen() override
    {
        if (!konfiguration.enabled)
        {
            return false;
        }

        // Aufwärmzeit anzeigen (erste 2 Minuten)
        unsigned long aufwaermDauer = millis() - aufwaermzeitStart;
        if (aufwaermDauer < 120000 && aufwaermDauer % 30000 < 1000)
        {
            Serial.printf("[MQ135] Aufwärmen: %lu Sekunden...\n", aufwaermDauer / 1000);
        }

        // ADC-Wert einlesen (0-4095)
        int adcWert = analogRead(konfiguration.gpioPin);

        // Spannung berechnen (ESP32: 3.3V Referenz)
        float spannung = (adcWert / 4095.0f) * 3.3f;

        // Widerstand berechnen (Spannungsteiler mit RL = 10kOhm)
        float widerstand = 0;
        if (spannung > 0.01f)
        {
            widerstand = (3.3f - spannung) / spannung * 10000.0f;
        }

        // ppm-Äquivalent für Luftqualität berechnen
        // MQ-135 ist empfindlich für verschiedene Gase
        float ppm = berechnePPM(widerstand);

        // Messwert speichern
        aktualisiereMesswert(ppm, SensorStatus::OK);

        // Debug-Ausgabe
        Serial.printf("[MQ135] %s: ADC=%d, Spannung=%.2fV, Widerstand=%.0f Ohm, CO2~%.0f ppm\n",
                     konfiguration.sensorId.c_str(), adcWert, spannung, widerstand, ppm);

        return true;
    }

    /**
     * @brief Kalibriert den Sensor in frischer Außenluft (400-450 ppm CO2)
     * @details Muss bei offenem Fenster oder draußen aufgerufen werden!
     */
    void kalibrierenInFrischerLuft()
    {
        Serial.println("[MQ135] Kalibrierung in frischer Luft - Fenster öffnen!");

        // 30 Messungen über 30 Sekunden mitteln
        float summe = 0;
        for (int i = 0; i < 30; i++)
        {
            int adcWert = analogRead(konfiguration.gpioPin);
            float spannung = (adcWert / 4095.0f) * 3.3f;
            float widerstand = (3.3f - spannung) / spannung * 10000.0f;
            summe += widerstand;
            delay(1000);
        }

        luftwert = summe / 30.0f;
        istKalibriert = true;

        Serial.printf("[MQ135] Kalibrierung abgeschlossen: R0 = %.0f Ohm\n", luftwert);
        Serial.println("[MQ135] Hinweis: In den nächsten 24h wird Sensor noch genauer!");
    }

    /**
     * @brief Setzt den Schwellwert für schlechte Luftqualität
     * @param schwelle ppm-Wert für Warnung (typisch: 800-1000 ppm)
     */
    void setzeSchwellwert(float schwelle)
    {
        alarmSchwelle = schwelle;
    }

    /**
     * @brief Gibt eine Text-Beschreibung der Luftqualität
     * @return String mit Qualitätsstufe
     */
    String getLuftqualitaet() const
    {
        float ppm = messwert.wert;

        if (ppm < 600)
        {
            return "Gut";
        }
        else if (ppm < 800)
        {
            return "Mittel";
        }
        else if (ppm < 1000)
        {
            return "Schlecht";
        }
        else
        {
            return "Gefährlich";
        }
    }

    /**
     * @brief Prüft ob Alarm ausgelöst werden soll
     */
    bool alarmAusloesen() const
    {
        return messwert.wert > alarmSchwelle;
    }

private:
    /** @brief Referenzwiderstand in frischer Luft (R0) */
    float luftwert;

    /** @brief true wenn Kalibrierung durchgeführt */
    bool istKalibriert;

    /** @brief Startzeit der Aufwärmphase */
    unsigned long aufwaermzeitStart;

    /** @brief Schwellwert für Alarm */
    float alarmSchwelle = 800.0f;  // WHO-Richtwert: 1000 ppm CO2

    /**
     * @brief Berechnet ppm-Äquivalent aus Widerstand
     * @details Verwendet eine typische Kennlinie für MQ-135
     *          Die Werte sind SCHÄTZUNGEN und nicht exakt!
     *
     * Typische Referenzwerte (in sauberer Luft ~400ppm CO2):
     * - Rs/Ro ≈ 1.0 (in kalibrierter Umgebung)
     * - Rs/Ro ≈ 2-4 (in belüftetem Raum)
     * - Rs/Ro ≈ 8-10 (in schlecht belüftetem Raum)
     *
     * Umrechnung: ppm = 116.602 * (Rs/Ro)^-2.769 (für CO2-Äquivalent)
     */
    float berechnePPM(float widerstand)
    {
        // Standardwert falls nicht kalibriert
        if (luftwert <= 0)
        {
            // Typischer Wert für unbeheizten Sensor in Raumluft
            luftwert = 30000.0f;  // ~30 kOhm
        }

        float verhaeltnis = widerstand / luftwert;

        // CO2-Äquivalent Berechnung (vereinfacht)
        // Formel basiert auf typischer MQ-135 Kennlinie
        float ppm = 0;

        if (verhaeltnis > 0.1f)
        {
            ppm = 116.602f * pow(verhaeltnis, -2.769f);
        }

        // ppm auf physiologischen Bereich begrenzen
        ppm = constrain(ppm, 0.0f, 5000.0f);

        return ppm;
    }
};

#endif // MQ135_SENSOR_H
