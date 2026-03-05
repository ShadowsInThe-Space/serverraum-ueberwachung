/**
 * @file DisplayManager.h
 * @brief Header-Datei für Display-Manager
 * @details TFT_eSPI Display für Serverraum-Überwachung
 *          Layout: 5 Kacheln (3 oben, 2 unten) mit allen Sensorwerten
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 */

#ifndef DISPLAY_MANAGER_H
#define DISPLAY_MANAGER_H

#include <Arduino.h>
#include <TFT_eSPI.h>
#include <lvgl.h>

// ============================================================================
// SENSOR-INDIZES
// ============================================================================
#define SENSOR_TEMP     0   /* Temperatur (DHT22) */
#define SENSOR_FEUCHTE  1   /* Luftfeuchtigkeit (DHT22) */
#define SENSOR_RAUCH    2   /* Rauchgas (MQ-2) */
#define SENSOR_LUFT     3   /* Luftqualitaet (MQ-135) */
#define SENSOR_PIR      4   /* Bewegung (PIR) */
#define ANZAHL_SENSOREN 5

// ============================================================================
// TIMING DER SZENEN
// ============================================================================
#define TIMER_UEBERSICHT_MS 10000   /* 10s auf der Uebersicht */
#define TIMER_DETAIL_MS      8000   /* 8s pro Detailansicht */

// ============================================================================
// DISPLAY-AUFLOESUNG (Landscape)
// ============================================================================
#define DISP_BREITE 320
#define DISP_HOEHE  170

// ============================================================================
// CHART-DATENPUFFER
// ============================================================================
#define CHART_PUNKTE 20   /* Letzte 20 Messungen im Liniendiagramm */

class DisplayManager
{
private:
    // --- Sensorwerte-Cache ---
    float wert[ANZAHL_SENSOREN];
    bool  alarm_flag[ANZAHL_SENSOREN];
    bool  ist_alarm;

    // --- Chart-Ringpuffer (pro Sensor) ---
    float chart_puffer[ANZAHL_SENSOREN][CHART_PUNKTE];
    int   chart_index [ANZAHL_SENSOREN];
    int   chart_anzahl[ANZAHL_SENSOREN];

    // --- Szenen-Steuerung ---
    // Szene 0 = Uebersicht | Szene 1..5 = Detail Sensor 0..4
    int           aktuelle_szene;
    unsigned long szene_start_ms;

    // --- LVGL: Screens ---
    lv_obj_t* scr_uebersicht;
    lv_obj_t* scr_detail;

    // --- LVGL: Uebersicht-Elemente (5 Kacheln) ---
    lv_obj_t* kachel_bg  [ANZAHL_SENSOREN];
    lv_obj_t* kachel_name[ANZAHL_SENSOREN];
    lv_obj_t* kachel_wert[ANZAHL_SENSOREN];
    lv_obj_t* kachel_einh[ANZAHL_SENSOREN];
    lv_obj_t* uebersicht_countdown;

    // --- LVGL: Detail-Elemente ---
    lv_obj_t*          detail_titel;
    lv_obj_t*          detail_aktuell;
    lv_obj_t*          detail_seite;
    lv_obj_t*          detail_chart;
    lv_chart_series_t* detail_serie;
    lv_obj_t*          detail_min;
    lv_obj_t*          detail_avg;
    lv_obj_t*          detail_max;
    lv_obj_t*          detail_countdown;

    // --- LVGL: Display-Treiber (statisch fuer C-Callbacks) ---
    static lv_disp_draw_buf_t draw_buf;
    static lv_color_t         lv_draw_buf[DISP_BREITE * 20];
    static lv_disp_drv_t      disp_drv;

    // --- Private Methoden ---
    void erstelleUebersichtScreen();
    void erstelleDetailScreen();
    void aktualisiereUebersichtKachel(int idx);
    void aktualisiereDetailAnsicht(int sensor_idx);
    void aktualisiereCountdownLabel();
    void naechsteSzene();

    void   fuegeChartPunktHinzu(int idx, float neuer_wert);
    void   berechneStatistik(int idx, float& min_v, float& avg_v, float& max_v);
    String formatiereWert(int idx);

    const char* getSensorName  (int idx);
    const char* getSensorEinheit(int idx);

    lv_color_t getKachelBg  (int idx);
    lv_color_t getKachelText(int idx);

    static void lvgl_flush_cb(lv_disp_drv_t* drv,
                               const lv_area_t* area,
                               lv_color_t* color_p);

public:
    DisplayManager();
    ~DisplayManager();

    /**
     * @brief Initialisiert TFT + LVGL + erstellt alle Screens
     */
    void init();

    /**
     * @brief Muss regelmaessig aus loop() aufgerufen werden.
     *        Fuehrt LVGL-Timer aus und prueft Auto-Wechsel-Timing.
     */
    void lvglUpdate();

    /**
     * @brief Aktualisiert alle 5 Sensorwerte gleichzeitig
     */
    void aktualisiereAlleWerte(float temp, float feuchte,
                               float rauch, float luft, bool pir);

    /**
     * @brief Setzt Alarmzustand fuer einen einzelnen Sensor
     * @param sensor  "temp" | "feuchte" | "rauch" | "luft" | "pir"
     * @param alarm   true = Alarm aktiv
     */
    void setzeSensorAlarm(const String& sensor, bool alarm);

    /**
     * @brief Wird vom SensorManager bei Alarm aufgerufen
     */
    void setzeAlarmZustand(bool alarm, String nachricht, float wert);

    /**
     * @brief Kompatibilitaets-Methode (kein Effekt auf LVGL-Display)
     */
    void aktualisiereTemperatur(float temperatur, float schwellwert = 30.0f);

    /**
     * @brief Statusmeldung (wird nur auf Serial ausgegeben)
     */
    void aktualisiereStatus(const char* status);

    /**
     * @brief Display nach WLAN-Init neu initialisieren
     */
    void neuStarten();

    /**
     * @brief Gibt zurueck ob mindestens ein Alarm aktiv ist
     */
    bool istAlarmAktiv() const { return ist_alarm; }
};

#endif // DISPLAY_MANAGER_H
