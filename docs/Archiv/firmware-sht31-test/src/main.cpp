/**
 * @file main.cpp
 * @brief SHT31 Test-Firmware für ESP32
 * @details Minimale Firmware nur für SHT31 I2C Sensor Test
 *
 * Hardware:
 * - ESP32 DevKit
 * - SHT31 Sensor an GPIO 22 (SCL) und GPIO 21 (SDA)
 */

#include <Arduino.h>
#include <Wire.h>

// SHT31 I2C Adressen
const uint8_t SHT31_ADDR_44 = 0x44;
const uint8_t SHT31_ADDR_45 = 0x45;

// GPIO Pins
const int PIN_SDA = 21;
const int PIN_SCL = 22;

void setup()
{
    Serial.begin(115200);
    delay(500);
    Serial.println("=== SHT31 TEST START ===");
    Serial.printf("I2C Pins: SDA=%d, SCL=%d\n", PIN_SDA, PIN_SCL);

    Wire.begin(PIN_SDA, PIN_SCL);
    Wire.setClock(100000);
    delay(100);

    Serial.println("Scanning I2C bus...");
    int found = 0;
    for (uint8_t addr = 1; addr < 127; addr++)
    {
        Wire.beginTransmission(addr);
        uint8_t err = Wire.endTransmission();
        if (err == 0)
        {
            Serial.printf("Found: 0x%02X\n", addr);
            found++;
        }
    }
    Serial.printf("Scan done: %d devices\n", found);

    if (found == 0)
    {
        Serial.println("NO DEVICES FOUND!");
    }
}

void loop()
{
    static unsigned long last = 0;
    if (millis() - last > 5000)
    {
        last = millis();
        Serial.println("--- Loop ---");

        Wire.beginTransmission(0x44);
        uint8_t err = Wire.endTransmission();
        Serial.printf("0x44: err=%d\n", err);

        if (err == 2)
        {
            Serial.println("NACK - Sensor not found");
        }
    }
}
