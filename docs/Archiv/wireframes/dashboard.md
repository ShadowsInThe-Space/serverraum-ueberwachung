# Wireframes – Serverraum-Dashboard

## Übersicht

Dieses Dokument enthält die Wireframes für das Serverraum-Überwachungs-Dashboard.

---

## 1. Dashboard (Startseite)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🔒 Serverraum-Überwachung                            [Einstellungen]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  🌡️ 22.5°C │  │  💧 45%    │  │  ⚠️ 150 ppm │  │  🚫 Keine  │  │
│  │  Temperatur │  │  Feuchte   │  │  Rauchgas   │  │  Bewegung  │  │
│  │  ─────────  │  │  ─────────  │  │  ─────────  │  │  ─────────  │  │
│  │  ✅ Normal  │  │  ✅ Normal  │  │  ⚡ Warnung  │  │  ✅ Normal  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Letzte Aktualisierung: 15:30:00                                  │  │
│  │ ● Verbunden mit ESP32-001  │  📶 WLAN: -45 dBm                 │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Aktive Alarme:                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ ⚠️ Rauchgas überschritten (150 ppm) - Schwellwert: 200 ppm    │  │
│  │    Sensor: MQ-2  |  Zeit: 15:28:00  |  [Quittieren]          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [Dashboard]  [Verlauf]  [Alarme]  [Einstellungen]                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Elemente:
- **Sensor-Karten (4):** Temperatur, Feuchte, Rauchgas, Bewegung
- **Status-Indikator:** Farbcodierung (grün=normal, gelb=warnung, rot=alarm)
- **Verbindungsstatus:** ESP32-Status, WLAN-Stärke
- **Alarm-Banner:** Aktive Alarme mit Quittieren-Button
- **Navigation:** Untere Navigationsleiste

---

## 2. Verlauf

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🔒 Serverraum-Überwachung                            [Einstellungen]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Sensor: [Temperatur ▼]  Zeitraum: [24h ▼]  [Anzeigen]               │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                │   │
│  │    30┤                              ╭──╮                         │   │
│  │       │                         ╭──╯  ╰──╮                     │   │
│  │    25┤                    ╭──╯           ╰──╮                 │   │
│  │       │               ╭──╯                     ╰──╮            │   │
│  │    20┤          ╭──╯                             ╰──╮         │   │
│  │       │     ╭──╯                                     ╰──╮     │   │
│  │    15┤──╭──╯                                           ╰─│     │   │
│  │       │  │                                                │     │   │
│  │       └──┴────────────────────────────────────────────────┴──   │   │
│  │        00:00   06:00   12:00   18:00   24:00                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Statistik:                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Durchschnitt: 22.3°C  |  Min: 18.5°C  |  Max: 28.7°C         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [Dashboard]  [Verlauf]  [Alarme]  [Einstellungen]                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Elemente:
- **Filter:** Sensorauswahl, Zeitraum (1h, 6h, 24h, 7d, 30d)
- **Linien-Diagramm:** Zeitlicher Verlauf mit Schwellwert-Linie
- **Statistik-Box:** Durchschnitt, Min, Max

---

## 3. Alarme

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🔒 Serverraum-Überwachung                            [Einstellungen]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Filter: [Alle ▼]  Sortieren: [Neueste zuerst ▼]                     │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Status   │ Sensor      │ Typ          │ Wert    │ Zeit      │ Aktion│
│  ├──────────┼─────────────┼──────────────┼─────────┼───────────┼───────┤
│  │ ⚠️ Aktiv │ MQ-2       │ Rauchgas     │ 150 ppm│ 15:28:00 │ [✓]  │
│  ├──────────┼─────────────┼──────────────┼─────────┼───────────┼───────┤
│  │ ✅ Quittiert│ DHT22    │ Temperatur   │ 31.2°C │ 14:15:00 │ [↺]  │
│  ├──────────┼─────────────┼──────────────┼─────────┼───────────┼───────┤
│  │ ✅ Gelöst │ PIR        │ Bewegung     │ true    │ 10:30:00 │       │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Alarm-Details:                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Sensor: MQ-2 (Rauchgas)                                        │   │
│  │ Alarmtyp: Schwellwert überschritten                             │   │
│  │ Messwert: 150 ppm                                              │   │
│  │ Schwellwert: 200 ppm                                           │   │
│  │ Erstellt: 03.03.2026 15:28:00                                 │   │
│  │ [Quittieren] [In Verlauf anzeigen]                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [Dashboard]  [Verlauf]  [Alarme]  [Einstellungen]                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Elemente:
- **Alarm-Liste:** Sortierbare Tabelle mit Status
- **Filter:** Nach Status (alle, aktiv, quittiert, gelöst)
- **Detail-Panel:** Details zum ausgewählten Alarm
- **Aktionen:** Quittieren, In Verlauf anzeigen

---

## 4. Einstellungen

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🔒 Serverraum-Überwachung                            [Einstellungen]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────┐  ┌───────────────────────────────────────┐  │
│  │ Konfiguration        │  │                                       │  │
│  │ ────────────────────│  │ Sensor: DHT22 (Temperatur & Feuchte) │  │
│  │ ▸ Sensoren          │  │ ─────────────────────────────────────  │  │
│  │ ▸ Alarmierung       │  │ Name: [Temperatur & Feuchte      ]    │  │
│  │ ▸ MQTT              │  │ GPIO-Pin: [5    ]                     │  │
│  │ ▸ E-Mail            │  │ Einheit: [°C/%  ]                    │  │
│  │ ▸ System            │  │ [✓] Aktiv                              │  │
│  │                      │  │                                       │  │
│  │                      │  │ ──── Schwellwerte ────                │  │
│  │                      │  │ Min: [15.0] °C                       │  │
│  │                      │  │ Max: [30.0] °C                       │  │
│  │                      │  │                                       │  │
│  │                      │  │ ──── Alarmierung ────                 │  │
│  │                      │  │ [✓] E-Mail                           │  │
│  │                      │  │ [✓] LED                               │  │
│  │                      │  │ [ ] Buzzer                            │  │
│  │                      │  │ [✓] Dashboard                         │  │
│  │                      │  │                                       │  │
│  │                      │  │ [Speichern] [Abbrechen]              │  │
│  └──────────────────────┘  └───────────────────────────────────────┘  │
│                                                                         │
│  [Dashboard]  [Verlauf]  [Alarme]  [Einstellungen]                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Elemente:
- **Navigationsbaum:** Konfigurations-Kategorien
- **Formular:** Sensor-Name, GPIO-Pin, Einheit
- **Schwellwerte:** Min/Max mit Einheiten
- **Alarmierung:** Checkboxen für E-Mail, LED, Buzzer, Dashboard
- **Buttons:** Speichern, Abbrechen

---

## 5. Mobile Ansicht (Responsive)

```
┌─────────────────────┐
│ 🔒 Serverraum      │
├─────────────────────┤
│ ┌───┐ ┌───┐       │
│ │22°│ │45%│       │
│ └───┘ └───┘       │
│ ┌───┐ ┌───┐       │
│ │150│ │ ○ │       │
│ └───┘ └───┘       │
├─────────────────────┤
│ ⚠️ 1 aktiver Alarm │
├─────────────────────┤
│ [Dash] [Verl] [✋] │
└─────────────────────┘
```

---

## Farbschema

| Element | Farbe | Bedeutung |
|---------|-------|----------|
| Normal | Grün (#22c55e) | Wert im normalen Bereich |
| Warnung | Gelb (#eab308) | Wert nähert sich Schwellwert |
| Alarm | Rot (#ef4444) | Schwellwert überschritten |
| Inaktiv | Grau (#6b7280) | Sensor deaktiviert |

## Technologie

- **CSS Framework:** Tailwind CSS
- **Icons:** Heroicons oder Font Awesome
- **Charts:** Chart.js oder ApexCharts
- **Responsive:** Mobile-First mit Breakpoints
