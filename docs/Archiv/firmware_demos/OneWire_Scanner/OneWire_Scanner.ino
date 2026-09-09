/**
 * @file OneWire_Scanner.ino
 * @brief OneWire Geräte Scanner für ESP32
 * @details Scannt alle GPIO-Pins und zeigt gefundene 1-Wire Geräte
 */

#include <OneWire.h>

// Array von GPIOs zum Testen
const int testPins[] = {2, 4, 5, 12, 13, 14, 15, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35};
const int numPins = sizeof(testPins) / sizeof(testPins[0]);

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== OneWire Scanner ===");
  Serial.println("Suche auf allen GPIOs...\n");
  
  int totalFound = 0;
  
  for (int i = 0; i < numPins; i++) {
    int pin = testPins[i];
    Serial.printf("Teste GPIO %d... ", pin);
    
    OneWire oneWire(pin);
    byte addr[8];
    bool found = false;
    
    // 3 Versuche pro Pin
    for (int attempt = 0; attempt < 3; attempt++) {
      if (oneWire.search(addr)) {
        found = true;
        totalFound++;
        break;
      }
      delay(100);
    }
    
    if (found) {
      Serial.print("GERÄT GEFUNDEN! Adresse: ");
      for (int j = 0; j < 8; j++) {
        Serial.printf("%02X ", addr[j]);
      }
      Serial.println();
      
      // Typ erkennen
      Serial.print("  Typ: ");
      switch (addr[0]) {
        case 0x10: Serial.println("DS18S20 (1-Wire Thermometer)"); break;
        case 0x28: Serial.println("DS18B20 (1-Wire Thermometer)"); break;
        case 0x22: Serial.println("DS1822 (1-Wire Thermometer)"); break;
        default: Serial.printf("Unbekannt (0x%02X)", addr[0]); break;
      }
    } else {
      Serial.println("Kein Gerät");
    }
  }
  
  Serial.printf("\n=== Ergebnis ===\n");
  Serial.printf("Gescannte Pins: %d\n", numPins);
  Serial.printf("Gefundene Geräte: %d\n", totalFound);
  
  if (totalFound == 0) {
    Serial.println("\nFEHLER: Keine 1-Wire Geräte gefunden!");
    Serial.println("Mögliche Ursachen:");
    Serial.println("  - Sensor nicht angeschlossen");
    Serial.println("  - Pull-Up Widerstand fehlt");
    Serial.println("  - Falsche Verkabelung");
    Serial.println("  - ESP32 GPIO Problem");
  }
}

void loop() {
  // Nichts tun - einmaliger Scan
  delay(10000);
}
