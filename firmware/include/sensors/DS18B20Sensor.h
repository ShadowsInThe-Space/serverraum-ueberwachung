/**
 * @file DS18B20Sensor.h
 * @brief Konkrete Sensor-Klasse für DS18B20 (1-Wire Temperatursensor)
 * @details Implementiert die abstrakte Sensor-Schnittstelle für den DS18B20-Sensor.
 *          Der DS18B20 ist ein digitaler 1-Wire Temperatursensor mit hoher Genauigkeit.
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * @version 1.0
 *
 * Hardware: DS18B20 Temperatursensor
 * Pin-Belegung: Siehe Tech-Specs (GPIO 5, 1-Wire Bus)
 *
 * Funktionsweise 1-Wire:
 * - Serielle Kommunikation über einzige Datenleitung
 * - Jeder Sensor hat eindeutige 64-Bit Seriennummer
 * - Mehrere Sensoren können an derselben Leitung betrieben werden (Bus)
 * - Parasitäre Stromversorgung möglich (nur 2 Drähte statt 3)
 *
 * Vorteile gegenüber DHT22:
 * - Genauere Temperaturmessung (±0.5°C vs ±0.5°C, aber stabiler)
 * - Längere Kabel möglich (bis 100m!)
 * - Mehrere Sensoren an einem Pin möglich
 *
 * Nachteile:
 * - Benötigt OneWire Bibliothek
 * - Etwas komplexere Verkabelung (4.7kΩ Pullup-Widerstand)
 *
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

#ifndef DS18B20_SENSOR_H
#define DS18B20_SENSOR_H

#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "Sensor.h"

/**
 * @class DS18B20Sensor
 * @brief Konkrete Implementierung für DS18B20-Temperatursensor
 * @details Erbt von der abstrakten Sensor-Klasse.
 *
 * Technische Daten DS18B20:
 * - Messbereich: -55°C bis +125°C
 * - Genauigkeit: ±0.5°C im Bereich -10°C bis +85°C
 * - Auflösung: 9-12 Bit (konfigurierbar, entspricht 0.5°C bis 0.0625°C)
 * - Ansprechzeit: ~750ms bei 12-Bit Auflösung
 * - Spannung: 3.0V bis 5.5V
 */
class DS18B20Sensor : public Sensor
{
public:
    /**
     * @brief Konstruktor für DS18B20-Sensor
     * @param pin GPIO-Pin für 1-Wire Bus
     * @param sensorId Eindeutige ID für diesen Sensor
     * @param messintervall Zeit in ms zwischen Messungen (mindestens 750ms!)
     *
     * @note Mehrere DS18B20 können am selben Pin betrieben werden!
     *       Jeder Sensor wird über seine eindeutige ID identifiziert.
     */
    DS18B20Sensor(int pin, String sensorId, unsigned long messintervall = 1000)
        : Sensor(pin, sensorId, SensorTyp::DS18B20, messintervall, true)
    {
        // OneWire Instanz erstellen
        oneWireSensor = new OneWire(pin);

        // DallasTemperature mit OneWire initialisieren
        dallasSensor = new DallasTemperature(oneWireSensor);

        // Geräte-Adresse initialisieren (wird in init() ermittelt)
        memset(sensorAdresse, 0, 8);
    }

    /**
     * @brief Destruktor
     */
    ~DS18B20Sensor() override
    {
        delete dallasSensor;
        delete oneWireSensor;
    }

    /**
     * @brief Initialisiert den DS18B20-Sensor
     * @return true wenn Initialisierung erfolgreich
     *
     * Aufgaben:
     * 1. 1-Wire Bus initialisieren
     * 2. Sensor(en) suchen und Adressen ermitteln
     * 3. Auflösung konfigurieren (12 Bit = 0.0625°C Genauigkeit)
     */
    bool init() override
    {
        // Starte 1-Wire Bibliothek
        oneWireSensor->reset_search();

        // Initialisiere DallasTemperature-Bibliothek (KRITISCH!)
        dallasSensor->begin();

        // Suche nach Sensoren am Bus
        // Jeder DS18B20 hat eindeutige 64-Bit Seriennummer
        if (!oneWireSensor->search(sensorAdresse))
        {
            // Kein Sensor gefunden!
            Serial.println("[DS18B20] Fehler: Kein Sensor gefunden an GPIO " + String(konfiguration.gpioPin));
            messwert.status = SensorStatus::NICHT_VERFUEGBAR;
            return false;
        }

        // Prüfe CRC der Adresse (Fehlererkennung)
        if (OneWire::crc8(sensorAdresse, 7) != sensorAdresse[7])
        {
            Serial.println("[DS18B20] Fehler: CRC-Prüfung fehlgeschlagen!");
            messwert.status = SensorStatus::FEHLER;
            return false;
        }

        // Prüfe ob es wirklich ein DS18B20 ist
        // Das erste Byte der Adresse sollte 0x28 sein
        if (sensorAdresse[0] != 0x28)
        {
            Serial.println("[DS18B20] Fehler: Kein DS18B20 gefunden!");
            messwert.status = SensorStatus::FEHLER;
            return false;
        }

        // Setze Auflösung auf 12 Bit (höchste Genauigkeit)
        dallasSensor->setResolution(sensorAdresse, 12);

        // Starte erste Messung (asynchron - wird in messen() abgerufen)
        dallasSensor->requestTemperatures();

        messwert.status = SensorStatus::OK;

        // Gebe Sensor-Adresse aus (zur Kontrolle)
        Serial.print("[DS18B20] Initialisiert: GPIO ");
        Serial.println(konfiguration.gpioPin);
        Serial.print("[DS18B20] Sensor-Adresse: ");
        for (uint8_t i = 0; i < 8; i++)
        {
            Serial.print(" ");
            Serial.print(sensorAdresse[i], HEX);
        }
        Serial.println();

        return true;
    }

    /**
     * @brief Führt eine Temperatur-Messung durch
     * @return true wenn Messung erfolgreich
     *
     * Ablauf:
     * 1. Prüfe ob vorherige Messung abgeschlossen (mindestens 750ms)
     * 2. Temperatur von Sensor abrufen
     * 3. Auf Fehler prüfen (Sensor nicht angeschlossen, etc.)
     * 4. Nächste Messung anfordern (asynchron)
     */
    bool messen() override
    {
        if (!konfiguration.enabled)
        {
            return false;
        }

        // Prüfe ob Sensor initialisiert wurde
        if (sensorAdresse[0] == 0)
        {
            Serial.println("[DS18B20] Fehler: Sensor nicht initialisiert!");
            return false;
        }

        // Lese Temperatur vom Sensor
        // Die Temperatur wird intern nach requestTemperatures() gespeichert
        float temperatur = dallasSensor->getTempC(sensorAdresse);

        // Prüfe auf Fehlerwerte
        // -127.0 = Sensor nicht angeschlossen oder Fehler
        // +85.0 = Reset während Messung
        if (temperatur == -127.0f || temperatur == 85.0f)
        {
            aktualisiereMesswert(0.0f, SensorStatus::FEHLER);
            Serial.println("[DS18B20] Fehler: Sensor antwortet nicht!");
            return false;
        }

        // Messwert speichern
        aktualisiereMesswert(temperatur, SensorStatus::OK);

        // Starte nächste Messung (für nächsten Zyklus)
        dallasSensor->requestTemperatures();

        // Debug-Ausgabe
        Serial.printf("[DS18B20] %s: %.2f°C\n", konfiguration.sensorId.c_str(), temperatur);

        return true;
    }

    /**
     * @brief Gibt die Sensor-Adresse als String zurück
     * @return Hex-String der 64-Bit Adresse
     */
    String getAdresseAlsString() const
    {
        String adresse = "";
        for (uint8_t i = 0; i < 8; i++)
        {
            if (sensorAdresse[i] < 16)
            {
                adresse += "0";
            }
            adresse += String(sensorAdresse[i], HEX);
            if (i < 7)
            {
                adresse += ":";
            }
        }
        return adresse;
    }

    /**
     * @brief Scannt alle Sensoren am Bus und gibt Anzahl zurück
     * @param pin GPIO-Pin des 1-Wire Busses
     * @return Anzahl gefundener Sensoren
     */
    static int anzahlSensorenSuchen(int pin)
    {
        OneWire oneWire(pin);
        DallasTemperature tempSensor(&oneWire);
        tempSensor.begin();

        return tempSensor.getDeviceCount();
    }

private:
    /** @brief OneWire Instanz für 1-Wire Kommunikation */
    OneWire* oneWireSensor;

    /** @brief DallasTemperature Bibliotheks-Instanz */
    DallasTemperature* dallasSensor;

    /** @brief 64-Bit Adresse des Sensors (eindeutige Seriennummer) */
    uint8_t sensorAdresse[8];
};

#endif // DS18B20_SENSOR_H
