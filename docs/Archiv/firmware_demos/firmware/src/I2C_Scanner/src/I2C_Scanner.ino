/**
 * @file I2C_Scanner.ino
 * @brief I2C Scanner für ESP32-S3
 * @details Findet alle I2C-Geräte am Bus und zeigt ihre Adressen
 */

#include <Arduino.h>
#include <Wire.h>

// ESP32-S3 hat keine fixed I2C Pins, wir müssen sie definieren
// Default: GPIO 8 (SCL) und GPIO 9 (SDA)

void setup()
{
    Serial.begin(115200);
    delay(1000);

    Serial.println("╔═══════════════════════════════════════════════════════╗");
    Serial.println("║   I2C Scanner                                      ║");
    Serial.println("╚═══════════════════════════════════════════════════════╝\n");

    // Teste verschiedene Pin-Kombinationen
    int sclPins[] = {8, 9, 6, 7};
    int sdaPins[] = {9, 8, 5, 6};
    
    for (int test = 0; test < 4; test++)
    {
        int scl = sclPins[test];
        int sda = sdaPins[test];
        
        Serial.printf("\n=== Teste SCL=GPIO%d, SDA=GPIO%d ===\n", scl, sda);
        
        Wire.begin(sda, scl);
        
        // Scannen
        int count = 0;
        for (uint8_t addr = 1; addr < 127; addr++)
        {
            Wire.beginTransmission(addr);
            uint8_t error = Wire.endTransmission();
            
            if (error == 0)
            {
                Serial.printf("✓ Gerät gefunden bei Adresse: 0x%02X (%d)\n", addr, addr);
                count++;
                
                // Versuche Typ zu identifizieren
                if (addr == 0x44 || addr == 0x45) {
                    Serial.println("  → Vermutlich SHT-31D (Temp/Feuchte)");
                } else if (addr == 0x76 || addr == 0x77) {
                    Serial.println("  → Vermutlich BMP280/BME280 (Temp/Druck)");
                } else if (addr == 0x27) {
                    Serial.println("  → Vermutlich LCD1602/I2C Display");
                } else if (addr == 0x3C) {
                    Serial.println("  → Vermutlich OLED Display (SSD1306)");
                }
            }
            else if (error == 4)
            {
                Serial.printf("✗ Unbekannter Fehler bei Adresse: 0x%02X\n", addr);
            }
        }
        
        if (count == 0) {
            Serial.println("Keine Geräte gefunden!");
        } else {
            Serial.printf("\n=== %d Gerät(e) gefunden ===\n", count);
        }
        
        delay(500);
    }
    
    Serial.println("\n=== Scan abgeschlossen ===");
}

void loop()
{
    delay(10000);  // Nichts tun
}
