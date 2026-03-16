/**
 * @file SHT31Sensor.h
 * @brief Konkrete Sensor-Klasse für SHT31 (I2C Temperatursensor + Feuchtigkeit)
 * @details Implementiert die abstrakte Sensor-Schnittstelle für den SHT31-Sensor.
 *          Der SHT31 ist ein I2C-Sensor für Temperatur und Luftfeuchtigkeit.
 *
 * @author Marc-Dennis Haberland
 * @date 16.03.2026
 * @version 1.0
 *
 * Hardware: SHT31 Sensor (I2C)
 * I2C-Adresse: 0x44 (Standard) oder 0x45
 *
 * Technische Daten SHT31:
 * - Temperatur: -40°C bis +125°C, Genauigkeit ±0.3°C
 * - Luftfeuchtigkeit: 0-100% rF, Genauigkeit ±2% rF
 * - I2C Kommunikation
 * - Spannung: 2.4V - 5.5V
 *
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

#ifndef SHT31_SENSOR_H
#define SHT31_SENSOR_H

#include <Arduino.h>
#include <Wire.h>
#include "Sensor.h"

// SHT31 I2C Adressen
const uint8_t SHT31_ADDR_1 = 0x44;  // Standard-Adresse
const uint8_t SHT31_ADDR_2 = 0x45;  // Alternative Adresse (wenn ADDR Pin auf HIGH)

/**
 * @class SHT31Sensor
 * @brief Konkrete Implementierung für SHT31-Sensor
 * @details Erbt von der abstrakten Sensor-Klasse.
 *          Misst sowohl Temperatur als auch Luftfeuchtigkeit.
 */
class SHT31Sensor : public Sensor
{
public:
    /**
     * @brief Konstruktor für SHT31-Sensor
     * @param sclPin GPIO-Pin für I2C SCL
     * @param sdaPin GPIO-Pin für I2C SDA
     * @param sensorId Eindeutige ID für diesen Sensor
     * @param messintervall Zeit in ms zwischen Messungen
     */
    SHT31Sensor(int sclPin, int sdaPin, String sensorId, unsigned long messintervall = 1000)
        : Sensor(sclPin, sensorId, SensorTyp::SHT31, messintervall, true),
          sclPin(sclPin), sdaPin(sdaPin), i2cAdresse(SHT31_ADDR_1)
    {
        // Wire wird in init() initialisiert
    }

    /**
     * @brief Destruktor
     */
    ~SHT31Sensor() override
    {
        // Keine dynamischen Objekte zu löschen
    }

    /**
     * @brief Initialisiert den SHT31-Sensor
     * @return true wenn Initialisierung erfolgreich
     */
    bool init() override
    {
        Serial.printf("[SHT31] Starte Initialisierung mit SCL=GPIO%d, SDA=GPIO%d\n", sclPin, sdaPin);

        // I2C initialisieren mit benutzerdefinierten Pins
        Wire.begin(sdaPin, sclPin);
        Wire.setClock(100000);  // 100kHz für bessere Stabilität
        delay(100);  // Kurze Pause nach Wire.begin

        // I2C-Scan NACH Wire.begin - immer ausführen!
        Serial.println("[SHT31] === I2C SCAN ===");
        int geraeteGefunden = 0;
        for (uint8_t addr = 1; addr < 127; addr++)
        {
            Wire.beginTransmission(addr);
            uint8_t error = Wire.endTransmission();
            if (error == 0)
            {
                Serial.printf("[SHT31] >>> I2C-Gerät gefunden: 0x%02X\n", addr);
                geraeteGefunden++;
            }
            else if (error != 2)  // 2 = kein Gerät, das ist normal
            {
                Serial.printf("[SHT31] >>> Fehler bei Adresse 0x%02X: %d\n", addr, error);
            }
        }
        Serial.printf("[SHT31] I2C-Scan beendet. Gefunden: %d Geräte\n", geraeteGefunden);

        // Jetzt SHT31 initialisieren
        // Software-Reset senden
        Wire.beginTransmission(i2cAdresse);
        Wire.write(0x30);  // Soft Reset Command
        Wire.write(0xA2);
        if (Wire.endTransmission() != 0)
        {
            Serial.println("[SHT31] Fehler: Soft Reset fehlgeschlagen!");
            // Versuche alternative Adresse
            i2cAdresse = SHT31_ADDR_2;
            Serial.printf("[SHT31] Versuche alternative Adresse 0x%02X\n", i2cAdresse);
            Wire.beginTransmission(i2cAdresse);
            Wire.write(0x30);
            Wire.write(0xA2);
            if (Wire.endTransmission() != 0)
            {
                Serial.println("[SHT31] Fehler: Kein Sensor gefunden!");
                messwert.status = SensorStatus::NICHT_VERFUEGBAR;
                return false;
            }
        }

        messwert.status = SensorStatus::OK;
        Serial.printf("[SHT31] Initialisiert: SCL=GPIO%d, SDA=GPIO%d, Adresse=0x%02X\n",
                      sclPin, sdaPin, i2cAdresse);

        return true;
    }

    /**
     * @brief Führt eine Messung durch
     * @return true wenn Messung erfolgreich
     */
    bool messen() override
    {
        if (!konfiguration.enabled)
        {
            return false;
        }

        // Messung starten (Single Shot Mode, High Repeatability)
        Wire.beginTransmission(i2cAdresse);
        Wire.write(0x24);  // High repeatability measurement
        Wire.write(0x00);
        Wire.endTransmission();

        // Warten auf Messung (mindestens 10ms für high repeatability)
        delay(15);

        // Daten lesen (6 Bytes: Temp MSB, Temp LSB, Temp CRC, Hum MSB, Hum LSB, Hum CRC)
        Wire.requestFrom(i2cAdresse, (uint8_t)6);

        if (Wire.available() == 6)
        {
            uint8_t tempMSB = Wire.read();
            uint8_t tempLSB = Wire.read();
            uint8_t tempCRC = Wire.read();
            uint8_t humMSB = Wire.read();
            uint8_t humLSB = Wire.read();
            uint8_t humCRC = Wire.read();

            // Temperatur berechnen: -45 + 175 * (raw / 65536)
            uint16_t tempRaw = (tempMSB << 8) | tempLSB;
            float temperatur = -45.0f + 175.0f * ((float)tempRaw / 65536.0f);

            // Luftfeuchtigkeit berechnen: 100 * (raw / 65536)
            uint16_t humRaw = (humMSB << 8) | humLSB;
            float luftfeuchtigkeit = 100.0f * ((float)humRaw / 65536.0f);

            // Wir speichern die Temperatur als Hauptwert
            // Die Luftfeuchtigkeit könnte separat abgerufen werden
            aktualisiereMesswert(temperatur, SensorStatus::OK);

            Serial.printf("[SHT31] %s: %.2f°C, %.2f%%\n", 
                          konfiguration.sensorId.c_str(), temperatur, luftfeuchtigkeit);

            return true;
        }
        else
        {
            Serial.println("[SHT31] Fehler: Keine Daten empfangen!");
            aktualisiereMesswert(0.0f, SensorStatus::FEHLER);
            return false;
        }
    }

    /**
     * @brief Gibt die Luftfeuchtigkeit zurück
     * @return Luftfeuchtigkeit in %
     */
    float getLuftfeuchtigkeit() const
    {
        return luftfeuchtigkeit;
    }

private:
    /** @brief SCL Pin */
    int sclPin;
    
    /** @brief SDA Pin */
    int sdaPin;
    
    /** @brief I2C Adresse */
    uint8_t i2cAdresse;
    
    /** @brief Letzte gemessene Luftfeuchtigkeit */
    float luftfeuchtigkeit = 0.0f;
};

#endif // SHT31_SENSOR_H
