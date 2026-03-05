/**
 * @file DisplayManager.cpp
 * @brief Implementierung des Display-Managers
 * @details TFT_eSPI Kachel-Dashboard fuer Serverraum-Ueberwachung.
 *          5 Kacheln: Temperatur | Feuchte | PIR (oben)
 *                     Rauchgas   | Luftqualitaet (unten)
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 */

#include "DisplayManager.h"
#include <WiFi.h>

// ============================================================================
// Globale TFT-Instanz (fuer LVGL Flush-Callback)
// ============================================================================
static TFT_eSPI tft_global;

// ============================================================================
// LVGL statische Member-Initialisierung
// ============================================================================
lv_disp_draw_buf_t DisplayManager::draw_buf;
lv_color_t         DisplayManager::lv_draw_buf[DISP_BREITE * 20];
lv_disp_drv_t      DisplayManager::disp_drv;

// ============================================================================
// LVGL Farb-Konstanten
// ============================================================================
static const lv_color_t FARBE_KACHEL_BG    = LV_COLOR_MAKE(0, 100, 0);      // Dunkelgruen
static const lv_color_t FARBE_KACHEL_TEXT  = LV_COLOR_MAKE(0, 0, 139);      // Navy
static const lv_color_t FARBE_KACHEL_LABEL = LV_COLOR_MAKE(170, 170, 170);  // Hellgrau
static const lv_color_t FARBE_ALARM_BG     = LV_COLOR_MAKE(180, 0, 0);      // Dunkelrot
static const lv_color_t FARBE_ALARM_TEXT   = LV_COLOR_MAKE(255, 220, 0);    // Gelb
static const lv_color_t FARBE_DETAIL_BG    = LV_COLOR_MAKE(12, 12, 20);     // Fast schwarz
static const lv_color_t FARBE_HEADER_BG    = LV_COLOR_MAKE(0, 80, 0);       // Header-Gruen
static const lv_color_t FARBE_CHART_LINIE  = LV_COLOR_MAKE(0, 200, 80);     // Gruene Linie
static const lv_color_t FARBE_WEISS        = LV_COLOR_MAKE(255, 255, 255);

// ============================================================================
// Konstruktor / Destruktor
// ============================================================================

DisplayManager::DisplayManager()
    : ist_alarm(false),
      aktuelle_szene(0),
      szene_start_ms(0),
      scr_uebersicht(nullptr),
      scr_detail(nullptr),
      uebersicht_countdown(nullptr),
      detail_titel(nullptr),
      detail_aktuell(nullptr),
      detail_seite(nullptr),
      detail_chart(nullptr),
      detail_serie(nullptr),
      detail_min(nullptr),
      detail_avg(nullptr),
      detail_max(nullptr),
      detail_countdown(nullptr)
{
    for (int i = 0; i < ANZAHL_SENSOREN; i++)
    {
        wert[i]        = 0.0f;
        alarm_flag[i]  = false;
        chart_index[i] = 0;
        chart_anzahl[i] = 0;
        kachel_bg[i]   = nullptr;
        kachel_name[i] = nullptr;
        kachel_wert[i] = nullptr;
        kachel_einh[i] = nullptr;
        for (int j = 0; j < CHART_PUNKTE; j++)
            chart_puffer[i][j] = 0.0f;
    }
}

DisplayManager::~DisplayManager() {}

// ============================================================================
// LVGL Flush-Callback (statisch, kein this-Pointer)
// ============================================================================

void DisplayManager::lvgl_flush_cb(lv_disp_drv_t* drv,
                                    const lv_area_t* area,
                                    lv_color_t* color_p)
{
    uint32_t w = area->x2 - area->x1 + 1;
    uint32_t h = area->y2 - area->y1 + 1;

    // LV_COLOR_16_SWAP=1 -> Bytes schon getauscht -> swap=true in pushColors
    tft_global.startWrite();
    tft_global.setAddrWindow(area->x1, area->y1, w, h);
    tft_global.pushColors((uint16_t*)color_p, w * h, true);
    tft_global.endWrite();

    lv_disp_flush_ready(drv);
}

// ============================================================================
// init()
// ============================================================================

void DisplayManager::init()
{
    Serial.println("\n=== Display + LVGL initialisieren ===");

    // --- TFT RST manuell toggeln (Stabilitaet bei Boot) ---
    #ifdef TFT_RST
    if (TFT_RST >= 0)
    {
        pinMode(TFT_RST, OUTPUT);
        digitalWrite(TFT_RST, LOW);
        delay(100);
        digitalWrite(TFT_RST, HIGH);
        delay(200);
    }
    #endif

    tft_global.init();
    tft_global.setRotation(1);    // Querformat: 320x170
    tft_global.fillScreen(TFT_BLACK);

    // --- Hintergrundbeleuchtung einschalten ---
    #ifdef TFT_BL
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH);
    #endif

    delay(100);
    Serial.println("[Display] TFT bereit");

    // --- LVGL initialisieren ---
    lv_init();

    // --- Draw-Buffer: 20 Zeilen = 320*20*2 = 12.8 KB ---
    lv_disp_draw_buf_init(&draw_buf, lv_draw_buf, nullptr, DISP_BREITE * 20);

    // --- Display-Treiber registrieren ---
    lv_disp_drv_init(&disp_drv);
    disp_drv.hor_res  = DISP_BREITE;
    disp_drv.ver_res  = DISP_HOEHE;
    disp_drv.flush_cb = lvgl_flush_cb;
    disp_drv.draw_buf = &draw_buf;
    lv_disp_drv_register(&disp_drv);

    Serial.println("[LVGL] Treiber registriert");

    // --- Screens erstellen ---
    erstelleUebersichtScreen();
    erstelleDetailScreen();

    // --- Uebersicht als Startbildschirm ---
    lv_scr_load(scr_uebersicht);
    aktuelle_szene = 0;
    szene_start_ms = millis();

    // Ersten Render-Durchlauf erzwingen
    lv_timer_handler();
    delay(20);
    lv_timer_handler();

    Serial.println("[LVGL] Dashboard bereit - Szene: Uebersicht");
}

// ============================================================================
// lvglUpdate() - aus loop() aufrufen!
// ============================================================================

void DisplayManager::lvglUpdate()
{
    // LVGL interne Timer: Animationen, Redraws, ...
    lv_timer_handler();

    // Auto-Szenen-Wechsel pruefen
    unsigned long jetzt = millis();
    unsigned long dauer = (aktuelle_szene == 0) ? TIMER_UEBERSICHT_MS
                                                 : TIMER_DETAIL_MS;
    if (jetzt - szene_start_ms >= dauer)
        naechsteSzene();

    // Countdown alle 500ms aktualisieren
    static unsigned long letzter_cd = 0;
    if (jetzt - letzter_cd >= 500)
    {
        aktualisiereCountdownLabel();
        letzter_cd = jetzt;
    }
}

// ============================================================================
// aktualisiereAlleWerte()
// ============================================================================

void DisplayManager::aktualisiereAlleWerte(float temp, float feuchte,
                                            float rauch, float luft, bool pir)
{
    wert[SENSOR_TEMP]    = temp;
    wert[SENSOR_FEUCHTE] = feuchte;
    wert[SENSOR_RAUCH]   = rauch;
    wert[SENSOR_LUFT]    = luft;
    wert[SENSOR_PIR]     = pir ? 1.0f : 0.0f;

    // Ringpuffer befuellen
    fuegeChartPunktHinzu(SENSOR_TEMP,    temp);
    fuegeChartPunktHinzu(SENSOR_FEUCHTE, feuchte);
    fuegeChartPunktHinzu(SENSOR_RAUCH,   rauch);
    fuegeChartPunktHinzu(SENSOR_LUFT,    luft);
    fuegeChartPunktHinzu(SENSOR_PIR,     pir ? 1.0f : 0.0f);

    // Uebersicht-Kacheln aktualisieren
    for (int i = 0; i < ANZAHL_SENSOREN; i++)
        aktualisiereUebersichtKachel(i);

    // Detail-Chart aktualisieren wenn Detail-Screen gerade sichtbar
    if (aktuelle_szene >= 1 && aktuelle_szene <= ANZAHL_SENSOREN)
        aktualisiereDetailAnsicht(aktuelle_szene - 1);
}

// ============================================================================
// setzeSensorAlarm() / setzeAlarmZustand()
// ============================================================================

void DisplayManager::setzeSensorAlarm(const String& sensor, bool alarm)
{
    if      (sensor == "temp")    alarm_flag[SENSOR_TEMP]    = alarm;
    else if (sensor == "feuchte") alarm_flag[SENSOR_FEUCHTE] = alarm;
    else if (sensor == "rauch")   alarm_flag[SENSOR_RAUCH]   = alarm;
    else if (sensor == "luft")    alarm_flag[SENSOR_LUFT]    = alarm;
    else if (sensor == "pir")     alarm_flag[SENSOR_PIR]     = alarm;

    ist_alarm = false;
    for (int i = 0; i < ANZAHL_SENSOREN; i++)
        ist_alarm |= alarm_flag[i];

    // Kacheln neu zeichnen (Farbaenderung bei Alarm)
    for (int i = 0; i < ANZAHL_SENSOREN; i++)
        aktualisiereUebersichtKachel(i);
}

void DisplayManager::setzeAlarmZustand(bool alarm, String nachricht, float messwert)
{
    if      (nachricht.indexOf("Temperatur") >= 0) setzeSensorAlarm("temp",    alarm);
    else if (nachricht.indexOf("Feuchte")    >= 0) setzeSensorAlarm("feuchte", alarm);
    else if (nachricht.indexOf("Rauch")      >= 0 ||
             nachricht.indexOf("rauch")      >= 0) setzeSensorAlarm("rauch",   alarm);
    else if (nachricht.indexOf("Luft")       >= 0 ||
             nachricht.indexOf("luft")       >= 0) setzeSensorAlarm("luft",    alarm);
    else if (nachricht.indexOf("Bewegung")   >= 0) setzeSensorAlarm("pir",     alarm);
    else                                           ist_alarm = alarm;

    Serial.printf("[Display] Alarm: %s = %.1f -> Kachel rot\n",
                  nachricht.c_str(), messwert);
}

// ============================================================================
// Kompatibilitaets-Methoden
// ============================================================================

void DisplayManager::aktualisiereTemperatur(float temperatur, float schwellwert)
{
    wert[SENSOR_TEMP]    = temperatur;
    alarm_flag[SENSOR_TEMP] = (temperatur > schwellwert);
    aktualisiereUebersichtKachel(SENSOR_TEMP);
}

void DisplayManager::aktualisiereStatus(const char* status)
{
    Serial.printf("[Display] Status: %s\n", status);
}

// ============================================================================
// neuStarten() - nach WiFi-Init aufrufen
// ============================================================================

void DisplayManager::neuStarten()
{
    Serial.println("[Display] Neustart nach WiFi-Init...");
    delay(200);

    #ifdef TFT_RST
    if (TFT_RST >= 0)
    {
        pinMode(TFT_RST, OUTPUT);
        digitalWrite(TFT_RST, LOW);
        delay(50);
        digitalWrite(TFT_RST, HIGH);
        delay(150);
    }
    #endif

    tft_global.init();
    tft_global.setRotation(1);

    #ifdef TFT_BL
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH);
    #endif

    delay(100);

    // Aktuell aktiven Screen komplett neu rendern
    lv_obj_invalidate(lv_scr_act());
    lv_timer_handler();

    Serial.println("[Display] Neustart abgeschlossen.");
}

// ============================================================================
// naechsteSzene()
// ============================================================================

void DisplayManager::naechsteSzene()
{
    // 0 (Uebersicht) -> 1 (Temp) -> 2 (Feuchte) -> 3 (Rauch)
    //   -> 4 (Luft) -> 5 (PIR) -> 0 (Uebersicht) -> ...
    aktuelle_szene = (aktuelle_szene + 1) % (ANZAHL_SENSOREN + 1);
    szene_start_ms = millis();

    if (aktuelle_szene == 0)
    {
        lv_scr_load_anim(scr_uebersicht, LV_SCR_LOAD_ANIM_FADE_ON, 200, 0, false);
        Serial.println("[Display] Szene: Uebersicht");
    }
    else
    {
        int sensor_idx = aktuelle_szene - 1;
        aktualisiereDetailAnsicht(sensor_idx);
        lv_scr_load_anim(scr_detail, LV_SCR_LOAD_ANIM_FADE_ON, 200, 0, false);
        Serial.printf("[Display] Szene: Detail %s\n", getSensorName(sensor_idx));
    }
}

// ============================================================================
// aktualisiereCountdownLabel()
// ============================================================================

void DisplayManager::aktualisiereCountdownLabel()
{
    unsigned long dauer     = (aktuelle_szene == 0) ? TIMER_UEBERSICHT_MS
                                                     : TIMER_DETAIL_MS;
    unsigned long vergangen = millis() - szene_start_ms;
    int sek_rest = (vergangen < dauer) ? (int)((dauer - vergangen) / 1000) : 0;

    char buf[40];

    if (aktuelle_szene == 0 && uebersicht_countdown != nullptr)
    {
        snprintf(buf, sizeof(buf), "> Detail in %ds", sek_rest);
        lv_label_set_text(uebersicht_countdown, buf);
    }
    else if (aktuelle_szene > 0 && detail_countdown != nullptr)
    {
        int naechster = (aktuelle_szene % (ANZAHL_SENSOREN + 1));
        if (naechster == 0)
            snprintf(buf, sizeof(buf), "> Uebersicht in %ds", sek_rest);
        else
            snprintf(buf, sizeof(buf), "> %s in %ds",
                     getSensorName(naechster - 1), sek_rest);
        lv_label_set_text(detail_countdown, buf);
    }
}

// ============================================================================
// erstelleUebersichtScreen()
// Layout: (320x156px Kacheln) + (14px Countdown-Zeile)
//   Reihe 1 (3 Kacheln, h=78): TEMP(107px) | FEUCHTE(107px) | PIR(106px)
//   Reihe 2 (2 Kacheln, h=78): RAUCH(160px) | LUFT(160px)
// ============================================================================

void DisplayManager::erstelleUebersichtScreen()
{
    scr_uebersicht = lv_obj_create(nullptr);
    lv_obj_set_style_bg_color(scr_uebersicht, LV_COLOR_MAKE(5, 5, 5), 0);
    lv_obj_set_style_pad_all(scr_uebersicht, 0, 0);
    lv_obj_clear_flag(scr_uebersicht, LV_OBJ_FLAG_SCROLLABLE);

    const int K_H = 78;   // Kachel-Hoehe
    const int K_Y2 = 78;  // Y-Start Reihe 2

    // Kachel-Layout [x, y, w, h]
    int layout[ANZAHL_SENSOREN][4] = {
        {   0,   0, 107, K_H },   // TEMP
        { 107,   0, 107, K_H },   // FEUCHTE
        { 214,   0, 106, K_H },   // PIR
        {   0, K_Y2, 160, K_H },  // RAUCH
        { 160, K_Y2, 160, K_H },  // LUFT
    };

    for (int i = 0; i < ANZAHL_SENSOREN; i++)
    {
        // Kachel-Container
        lv_obj_t* tile = lv_obj_create(scr_uebersicht);
        lv_obj_set_pos(tile, layout[i][0], layout[i][1]);
        lv_obj_set_size(tile, layout[i][2], layout[i][3]);
        lv_obj_set_style_pad_all(tile, 4, 0);
        lv_obj_set_style_radius(tile, 4, 0);
        lv_obj_set_style_border_width(tile, 1, 0);
        lv_obj_set_style_border_color(tile, LV_COLOR_MAKE(30, 30, 30), 0);
        lv_obj_set_style_bg_color(tile, FARBE_KACHEL_BG, 0);
        lv_obj_clear_flag(tile, LV_OBJ_FLAG_SCROLLABLE);
        kachel_bg[i] = tile;

        // Sensor-Name (oben, klein, hellgrau)
        lv_obj_t* name_lbl = lv_label_create(tile);
        lv_obj_set_style_text_font(name_lbl, &lv_font_montserrat_12, 0);
        lv_obj_set_style_text_color(name_lbl, FARBE_KACHEL_LABEL, 0);
        lv_label_set_text(name_lbl, getSensorName(i));
        lv_obj_align(name_lbl, LV_ALIGN_TOP_MID, 0, 2);
        kachel_name[i] = name_lbl;

        // Messwert (Mitte, gross, navy)
        lv_obj_t* wert_lbl = lv_label_create(tile);
        lv_obj_set_style_text_font(wert_lbl, &lv_font_montserrat_28, 0);
        lv_obj_set_style_text_color(wert_lbl, FARBE_KACHEL_TEXT, 0);
        lv_label_set_text(wert_lbl, "0");
        lv_obj_align(wert_lbl, LV_ALIGN_CENTER, 0, 2);
        kachel_wert[i] = wert_lbl;

        // Einheit (unten, sehr klein, grau)
        lv_obj_t* einh_lbl = lv_label_create(tile);
        lv_obj_set_style_text_font(einh_lbl, &lv_font_montserrat_10, 0);
        lv_obj_set_style_text_color(einh_lbl, FARBE_KACHEL_LABEL, 0);
        lv_label_set_text(einh_lbl, getSensorEinheit(i));
        lv_obj_align(einh_lbl, LV_ALIGN_BOTTOM_MID, 0, -2);
        kachel_einh[i] = einh_lbl;
    }

    // Countdown-Label unten rechts (14px)
    lv_obj_t* cd = lv_label_create(scr_uebersicht);
    lv_obj_set_style_text_font(cd, &lv_font_montserrat_10, 0);
    lv_obj_set_style_text_color(cd, LV_COLOR_MAKE(80, 80, 80), 0);
    lv_label_set_text(cd, "> Detail in 10s");
    lv_obj_align(cd, LV_ALIGN_BOTTOM_RIGHT, -4, -1);
    uebersicht_countdown = cd;
}

// ============================================================================
// erstelleDetailScreen()
// Layout (320x170px):
//   Header  (28px): Sensor-Name | Aktueller Wert | Index "1/5"
//   Chart   (96px): LVGL Liniendiagramm
//   Stats   (30px): Min / Durchschnitt / Max
//   Countdown(16px): Wechselt zu ... in Xs
// ============================================================================

void DisplayManager::erstelleDetailScreen()
{
    scr_detail = lv_obj_create(nullptr);
    lv_obj_set_style_bg_color(scr_detail, FARBE_DETAIL_BG, 0);
    lv_obj_set_style_pad_all(scr_detail, 0, 0);
    lv_obj_clear_flag(scr_detail, LV_OBJ_FLAG_SCROLLABLE);

    // --- Header-Leiste (28px) ---
    lv_obj_t* header = lv_obj_create(scr_detail);
    lv_obj_set_pos(header, 0, 0);
    lv_obj_set_size(header, DISP_BREITE, 28);
    lv_obj_set_style_bg_color(header, FARBE_HEADER_BG, 0);
    lv_obj_set_style_pad_all(header, 3, 0);
    lv_obj_set_style_border_width(header, 0, 0);
    lv_obj_set_style_radius(header, 0, 0);
    lv_obj_clear_flag(header, LV_OBJ_FLAG_SCROLLABLE);

    // Sensor-Titel (links)
    detail_titel = lv_label_create(header);
    lv_obj_set_style_text_font(detail_titel, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(detail_titel, FARBE_WEISS, 0);
    lv_label_set_text(detail_titel, "SENSOR");
    lv_obj_align(detail_titel, LV_ALIGN_LEFT_MID, 4, 0);

    // Aktueller Wert (Mitte)
    detail_aktuell = lv_label_create(header);
    lv_obj_set_style_text_font(detail_aktuell, &lv_font_montserrat_20, 0);
    lv_obj_set_style_text_color(detail_aktuell, LV_COLOR_MAKE(100, 255, 100), 0);
    lv_label_set_text(detail_aktuell, "0");
    lv_obj_align(detail_aktuell, LV_ALIGN_CENTER, 0, 0);

    // Seiten-Indikator (rechts: "1/5")
    detail_seite = lv_label_create(header);
    lv_obj_set_style_text_font(detail_seite, &lv_font_montserrat_12, 0);
    lv_obj_set_style_text_color(detail_seite, LV_COLOR_MAKE(140, 140, 140), 0);
    lv_label_set_text(detail_seite, "1/5");
    lv_obj_align(detail_seite, LV_ALIGN_RIGHT_MID, -4, 0);

    // --- Liniendiagramm (y=30, h=96px) ---
    detail_chart = lv_chart_create(scr_detail);
    lv_obj_set_pos(detail_chart, 2, 30);
    lv_obj_set_size(detail_chart, DISP_BREITE - 4, 96);
    lv_chart_set_type(detail_chart, LV_CHART_TYPE_LINE);
    lv_chart_set_point_count(detail_chart, CHART_PUNKTE);
    lv_chart_set_div_line_count(detail_chart, 3, 5);
    lv_obj_set_style_bg_color(detail_chart, LV_COLOR_MAKE(8, 18, 12), 0);
    lv_obj_set_style_border_color(detail_chart, LV_COLOR_MAKE(40, 70, 40), 0);
    lv_obj_set_style_line_color(detail_chart, LV_COLOR_MAKE(25, 45, 25), LV_PART_MAIN);
    lv_obj_set_style_pad_all(detail_chart, 6, 0);

    // Datenpunkte unsichtbar (nur Linie zeigen)
    lv_obj_set_style_width(detail_chart,  0, LV_PART_INDICATOR);
    lv_obj_set_style_height(detail_chart, 0, LV_PART_INDICATOR);

    // Datenreihe hinzufuegen
    detail_serie = lv_chart_add_series(detail_chart,
                                        FARBE_CHART_LINIE,
                                        LV_CHART_AXIS_PRIMARY_Y);

    // --- Statistik-Labels (y=128, h=28px) ---
    detail_min = lv_label_create(scr_detail);
    lv_obj_set_style_text_font(detail_min, &lv_font_montserrat_12, 0);
    lv_obj_set_style_text_color(detail_min, LV_COLOR_MAKE(80, 180, 255), 0);
    lv_label_set_text(detail_min, "Min: -");
    lv_obj_set_pos(detail_min, 8, 130);

    detail_avg = lv_label_create(scr_detail);
    lv_obj_set_style_text_font(detail_avg, &lv_font_montserrat_12, 0);
    lv_obj_set_style_text_color(detail_avg, LV_COLOR_MAKE(220, 200, 80), 0);
    lv_label_set_text(detail_avg, "Avg: -");
    lv_obj_align(detail_avg, LV_ALIGN_TOP_MID, 0, 130);

    detail_max = lv_label_create(scr_detail);
    lv_obj_set_style_text_font(detail_max, &lv_font_montserrat_12, 0);
    lv_obj_set_style_text_color(detail_max, LV_COLOR_MAKE(255, 100, 60), 0);
    lv_label_set_text(detail_max, "Max: -");
    lv_obj_align(detail_max, LV_ALIGN_TOP_RIGHT, -8, 130);

    // --- Countdown (unten) ---
    detail_countdown = lv_label_create(scr_detail);
    lv_obj_set_style_text_font(detail_countdown, &lv_font_montserrat_10, 0);
    lv_obj_set_style_text_color(detail_countdown, LV_COLOR_MAKE(70, 70, 70), 0);
    lv_label_set_text(detail_countdown, "> ... in 8s");
    lv_obj_align(detail_countdown, LV_ALIGN_BOTTOM_RIGHT, -4, -2);
}

// ============================================================================
// aktualisiereUebersichtKachel()
// ============================================================================

void DisplayManager::aktualisiereUebersichtKachel(int idx)
{
    if (kachel_bg[idx] == nullptr) return;

    bool alarm = alarm_flag[idx];

    // Hintergrund- und Textfarbe je nach Alarmzustand
    lv_obj_set_style_bg_color(kachel_bg[idx],
                               alarm ? FARBE_ALARM_BG : FARBE_KACHEL_BG, 0);
    lv_obj_set_style_text_color(kachel_wert[idx],
                                 alarm ? FARBE_ALARM_TEXT : FARBE_KACHEL_TEXT, 0);

    // Messwert als Text setzen
    String wert_str = formatiereWert(idx);
    lv_label_set_text(kachel_wert[idx], wert_str.c_str());
}

// ============================================================================
// aktualisiereDetailAnsicht()
// ============================================================================

void DisplayManager::aktualisiereDetailAnsicht(int sensor_idx)
{
    if (detail_chart == nullptr) return;

    // Header-Text aktualisieren
    lv_label_set_text(detail_titel, getSensorName(sensor_idx));

    char buf[32];
    snprintf(buf, sizeof(buf), "%d/%d", sensor_idx + 1, ANZAHL_SENSOREN);
    lv_label_set_text(detail_seite, buf);

    // Aktuellen Wert + Einheit anzeigen
    String wert_str = formatiereWert(sensor_idx);
    wert_str += " ";
    wert_str += getSensorEinheit(sensor_idx);
    lv_label_set_text(detail_aktuell, wert_str.c_str());

    // --- Chart-Daten aus Ringpuffer fuellen ---
    int    anzahl  = chart_anzahl[sensor_idx];
    lv_coord_t* y_arr = lv_chart_get_y_array(detail_chart, detail_serie);

    if (anzahl == 0)
    {
        for (int i = 0; i < CHART_PUNKTE; i++)
            y_arr[i] = LV_CHART_POINT_NONE;
    }
    else
    {
        // Ringpuffer chronologisch in Chart-Array schreiben
        int start = (chart_index[sensor_idx] - anzahl + CHART_PUNKTE) % CHART_PUNKTE;
        for (int i = 0; i < CHART_PUNKTE; i++)
        {
            if (i < anzahl)
            {
                int ring_idx = (start + i) % CHART_PUNKTE;
                // *10 um eine Dezimalstelle als Integer darzustellen
                y_arr[i] = (lv_coord_t)(chart_puffer[sensor_idx][ring_idx] * 10);
            }
            else
            {
                y_arr[i] = LV_CHART_POINT_NONE;
            }
        }

        // Y-Achse dynamisch skalieren
        float min_v, avg_v, max_v;
        berechneStatistik(sensor_idx, min_v, avg_v, max_v);

        float range = max_v - min_v;
        if (range < 5.0f) range = 5.0f;

        lv_chart_set_range(detail_chart, LV_CHART_AXIS_PRIMARY_Y,
                           (lv_coord_t)((min_v - range * 0.15f) * 10),
                           (lv_coord_t)((max_v + range * 0.15f) * 10));

        // Statistik-Labels
        snprintf(buf, sizeof(buf), "Min:%.1f", min_v);
        lv_label_set_text(detail_min, buf);

        snprintf(buf, sizeof(buf), "Avg:%.1f", avg_v);
        lv_label_set_text(detail_avg, buf);

        snprintf(buf, sizeof(buf), "Max:%.1f", max_v);
        lv_label_set_text(detail_max, buf);
    }

    lv_chart_refresh(detail_chart);

    // Alarm-Farbe im Header-Balken
    lv_obj_t* header = lv_obj_get_child(scr_detail, 0);
    if (header)
    {
        lv_obj_set_style_bg_color(header,
                                   alarm_flag[sensor_idx] ? FARBE_ALARM_BG
                                                           : FARBE_HEADER_BG, 0);
    }
}

// ============================================================================
// fuegeChartPunktHinzu() / berechneStatistik()
// ============================================================================

void DisplayManager::fuegeChartPunktHinzu(int idx, float neuer_wert)
{
    chart_puffer[idx][chart_index[idx]] = neuer_wert;
    chart_index[idx] = (chart_index[idx] + 1) % CHART_PUNKTE;
    if (chart_anzahl[idx] < CHART_PUNKTE) chart_anzahl[idx]++;
}

void DisplayManager::berechneStatistik(int idx,
                                        float& min_v, float& avg_v, float& max_v)
{
    int anzahl = chart_anzahl[idx];
    if (anzahl == 0) { min_v = avg_v = max_v = 0.0f; return; }

    min_v = chart_puffer[idx][0];
    max_v = chart_puffer[idx][0];
    float summe = 0.0f;

    for (int i = 0; i < anzahl; i++)
    {
        float v = chart_puffer[idx][i];
        if (v < min_v) min_v = v;
        if (v > max_v) max_v = v;
        summe += v;
    }
    avg_v = summe / (float)anzahl;
}

// ============================================================================
// Hilfsmethoden
// ============================================================================

const char* DisplayManager::getSensorName(int idx)
{
    switch (idx)
    {
        case SENSOR_TEMP:    return "TEMP";
        case SENSOR_FEUCHTE: return "FEUCHTE";
        case SENSOR_RAUCH:   return "RAUCH MQ-2";
        case SENSOR_LUFT:    return "LUFT MQ-135";
        case SENSOR_PIR:     return "BEWEGUNG";
        default:             return "?";
    }
}

const char* DisplayManager::getSensorEinheit(int idx)
{
    switch (idx)
    {
        case SENSOR_TEMP:    return "C";
        case SENSOR_FEUCHTE: return "%";
        case SENSOR_RAUCH:   return "ppm";
        case SENSOR_LUFT:    return "ppm";
        case SENSOR_PIR:     return "";
        default:             return "";
    }
}

String DisplayManager::formatiereWert(int idx)
{
    char buf[16];
    switch (idx)
    {
        case SENSOR_TEMP:
            snprintf(buf, sizeof(buf), "%.1f", wert[idx]);
            break;
        case SENSOR_FEUCHTE:
            snprintf(buf, sizeof(buf), "%.0f", wert[idx]);
            break;
        case SENSOR_RAUCH:
        case SENSOR_LUFT:
            if (wert[idx] < 1.0f)
                snprintf(buf, sizeof(buf), "OK");
            else
                snprintf(buf, sizeof(buf), "%.0f", wert[idx]);
            break;
        case SENSOR_PIR:
            return (wert[idx] > 0.5f) ? "JA" : "NEIN";
        default:
            snprintf(buf, sizeof(buf), "%.1f", wert[idx]);
    }
    return String(buf);
}

lv_color_t DisplayManager::getKachelBg(int idx)
{
    return alarm_flag[idx] ? FARBE_ALARM_BG : FARBE_KACHEL_BG;
}

lv_color_t DisplayManager::getKachelText(int idx)
{
    return alarm_flag[idx] ? FARBE_ALARM_TEXT : FARBE_KACHEL_TEXT;
}
