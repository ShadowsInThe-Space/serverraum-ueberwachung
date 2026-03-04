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
#define LV_MEM_CUSTOM          1
#define LV_MEM_SIZE           (32U * 1024U)      /* 32 KB für LVGL */
#define LV_ATTR_MEM_BUSY      1
#define LV_ATTR_MEM_ALIGN    4

/*====================
 *   COLOR SETTINGS
 *====================*/
#define LV_COLOR_DEPTH         16
#define LV_COLOR_16_SWAP      1

/*====================
 *   DISPLAY SETTINGS
 *====================*/
#define LV_HOR_RES_MAX        320
#define LV_VER_RES_MAX        240
#define LV_DPI                100

/*====================
 *   FEATURE SETTINGS
 *====================*/
#define LV_USE_ANIMATION      1
#define LV_USE_GPU            0
#define LV_USE_FILESYSTEM     0
#define LV_USE_LOG            0
#define LV_USE_ASSERT         0

/*====================
 *   FONT SETTINGS
 *====================*/
#define LV_FONT_DEFAULT       &lv_font_montserrat_14

/*====================
 *   INPUT DEVICE SETTINGS
 *====================*/
#define LV_INDEV_READ_PERIOD          50
#define LV_INDEV_POINT_MARKER        0

#endif /*LV_CONF_H*/
