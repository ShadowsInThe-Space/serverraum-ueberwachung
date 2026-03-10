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
        Serial.printf("[DS18B20] Init an GPIO %d\n", konfiguration.gpioPin);

        // Alte Instanzen freigeben und neu aufbauen
        delete dallasSensor;
        delete oneWireSensor;
        oneWireSensor = new OneWire(konfiguration.gpioPin);
        dallasSensor  = new DallasTemperature(oneWireSensor);

        // Bus stabilisieren lassen
        delay(100);

        // DallasTemperature sucht intern alle Geräte (korrekte Methode für ESP32)
        dallasSensor->begin();
        int anzahl = dallasSensor->getDeviceCount();
        Serial.printf("[DS18B20] %d Geraet(e) gefunden an GPIO %d\n", anzahl, konfiguration.gpioPin);

        if (anzahl == 0)
        {
            Serial.printf("[DS18B20] Kein Sensor! Prüfe: GPIO=%d, Pullup 4.7kΩ an 3.3V, VCC, GND\n",
                          konfiguration.gpioPin);
            messwert.status = SensorStatus::NICHT_VERFUEGBAR;
            return false;
        }

        // Adresse des ersten DS18B20 auslesen
        if (!dallasSensor->getAddress(sensorAdresse, 0))
        {
            Serial.println("[DS18B20] Fehler: Adresse konnte nicht gelesen werden!");
            messwert.status = SensorStatus::FEHLER;
            return false;
        }

        // Family-Code prüfen: DS18B20 = 0x28
        if (sensorAdresse[0] != 0x28)
        {
            Serial.printf("[DS18B20] Unbekannter Sensor-Typ: Family=0x%02X\n", sensorAdresse[0]);
            messwert.status = SensorStatus::FEHLER;
            return false;
        }

        // Adresse ausgeben
        Serial.print("[DS18B20] Sensor-Adresse: ");
        for (uint8_t i = 0; i < 8; i++)
            Serial.printf("%02X ", sensorAdresse[i]);
        Serial.println();

        // 12-Bit Auflösung (0.0625°C Genauigkeit, ~750ms Wandlungszeit)
        dallasSensor->setResolution(sensorAdresse, 12);

        // Erste Messung anstoßen (Ergebnis in messen() abrufen)
        dallasSensor->requestTemperatures();

        messwert.status = SensorStatus::OK;
        Serial.printf("[DS18B20] Bereit! GPIO=%d, 12-Bit Auflösung\n", konfiguration.gpioPin);
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

        // Wenn Sensor nicht initialisiert: automatischer Re-Init alle 10 Sekunden
        if (sensorAdresse[0] == 0)
        {
            unsigned long jetzt = millis();
            if (jetzt - letzterReinitVersuch >= 10000)
            {
                letzterReinitVersuch = jetzt;
                Serial.printf("[DS18B20] Kein Sensor an GPIO %d - versuche Re-Init...\n", konfiguration.gpioPin);
                if (!init())
                {
                    return false;
                }
            }
            else
            {
                return false;
            }
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

    /** @brief Zeitstempel des letzten Re-Init-Versuchs (für Cooldown) */
    unsigned long letzterReinitVersuch = 0;
};

#endif // DS18B20_SENSOR_H
