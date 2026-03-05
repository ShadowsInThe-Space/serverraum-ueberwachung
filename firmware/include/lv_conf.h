/**
 * @file lv_conf.h
 * @brief LVGL Konfiguration für ESP32-S3
 * @details Diese Datei konfiguriert LVGL für den ESP32-S3 mit minimalem Speicherverbrauch.
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 */

#ifndef LV_CONF_H
#define LV_CONF_H

#include <stdint.h>

/*====================
 *   MEMORY SETTINGS
 *====================*/
#define LV_MEM_CUSTOM 0
#define LV_MEM_SIZE           (48U * 1024U)      /* 32 KB für LVGL */

/*====================
 *  HAL EINSTELLUNGEN
 *====================*/
#define LV_DISP_DEF_REFR_PERIOD  30
#define LV_INDEV_DEF_READ_PERIOD 30

/*====================
 *  TICK: millis() als Zeitquelle
 *  -> kein manuelles lv_tick_inc() noetig!
 *====================*/
#define LV_TICK_CUSTOM               1
#define LV_TICK_CUSTOM_INCLUDE       "Arduino.h"
#define LV_TICK_CUSTOM_SYS_TIME_EXPR (millis())

/*====================
 *  FARB-EINSTELLUNGEN (16-Bit RGB565)
 *====================*/
#define LV_COLOR_DEPTH         16
#define LV_COLOR_16_SWAP       1    /* Byte-Swap fuer ST7789 */
#define LV_COLOR_SCREEN_TRANSP 0

/*====================
 *  KOORDINATEN
 *====================*/
#define LV_USE_LARGE_COORD 0

/*====================
 *  LOGGING / ASSERTS (DEAKTIVIERT)
 *====================*/
#define LV_USE_LOG                  0
#define LV_USE_ASSERT_NULL          0
#define LV_USE_ASSERT_MALLOC        0
#define LV_USE_ASSERT_STYLE         0
#define LV_USE_ASSERT_MEM_INTEGRITY 0
#define LV_USE_ASSERT_OBJ           0

/*====================
 *  GRAFIK
 *====================*/
#define LV_DRAW_COMPLEX        1
#define LV_SHADOW_CACHE_SIZE   0
#define LV_IMG_CACHE_DEF_SIZE  0
#define LV_GRADIENT_MAX_STOPS  2
#define LV_GRAD_CACHE_DEF_SIZE 0

/*====================
 *  ANIMATION
 *====================*/
#define LV_USE_ANIMATION 1

/*====================
 *  GRUPPE (kein Touch/Keyboard)
 *====================*/
#define LV_USE_GROUP 0

/*====================
 *  GPU-BESCHLEUNIGER (DEAKTIVIERT)
 *====================*/
#define LV_USE_GPU_STM32_DMA2D  0
#define LV_USE_GPU_NXP_PXP      0
#define LV_USE_GPU_NXP_VG_LITE  0
#define LV_USE_GPU_SDL          0

/*====================
 *  DEBUG-MONITORE (DEAKTIVIERT)
 *====================*/
#define LV_USE_PERF_MONITOR 0
#define LV_USE_MEM_MONITOR  0
#define LV_USE_REFR_DEBUG   0

/*====================
 *  UNICODE
 *====================*/
#define LV_USE_BIDI                 0
#define LV_USE_ARABIC_PERSIAN_CHARS 0

/*====================
 *  WIDGETS - NUR BENOETIGT
 *====================*/
#define LV_USE_ARC        0
#define LV_USE_BAR        1   /* Countdown-Fortschrittsbalken */
#define LV_USE_BTN        0
#define LV_USE_BTNMATRIX  0
#define LV_USE_CANVAS     0
#define LV_USE_CHECKBOX   0
#define LV_USE_CHART      1   /* Liniendiagramm fuer Sensorverlauf */
    #define LV_CHART_AXIS_TICK_LABEL_MAX_LENGTH 256
#define LV_USE_DROPDOWN   0
#define LV_USE_IMG        0
#define LV_USE_LABEL      1   /* Textanzeige fuer Sensorwerte */
    #define LV_LABEL_TEXT_SELECTION 0
    #define LV_LABEL_WAIT_CHAR_COUNT 3
#define LV_USE_LINE       0
#define LV_USE_ROLLER     0
#define LV_USE_SLIDER     0
#define LV_USE_SWITCH     0
#define LV_USE_TEXTAREA   0
    #define LV_TEXTAREA_DEF_PWD_SHOW_TIME 1500
#define LV_USE_TABLE      0

/*====================
 *  EXTRA WIDGETS (DEAKTIVIERT)
 *====================*/
#define LV_USE_SPINNER    0
#define LV_USE_SPINBOX    0   /* Benoetigt LV_USE_TEXTAREA */
#define LV_USE_ANIMIMG    0   /* Benoetigt LV_USE_IMG */
#define LV_USE_MSGBOX     0   /* Benoetigt LV_USE_BTNMATRIX */
#define LV_USE_TABVIEW    0   /* Benoetigt LV_USE_BTNMATRIX */
#define LV_USE_CALENDAR   0
#define LV_USE_TILEVIEW   0
#define LV_USE_WIN        0   /* Benoetigt LV_USE_BTNMATRIX + LV_USE_IMG */
#define LV_USE_SPAN       0
#define LV_USE_MENU       0
#define LV_USE_METER      0
#define LV_USE_SNAPSHOT   0
#define LV_USE_KEYBOARD   0   /* Benoetigt LV_USE_BTNMATRIX + LV_USE_TEXTAREA */
#define LV_USE_COLORWHEEL 0
#define LV_USE_IMGBTN     0   /* Benoetigt LV_USE_IMG */
#define LV_USE_LIST       0

/*====================
 *  LAYOUTS
 *====================*/
#define LV_USE_FLEX 1
#define LV_USE_GRID 0

/*====================
 *  THEME: DARK (passend fuer Serverraum)
 *====================*/
#define LV_USE_THEME_DEFAULT  1
    #define LV_THEME_DEFAULT_DARK            1
    #define LV_THEME_DEFAULT_GROW            0
    #define LV_THEME_DEFAULT_TRANSITION_TIME 80
#define LV_USE_THEME_BASIC 0
#define LV_USE_THEME_MONO  0

/*====================
 *  SCHRIFTEN (MONTSERRAT)
 *  Nur benoetigt Groessen aktivieren!
 *====================*/
#define LV_FONT_DEFAULT &lv_font_montserrat_14

#define LV_FONT_MONTSERRAT_8   0
#define LV_FONT_MONTSERRAT_10  1   /* Einheiten, Countdown */
#define LV_FONT_MONTSERRAT_12  1   /* Statistik Min/Avg/Max */
#define LV_FONT_MONTSERRAT_14  1   /* Sensor-Namen (Standard) */
#define LV_FONT_MONTSERRAT_16  0
#define LV_FONT_MONTSERRAT_18  0
#define LV_FONT_MONTSERRAT_20  1   /* Aktueller Wert in Detailansicht */
#define LV_FONT_MONTSERRAT_22  0
#define LV_FONT_MONTSERRAT_24  0
#define LV_FONT_MONTSERRAT_26  0
#define LV_FONT_MONTSERRAT_28  1   /* Grosse Kachel-Werte */
#define LV_FONT_MONTSERRAT_30  0
#define LV_FONT_MONTSERRAT_32  0
#define LV_FONT_MONTSERRAT_34  0
#define LV_FONT_MONTSERRAT_36  0
#define LV_FONT_MONTSERRAT_38  0
#define LV_FONT_MONTSERRAT_40  0
#define LV_FONT_MONTSERRAT_42  0
#define LV_FONT_MONTSERRAT_44  0
#define LV_FONT_MONTSERRAT_46  0
#define LV_FONT_MONTSERRAT_48  0

#define LV_FONT_MONTSERRAT_12_SUBPX      0
#define LV_FONT_MONTSERRAT_28_COMPRESSED 0
#define LV_FONT_DEJAVU_16_PERSIAN_HEBREW 0
#define LV_FONT_SIMSUN_16_CJK            0
#define LV_FONT_UNSCII_8                 0
#define LV_FONT_UNSCII_16                0

#define LV_FONT_CUSTOM_DECLARE

#define LV_USE_FONT_SUBPX      0
#define LV_USE_FONT_COMPRESSED 0

#define LV_SPRINTF_CUSTOM    0
#define LV_SPRINTF_USE_FLOAT 1

#endif  /* LV_CONF_H */
