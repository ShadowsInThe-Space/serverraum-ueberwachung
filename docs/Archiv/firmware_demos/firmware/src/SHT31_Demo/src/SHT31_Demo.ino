/**
 * @file SHT31_SENSOR_Demo.h
 * @brief Einfacher Demo-Code für SHT-31D Sensor
 * @details Testet Temperatur und Luftfeuchtigkeit ohne andere Sensoren.
 * 
 * Hardware:
 * - SHT-31D an GPIO 8 (SCL) und GPIO 9 (SDA)
 * - Betriebsspannung: 3,3V
 * 
 * I2C-Adresse: 0x44 (Standard)
 */

#include <Arduino.h>
#include <Wire.h>

// SHT31 I2C Adressen (teste beide)
const uint8_t SHT31_ADDR_1 = 0x44;
const uint8_t SHT31_ADDR_2 = 0x45;

// I2C Pins - GPIO 8 und 9 (Standard für ESP32-S3)
const int SCL_PIN = 8;
const int SDA_PIN = 9;

void setup()
{
    // Serielle Kommunikation starten
    Serial.begin(115200);
    delay(1000);

    Serial.println("╔═══════════════════════════════════════════════════════╗");
    Serial.println("║   SHT-31D Sensor Demo                                ║");
    Serial.println("╚═══════════════════════════════════════════════════════╝\n");

    // I2C initialisieren mit langsamer Geschwindigkeit
    Wire.begin(SDA_PIN, SCL_PIN);
    Wire.setClock(100000);  // 100kHz statt 400kHz
    
    // SHT-31D Software-Reset senden
    Wire.beginTransmission(SHT31_ADDR_1);
    Wire.write(0x30);  // Soft Reset Command
    Wire.write(0xA2);
    Wire.endTransmission();
    delay(10);

    // Überprüfen ob Sensor antwortet
    Wire.requestFrom(SHT31_ADDR_1, (uint8_t)1);
    if (Wire.available())
    {
        uint8_t status = Wire.read();
        Serial.printf("SHT-31D Status: 0x%02X\n", status);
    }

    Serial.println("\n=== Starte Messung ===\n");
}

void loop()
{
    // Zuerst Adresse 0x44 testen
    uint8_t addr = SHT31_ADDR_1;
    
    // Prüfen ob Gerät antwortet
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() != 0) {
        // 0x44 hat nicht geantwortet, 0x45 versuchen
        addr = SHT31_ADDR_2;
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() != 0) {
            Serial.println("Fehler: Kein SHT-31D gefunden (weder 0x44 noch 0x45)!");
            delay(2000);
            return;
        }
    }
    
    Serial.printf("SHT-31D gefunden an Adresse: 0x%02X\n", addr);

    // Messung starten (Single Shot Mode)
    Wire.beginTransmission(addr);
    Wire.write(0x24);  // High repeatability measurement
    Wire.write(0x00);
    Wire.endTransmission();

    // Warten auf Messung (mindestens 10ms für high repeatability)
    delay(15);

    // Daten lesen (6 Bytes: Temp MSB, Temp LSB, Temp CRC, Hum MSB, Hum LSB, Hum CRC)
    Wire.requestFrom(addr, (uint8_t)6);

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

        // Ausgabe
        Serial.printf("Temperatur:    %.2f °C\n", temperatur);
        Serial.printf("Luftfeuchtigkeit: %.2f %%\n", luftfeuchtigkeit);
        Serial.println("----------------------------------------");
    }
    else
    {
        Serial.println("Fehler: Keine Daten vom SHT-31D empfangen!");
    }

    // 2 Sekunden warten vor nächster Messung
    delay(2000);
}
