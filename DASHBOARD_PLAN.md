# Serverraum-Überwachung Dashboard - Redesign Plan

## Analyse des aktuellen Dashboards

### Probleme:
1. **Barrierefreiheit**:
   - Keine ARIA-Labels
   - Farbcodes ohne zusätzliche Marker (für Farbenblinde nicht nutzbar)
   - Keine Tastaturnavigation
   - Emoji als Icons (nicht barrierefrei)
   - Kontrastverhältnisse nicht geprüft

2. **Ergonomie**:
   - Veraltete Sensor-IDs im Code
   - Verwirrende Tab-Struktur
   - Keine klare Fokusführung
   - Lange Ladezeiten nicht angezeigt

3. **Technisch**:
   - Code-Duplikate (Sensor-IDs mehrfach definiert)
   - Mischung aus dt. und engl. Bezeichnern

---

## Neues Dashboard Konzept

### Design-Prinzipien

#### 1. Barrierefreiheit (WCAG 2.1 AA)
- **Farbkontraste**: Mindestens 4.5:1 für normalen Text, 3:1 für großen Text
- **Status nicht nur durch Farbe**: Textlabel + Farbe + optional Icon
- **Tastaturnavigation**: Alle interaktiven Elemente mit Tab erreichbar
- **ARIA-Labels**: Vollständige Bildschirmleser-Unterstützung
- **Fokus-Indikatoren**: Deutliche, sichtbare Fokusmarker
- **Keine Zeitlimits**: Aktionen ohne Zwang

#### 2. Ergonomie
- **Klare Hierarchie**: Überschrift → Gruppe → Einzelwert
- **Chunking**: Max 5-7 Sensoren visuell gruppiert
- **Vorhersehbarkeit**: Konsistentes Layout
- **Feedback**: Sofortiges visuelles Feedback bei Aktionen
- **Fehlervermeidung**: Bestätigungen vor kritischen Aktionen

#### 3. Struktur ohne Icons
- **Farb-Label-Kombination**: "Temperatur: 23.5°C" mit grünem Punkt
- **Text statt Icons**: "Bewegung erkannt" statt 🚶
- **Beschreibende Links**: "Sensor: Temperatur Serverraum"

---

## Layout-Struktur

### Header
```
┌─────────────────────────────────────────────────────────────┐
│ Serverraum-Überwachung    [Status: Verbunden]  [Einstellungen] │
└─────────────────────────────────────────────────────────────┘
```

### Hauptbereich

#### 1. System-Status-Leiste (Top)
```
┌─────────────────────────────────────────────────────────────┐
│ Letzte Aktualisierung: 14:32:05  │  ESP32-001  │  WLAN: -65 dBm │
└─────────────────────────────────────────────────────────────┘
```

#### 2. Sensor-Karten (Hauptbereich)
- Grid mit max 3 Spalten (bessere Lesbarkeit)
- Jede Karte enthält:
  - Sensorname (Überschrift)
  - Aktueller Wert (groß, zentral)
  - Einheit
  - Status-Label ("Normal", "Warnung", "Alarm")
  - Trend-Indikator (optional: "steigend", "fallend", "stabil")
  - Timestamp der letzten Messung

#### 3. Alarm-Bereich
- Collapsible, immer sichtbar wenn Alarme aktiv
- Klare "Quittieren"-Schaltfläche
- Alarm-Liste mit Zeitstempel

#### 4. Tabs (für Detail-Ansichten)
- Verlauf (Chart + Statistik)
- Alarme (historisch)
- Einstellungen

---

## HTML-Struktur

```html
<!-- Sensor-Karte mit voller Barrierefreiheit -->
<article class="sensor-card" aria-labelledby="sensor-temp-name">
    <header>
        <h3 id="sensor-temp-name">Temperatur Serverraum</h3>
        <span class="sensor-typ">DS18B20</span>
    </header>

    <div class="sensor-wert" aria-live="polite">
        <span class="wert">23.5</span>
        <span class="einheit">°C</span>
    </div>

    <div class="sensor-status status-normal" role="status">
        <span class="status-punkt" aria-hidden="true"></span>
        <span class="status-label">Normal</span>
    </div>

    <footer>
        <time datetime="2026-04-26T14:32:05">14:32:05</time>
    </footer>
</article>
```

---

## Tailwind-Klassen

### Farbpalette (mit Kontrasten)
```js
colors: {
    // Status-Farben mit 4.5:1 Kontrast
    status: {
        normal: { DEFAULT: '#22c55e', light: '#86efac', dark: '#166534' },
        warning: { DEFAULT: '#eab308', light: '#fef08a', dark: '#854d0e' },
        alarm: { DEFAULT: '#ef4444', light: '#fca5a5', dark: '#991b1b' },
        inactive: { DEFAULT: '#6b7280', light: '#9ca3af', dark: '#374151' }
    },
    // Textfarben
    text: {
        primary: '#f9fafb',    // Kontrast 15:1 auf dunklem BG
        secondary: '#9ca3af',  // Kontrast 7:1
        muted: '#6b7280'       // Kontrast 4.5:1
    }
}
```

### Sensor-Karte
```html
<div class="bg-gray-800 rounded-lg p-6 border-l-4 border-status-normal">
    <!-- Fokus-Styles für Tastaturnutzer -->
    <button class="focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900">
</div>
```

---

## JavaScript-Architektur

### Module
1. **api.js** - Backend-Kommunikation (vorhanden)
2. **dashboard.js** - Hauptlogik
3. **charts.js** - Diagramme
4. **a11y.js** - Barrierefreiheit-Helper

### Funktionen
```js
// Barrierefreiheit
function updateSensorCard(sensorId, data) {
    // ARIA-live region aktualisieren
    document.getElementById(`sensor-${sensorId}-wert`).textContent = data.wert;
}

function initKeyboardNavigation() {
    // Alle interaktiven Elemente mit Tab-Index
    // Pfeiltasten für Sensor-Karten-Navigation
}

function announceToScreenreader(message) {
    // Visuell-hidden region für Screenreader
}
```

---

## Implementierungs-Reihenfolge

1. **Phase 1: HTML-Grundstruktur**
   - index.html mit Semantic HTML
   - ARIA-Labels
   - Fokus-Management

2. **Phase 2: CSS/Tailwind**
   - Farbpalette mit Kontrasten
   - Responsive Grid
   - Druck-Styles

3. **Phase 3: JavaScript**
   - Sensor-Update-Logik
   - Chart-Integration
   - Keyboard-Navigation

4. **Phase 4: Tests**
   - Lighthouse Accessibility-Check
   - Keyboard-Only Navigation
   - Screenreader-Test

---

## Akzeptanzkriterien

- [ ] Lighthouse Accessibility Score ≥ 90
- [ ] Alle interaktiven Elemente per Tab erreichbar
- [ ] Status ist ohne Farbe erkennbar (Textlabel)
- [ ] Kontrastverhältnis ≥ 4.5:1
- [ ] Keine Emoji/Icons für kritische Informationen
- [ ] Responsive auf Mobile (320px minimum)
- [ ] Alle Formulare mit korrekten Labels
