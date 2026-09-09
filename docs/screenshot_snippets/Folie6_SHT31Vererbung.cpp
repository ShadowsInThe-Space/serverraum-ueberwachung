/**
 * @file Folie6_SHT31Vererbung.cpp
 * Konkrete Sensor-Klasse erbt von abstrakter Basis
 */

#include <Arduino.h>
#include <Wire.h>
#include "Sensor.h"
#include "SensorData.h"

// Konkrete Klasse erbt von abstrakter Sensor
class SHT31Sensor : public Sensor {
public:
    SHT31Sensor(int sclPin, int sdaPin, String sensorId, unsigned long messintervall = 1000, uint8_t i2cAdresse = 0x44)
        : Sensor(sclPin, sensorId, SensorTyp::SHT31, messintervall, true),
          sclPin(sclPin), sdaPin(sdaPin), i2cAdresse(i2cAdresse) {}

    // Überschreibt abstrakte Methode (override zeigt das!)
    bool init() override {
        Wire.begin(sdaPin, sclPin);
        Wire.setClock(100000);
        return true;
    }

    // Überschreibt abstrakte Methode
    bool messen() override {
        // SHT31: Single-Shot, High Repeatability, Clock Stretching disabled (0x24, 0x00)
        Wire.beginTransmission(i2cAdresse);
        Wire.write(0x24);
        Wire.write(0x00);
        if (Wire.endTransmission() != 0) {
            return false;
        }

        // Maximale Messzeit laut Datenblatt fuer diesen Modus: ca. 15 ms
        delay(15);

        const uint8_t expectedBytes = 6;
        uint8_t receivedBytes = Wire.requestFrom(i2cAdresse, expectedBytes);
        if (receivedBytes != expectedBytes) {
            return false;
        }

        uint8_t tempMsb = Wire.read();
        uint8_t tempLsb = Wire.read();
        uint8_t tempCrc = Wire.read();
        uint8_t humMsb = Wire.read();
        uint8_t humLsb = Wire.read();
        uint8_t humCrc = Wire.read();

        uint8_t temperaturBytes[2] = {tempMsb, tempLsb};
        uint8_t feuchteBytes[2] = {humMsb, humLsb};

        // Datenintegritaet pruefen (SHT31 CRC-8)
        if (!pruefeCrc8(temperaturBytes, tempCrc) || !pruefeCrc8(feuchteBytes, humCrc)) {
            return false;
        }

        uint16_t rawTemp = (static_cast<uint16_t>(tempMsb) << 8) | tempLsb;
        uint16_t rawHum = (static_cast<uint16_t>(humMsb) << 8) | humLsb;
        float temperatur = -45.0f + 175.0f * (static_cast<float>(rawTemp) / 65535.0f);
        luftfeuchtigkeit = 100.0f * (static_cast<float>(rawHum) / 65535.0f);

        aktualisiereMesswert(temperatur, SensorStatus::OK);
        return true;
    }

private:
    bool pruefeCrc8(const uint8_t* daten, uint8_t crcEmpfangen) const {
        uint8_t crc = 0xFF;
        for (uint8_t i = 0; i < 2; i++) {
            crc ^= daten[i];
            for (uint8_t bit = 0; bit < 8; bit++) {
                crc = (crc & 0x80) ? static_cast<uint8_t>((crc << 1) ^ 0x31) : static_cast<uint8_t>(crc << 1);
            }
        }
        return crc == crcEmpfangen;
    }

    int sclPin, sdaPin;
    uint8_t i2cAdresse;
    float luftfeuchtigkeit = 0.0f;
};
