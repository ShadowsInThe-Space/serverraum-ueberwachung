/**
 * @file DisplayManager.cpp
 * @brief Implementierung des Display-Managers
 * @details TFT_eSPI Display für Temperaturanzeige
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 */

#include "DisplayManager.h"
#include <WiFi.h>

// ============================================================================
// Globale TFT Instanz
// ============================================================================
TFT_eSPI tft_global;

// ============================================================================
// Konstruktor / Destruktor
// ============================================================================

DisplayManager::DisplayManager() : ist_alarm(false), aktuelle_temperatur(0.0f), schwellwert(30.0f)
{
}

DisplayManager::~DisplayManager()
{
}

// ============================================================================
// Öffentliche Methoden
// ============================================================================

void DisplayManager::init()
{
    Serial.println("\n=== Display initialisieren ===");

    // TFT Display initialisieren
    tft_global.init();
    tft_global.setRotation(1);  // Querformat (320x170)
    tft_global.fillScreen(TFT_BLACK);

    // Hintergrundbeleuchtung einschalten
    #ifdef TFT_BL
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH);
    #endif

    Serial.println("TFT initialisiert");

    // Initiale Anzeige
    zeigeStartbildschirm();

    Serial.println("Display bereit!");
}

void DisplayManager::aktualisiereTemperatur(float temperatur, float schwellwert)
{
    this->aktuelle_temperatur = temperatur;
    this->schwellwert = schwellwert;

    // Prüfen ob Alarm
    bool neuer_alarm = (temperatur > schwellwert);

    // Wenn sich Alarm-Status ändert, neu zeichnen
    if (neuer_alarm != ist_alarm)
    {
        ist_alarm = neuer_alarm;
    }

    // Temperatur anzeigen
    zeigeTemperatur(temperatur, ist_alarm);
}

void DisplayManager::aktualisiereStatus(const char* status)
{
    zeigeStatus(status);
}

void DisplayManager::timerCallback()
{
    // Nicht benötigt bei TFT_eSPI (kein LVGL)
}

// ============================================================================
// Private Methoden
// ============================================================================

void DisplayManager::zeigeStartbildschirm()
{
    // Startbildschirm: Grüner Hintergrund (Normalbetrieb)
    tft_global.fillScreen(TFT_GREEN);

    // Titel
    tft_global.setTextColor(TFT_WHITE, TFT_GREEN);
    tft_global.drawCentreString("Serverraum", 160, 20, 4);

    // Subtitle
    tft_global.setTextColor(TFT_WHITE, TFT_GREEN);
    tft_global.drawCentreString("Ueberwachung", 160, 65, 2);

    // Temperatur-Platzhalter
    tft_global.setTextColor(TFT_WHITE, TFT_GREEN);
    tft_global.drawCentreString("--.- C", 160, 95, 6);

    // Statuszeile
    tft_global.setTextColor(TFT_WHITE, TFT_GREEN);
    tft_global.drawCentreString("Starte...", 160, 148, 2);
}

void DisplayManager::zeigeTemperatur(float temperatur, bool alarm)
{
    // Ganzen Bildschirm in Statusfarbe einfärben
    // Normalbetrieb: Grün | Alarm: Rot
    uint32_t hintergrundFarbe = alarm ? TFT_RED   : TFT_GREEN;
    uint32_t schriftFarbe     = alarm ? TFT_YELLOW : TFT_WHITE;

    tft_global.fillScreen(hintergrundFarbe);

    // Überschrift oben
    tft_global.setTextColor(schriftFarbe, hintergrundFarbe);
    tft_global.drawCentreString("Serverraum", 160, 15, 2);

    // Alarmtext oder OK
    if (alarm)
    {
        tft_global.drawCentreString("!! ALARM !!", 160, 40, 2);
    }
    else
    {
        tft_global.drawCentreString("Status: OK", 160, 40, 2);
    }

    // Temperatur groß in der Mitte
    char buf[32];
    snprintf(buf, sizeof(buf), "%.1f C", temperatur);
    tft_global.setTextColor(schriftFarbe, hintergrundFarbe);
    tft_global.drawCentreString(buf, 160, 80, 6);  // Font 6 = große Zahl
}

void DisplayManager::zeigeStatus(const char* status)
{
    // Hintergrundfarbe je nach Alarmzustand
    uint32_t hintergrundFarbe = ist_alarm ? TFT_RED   : TFT_GREEN;
    uint32_t schriftFarbe     = ist_alarm ? TFT_YELLOW : TFT_WHITE;

    // Status-Bereich unten neu zeichnen (nicht ganzen Screen löschen)
    tft_global.fillRect(0, 140, 320, 30, hintergrundFarbe);
    tft_global.setTextColor(schriftFarbe, hintergrundFarbe);
    tft_global.drawCentreString(status, 160, 148, 2);
}
