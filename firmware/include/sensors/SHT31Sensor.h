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
        Serial.println("[SHT31] >>> INIT AUFGERUFEN <<<");
        Serial.flush();
        Serial.printf("[SHT31] Starte Initialisierung mit SCL=GPIO%d, SDA=GPIO%d\n", sclPin, sdaPin);
        Serial.flush();

        // I2C initialisieren mit benutzerdefinierten Pins
        Wire.begin(sdaPin, sclPin);
        Wire.setClock(100000);  // 100kHz für bessere Stabilität
        delay(100);  // Kurze Pause nach Wire.begin

        // I2C-Scan NACH Wire.begin - aber nur echte SHT31-Adressen testen
        Serial.println("[SHT31] === I2C SCAN ===");
        int sht31Gefunden = 0;
        uint8_t scanAdressen[2] = {SHT31_ADDR_1, SHT31_ADDR_2};
        const char* scanNamen[2] = {"0x44", "0x45"};

        for (int i = 0; i < 2; i++)
        {
            Wire.beginTransmission(scanAdressen[i]);
            uint8_t error = Wire.endTransmission();
            if (error == 0)
            {
                Serial.printf("[SHT31] >>> I2C Adresse %s antwortet!\n", scanNamen[i]);
                sht31Gefunden++;
            }
            else
            {
                Serial.printf("[SHT31] >>> Adresse %s antwortet nicht (error=%d)\n", scanNamen[i], error);
            }
        }
        Serial.printf("[SHT31] I2C-Scan beendet. %d von 2 SHT31-Adressen antworten\n", sht31Gefunden);
        Serial.flush();

        // Kurze Pause damit Serial Output vollständig übertragen wird
        delay(50);

        // Teste BEIDE SHT31-Adressen systematisch
        bool sensorGefunden = false;
        uint8_t testAdressen[2] = {SHT31_ADDR_1, SHT31_ADDR_2};
        const char* addrNamen[2] = {"0x44 (Standard)", "0x45 (Alternative)"};

        for (int i = 0; i < 2; i++)
        {
            i2cAdresse = testAdressen[i];
            Serial.printf("[SHT31] Teste %s...\n", addrNamen[i]);

            // Prüfe ob Adresse auf I2C-Bus antwortet
            Wire.beginTransmission(i2cAdresse);
            uint8_t txError = Wire.endTransmission();
            Serial.printf("[SHT31]   Transmission: %s\n", txError == 0 ? "ACK" : (txError == 2 ? "NACK (kein Gerät)" : "Fehler"));

            if (txError != 0) continue;

            // SHT31 Break Command senden (stoppt jede laufende Messung)
            Wire.beginTransmission(i2cAdresse);
            Wire.write(0x30);  // Break command
            Wire.write(0x93);
            Wire.endTransmission();
            delay(1);

            // Software-Reset senden
            Wire.beginTransmission(i2cAdresse);
            Wire.write(0x30);  // Soft Reset
            Wire.write(0xA2);
            uint8_t resetError = Wire.endTransmission();
            Serial.printf("[SHT31]   Soft Reset: %s\n", resetError == 0 ? "OK" : "Fehler");
            delay(10);

            // Statusregister lesen (0xF32D)
            Wire.beginTransmission(i2cAdresse);
            Wire.write(0xF3);  // Read Status Register High
            Wire.write(0x2D);
            Wire.endTransmission();

            delay(5);
            Wire.requestFrom(i2cAdresse, (uint8_t)3);
            if (Wire.available() >= 2)
            {
                uint8_t statusHigh = Wire.read();
                uint8_t statusLow = Wire.read();
                uint8_t statusCRC = Wire.read();
                Serial.printf("[SHT31]   Status: 0x%02X 0x%02X (CRC=0x%02X)\n", statusHigh, statusLow, statusCRC);
                sensorGefunden = true;
                Serial.printf("[SHT31] >>> SHT31 gefunden auf %s!\n", addrNamen[i]);
                break;
            }
            else
            {
                Serial.printf("[SHT31]   Keine Daten von %s (available=%d)\n", addrNamen[i], Wire.available());
            }
        }

        if (!sensorGefunden)
        {
            Serial.println("[SHT31] Fehler: Kein SHT31-Sensor gefunden!");
            messwert.status = SensorStatus::NICHT_VERFUEGBAR;
            return false;
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
        if (Wire.endTransmission() != 0)
        {
            Serial.println("[SHT31] Fehler: I2C-Schreibzugriff fehlgeschlagen!");
            aktualisiereMesswert(0.0f, SensorStatus::FEHLER);
            return false;
        }

        // Warten auf Messung (mindestens 10ms für high repeatability)
        delay(15);

        // Daten lesen (6 Bytes: Temp MSB, Temp LSB, Temp CRC, Hum MSB, Hum LSB, Hum CRC)
        uint8_t empfangeneBytes = Wire.requestFrom(i2cAdresse, (uint8_t)6);

        if (empfangeneBytes == 6 && Wire.available() == 6)
        {
            uint8_t tempMSB = Wire.read();
            uint8_t tempLSB = Wire.read();
            uint8_t tempCRC = Wire.read();
            uint8_t humMSB = Wire.read();
            uint8_t humLSB = Wire.read();
            uint8_t humCRC = Wire.read();

            uint8_t temperaturBytes[2] = {tempMSB, tempLSB};
            uint8_t feuchteBytes[2] = {humMSB, humLSB};

            if (!pruefeCrc8(temperaturBytes, tempCRC) || !pruefeCrc8(feuchteBytes, humCRC))
            {
                Serial.println("[SHT31] Fehler: CRC-Pruefung fehlgeschlagen!");
                aktualisiereMesswert(0.0f, SensorStatus::FEHLER);
                return false;
            }

            // Temperatur berechnen: -45 + 175 * (raw / 65536)
            uint16_t tempRaw = (tempMSB << 8) | tempLSB;
            float temperatur = -45.0f + 175.0f * ((float)tempRaw / 65536.0f);

            // Luftfeuchtigkeit berechnen: 100 * (raw / 65536)
            uint16_t humRaw = (humMSB << 8) | humLSB;
            luftfeuchtigkeit = 100.0f * ((float)humRaw / 65536.0f);

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
    /**
     * @brief Prueft SHT31 CRC-8 (Polynom 0x31, Init 0xFF)
     */
    bool pruefeCrc8(const uint8_t* daten, uint8_t crcEmpfangen) const
    {
        uint8_t crc = 0xFF;

        for (uint8_t i = 0; i < 2; i++)
        {
            crc ^= daten[i];
            for (uint8_t bit = 0; bit < 8; bit++)
            {
                if (crc & 0x80)
                {
                    crc = (crc << 1) ^ 0x31;
                }
                else
                {
                    crc <<= 1;
                }
            }
        }

        return crc == crcEmpfangen;
    }

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
