/**
 * @file DS18B20_Test.ino
 * @brief Einfacher DS18B20 Test für ESP32
 * @details Minimaler Code um den Sensor zu testen
 * 
 * Verdrahtung:
 * - VCC -> 3.3V (oder 5V)
 * - GND -> GND
 * - DATA -> GPIO 4 (änderbar)
 * - Pull-Up: 4.7kΩ zwischen DATA und VCC
 */

#include <OneWire.h>
#include <DallasTemperature.h>

// GPIO-Pin für DS18B20
#define DS18B20_PIN 4

// OneWire Instanz
OneWire oneWire(DS18B20_PIN);

// DallasTemperature Instanz
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== DS18B20 Test ===");
  
  // Sensoren suchen
  Serial.println("Suche nach Sensoren...");
  sensors.begin();
  
  int anzahlSensoren = sensors.getDeviceCount();
  Serial.print("Gefundene Sensoren: ");
  Serial.println(anzahlSensoren);
  
  if (anzahlSensoren == 0) {
    Serial.println("FEHLER: Kein Sensor gefunden!");
    Serial.println("Prüfe:");
    Serial.println("  - Verkabelung");
    Serial.println("  - Pull-Up Widerstand (4.7kΩ)");
    Serial.println("  - Sensor angeschlossen?");
  } else {
    Serial.println("Sensor(en) gefunden!");
    
    // Adressen ausgeben
    for (int i = 0; i < anzahlSensoren; i++) {
      DeviceAddress addr;
      sensors.getAddress(addr, i);
      Serial.print("Sensor ");
      Serial.print(i);
      Serial.print(" Adresse: ");
      for (int j = 0; j < 8; j++) {
        Serial.print(addr[j], HEX);
        Serial.print(" ");
      }
      Serial.println();
    }
  }
}

void loop() {
  if (sensors.getDeviceCount() > 0) {
    // Temperatur anfordern
    sensors.requestTemperatures();
    
    // Warten auf Messung (750ms für 12-bit)
    delay(750);
    
    // Temperatur lesen
    float temp = sensors.getTempCByIndex(0);
    
    Serial.print("Temperatur: ");
    Serial.print(temp);
    Serial.println(" °C");
    
    if (temp == DEVICE_DISCONNECTED_C) {
      Serial.println("FEHLER: Sensor nicht verbunden!");
    } else if (temp == -127.0) {
      Serial.println("FEHLER: Sensor antwortet nicht!");
    }
  }
  
  delay(2000);
}
