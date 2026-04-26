/**
 * Serverraum-Überwachung Dashboard
 * ================================
 * Hauptlogik für das Dashboard
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

// Globale Variablen
let aktualisierungsIntervall = null;
let sensorDaten = [];
let alarmDaten = [];

/**
 * Initialisiert das Dashboard
 */
function initDashboard() {
    console.log('Dashboard wird initialisiert...');

    // API-Verbindung prüfen
    window.api.checkApiConnection().then(verbunden => {
        if (verbunden) {
            console.log('API verbunden, lade Daten...');
            ladeSensorDaten();
            ladeAlarmDaten();
            ladeSchwellwerte();
            aktualisiereVerbindungsStatus(true);
            startAutoRefresh();
        } else {
            console.error('API nicht erreichbar');
            aktualisiereVerbindungsStatus(false);
        }
    }).catch(err => {
        console.error('Verbindungsfehler:', err);
        aktualisiereVerbindungsStatus(false);
    });
}

/**
 * Aktualisiert die Verbindungsstatus-Anzeige
 */
function aktualisiereVerbindungsStatus(verbunden) {
    const punkt = document.getElementById('status-punkt');
    const text = document.getElementById('status-text');

    if (punkt && text) {
        if (verbunden) {
            punkt.className = 'w-2 h-2 rounded-full bg-green-500';
            text.textContent = 'Verbunden';
        } else {
            punkt.className = 'w-2 h-2 rounded-full bg-red-500';
            text.textContent = 'Nicht verbunden';
        }
    }
}

/**
 * Lädt alle Sensoren und zeigt sie an
 */
async function ladeSensorDaten() {
    try {
        const sensoren = await window.api.getSensoren();
        sensorDaten = sensoren;
        aktualisiereSensorKarten(sensoren);
        aktualisiereVerlaufSensorDropdown(sensoren);
        aktualisiereZeitstempel();
    } catch (error) {
        console.error('Fehler beim Laden der Sensoren:', error);
    }
}

/**
 * Füllt das Sensor-Dropdown im Verlauf-Tab dynamisch
 */
function aktualisiereVerlaufSensorDropdown(sensoren) {
    const dropdown = document.getElementById('verlauf-sensor');
    if (!dropdown) return;

    dropdown.innerHTML = '';

    // Sensor-Name Mapping für Anzeige
    const sensorNamen = {
        'ds18b20_01': 'Temperatur (DS18B20)',
        'sht31_temp_01': 'Temperatur (SHT31)',
        'sht31_feuchte_01': 'Feuchtigkeit (SHT31)',
        'mq2_01': 'Rauchgas (MQ2)',
        'mq2_2': 'Rauchgas (MQ2)',
        'mq2_6': 'Rauchgas (MQ2)',
        'mq135_3': 'Luftqualität (MQ135)',
        'mq135_7': 'Luftqualität (MQ135)',
        'pir_4': 'Bewegung (PIR)',
        'pir_8': 'Bewegung (PIR)'
    };

    sensoren.forEach(sensor => {
        const option = document.createElement('option');
        option.value = sensor.sensor_id;
        // Versuche den Namen aus dem Sensor-Objekt oder dem Mapping
        option.textContent = sensor.name || sensorNamen[sensor.sensor_id] || sensor.sensor_typ || sensor.sensor_id;
        dropdown.appendChild(option);
    });
}

/**
 * Aktualisiert die Sensor-Karten
 */
function aktualisiereSensorKarten(sensoren) {
    const container = document.getElementById('sensor-karten');
    if (!container) return;

    container.innerHTML = '';

    // Sensor-Konfiguration - IDs müssen mit der DB übereinstimmen
    // DB: ds18b20_01, sht31_temp_01, sht31_feuchte_01, mq2_01, mq2_2, mq2_6, mq135_3, mq135_7, pir_4, pir_8
    const sensorConfig = [
        { id: 'ds18b20_01', name: 'Temperatur (DS18B20)', icon: '🌡️', einheit: '°C' },
        { id: 'sht31_temp_01', name: 'Temperatur (SHT31)', icon: '🌡️', einheit: '°C' },
        { id: 'sht31_feuchte_01', name: 'Feuchtigkeit (SHT31)', icon: '💧', einheit: '%' },
        { id: 'mq2_01', name: 'Rauchgas (MQ2)', icon: '⚠️', einheit: 'ppm' },
        { id: 'pir_4', name: 'Bewegung (PIR)', icon: '🚶', einheit: '' }
    ];

    sensorConfig.forEach(config => {
        const sensor = sensoren.find(s => s.sensor_id === config.id);
        const wert = sensor && sensor.letzte_messung !== null ? sensor.letzte_messung : '--';
        const status = sensor && sensor.letzte_messung !== null ? 'normal' : 'inaktiv';

        const card = document.createElement('div');
        card.className = `bg-gray-800 rounded-xl p-6 status-card border-l-4 ${
            status === 'alarm' ? 'border-red-500' :
            status === 'warnung' ? 'border-yellow-500' :
            status === 'inaktiv' ? 'border-gray-500' : 'border-green-500'
        }`;

        card.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <span class="text-2xl">${config.icon}</span>
                <span class="text-xs text-gray-500 uppercase">${config.name}</span>
            </div>
            <div class="text-3xl font-bold">
                ${wert} ${config.einheit}
            </div>
            <div class="text-sm text-gray-500 mt-1">
                ${sensor && sensor.letzte_zeit ? formatZeitstempel(sensor.letzte_zeit) : 'Keine Daten'}
            </div>
        `;

        container.appendChild(card);
    });
}

/**
 * Lädt alle Alarme
 */
async function ladeAlarmDaten() {
    try {
        const alarme = await window.api.getAlarme('aktiv');
        alarmDaten = alarme;
        zeigeAlarme(alarme);
    } catch (error) {
        console.error('Fehler beim Laden der Alarme:', error);
    }
}

/**
 * Zeigt Alarme im UI
 */
function zeigeAlarme(alarme) {
    const section = document.getElementById('alarme-section');
    const container = document.getElementById('aktive-alarme');

    if (!section || !container) return;

    if (alarme && alarme.length > 0) {
        section.style.display = 'block';
        container.innerHTML = '';

        alarme.forEach(alarm => {
            const div = document.createElement('div');
            div.className = 'bg-red-900/30 border border-red-600 rounded-lg p-4 flex justify-between items-center';

            const alarmTyp = document.createElement('span');
            alarmTyp.className = 'font-medium';
            alarmTyp.textContent = alarm.alarm_typ || 'Alarm';

            const nachricht = document.createElement('span');
            nachricht.className = 'text-gray-400 ml-2';
            nachricht.textContent = alarm.nachricht || '';

            const btn = document.createElement('button');
            btn.className = 'text-sm bg-red-600 hover:bg-red-700 px-3 py-1 rounded';
            btn.textContent = 'Quittieren';
            btn.onclick = () => quittiereAlarm(alarm.id);

            const textDiv = document.createElement('div');
            textDiv.appendChild(alarmTyp);
            textDiv.appendChild(nachricht);

            div.appendChild(textDiv);
            div.appendChild(btn);
            container.appendChild(div);
        });

        // Alarm Overlay anzeigen
        zeigeAlarmOverlay(alarme.length);
    } else {
        section.style.display = 'none';
        // Alarm Overlay ausblenden
        versteckeAlarmOverlay();
    }
}

/**
 * Zeigt den Alarm-Overlay
 */
function zeigeAlarmOverlay(anzahl) {
    const overlay = document.getElementById('alarm-overlay');
    const countElement = document.getElementById('alarm-count');

    if (overlay) {
        if (anzahl > 0) {
            if (countElement) {
                countElement.textContent = anzahl;
            }
            overlay.style.display = 'flex';
        } else {
            overlay.style.display = 'none';
        }
    }
}

/**
 * Versteckt den Alarm-Overlay
 */
function versteckeAlarmOverlay() {
    const overlay = document.getElementById('alarm-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

/**
 * Quittiert alle aktiven Alarme
 */
async function quittiereAlleAlarme() {
    if (!alarmDaten || alarmDaten.length === 0) {
        return;
    }

    try {
        // Alle Alarme sequenziell quittieren
        for (const alarm of alarmDaten) {
            await window.api.quittiereAlarm(alarm.id);
        }

        // Alarm-Daten neu laden
        ladeAlarmDaten();
    } catch (error) {
        console.error('Fehler beim Quittieren aller Alarme:', error);
    }
}

/**
 * Quittiert einen Alarm
 */
async function quittiereAlarm(alarmId) {
    try {
        await window.api.quittiereAlarm(alarmId);
        ladeAlarmDaten();
    } catch (error) {
        console.error('Fehler beim Quittieren:', error);
    }
}

/**
 * Startet automatische Aktualisierung
 */
function startAutoRefresh() {
    if (aktualisierungsIntervall) {
        clearInterval(aktualisierungsIntervall);
    }

    aktualisierungsIntervall = setInterval(() => {
        aktualisiereDaten();
    }, 5000);
}

/**
 * Aktualisiert alle Daten
 */
async function aktualisiereDaten() {
    await Promise.all([
        ladeSensorDaten(),
        ladeAlarmDaten()
    ]);
}

/**
 * Aktualisiert den Zeitstempel der letzten Aktualisierung
 */
function aktualisiereZeitstempel() {
    const element = document.getElementById('letzte-aktualisierung');
    if (element) {
        const jetzt = new Date();
        element.textContent = jetzt.toLocaleTimeString('de-DE');
    }
}

/**
 * Wechselt den aktiven Tab
 */
function wechselTab(tabName) {
    // Tab-Buttons aktualisieren
    document.querySelectorAll('[id^="tab-"]').forEach(btn => {
        btn.classList.remove('border-blue-500', 'text-white');
        btn.classList.add('text-gray-400');
    });

    const aktiverTab = document.getElementById('tab-' + tabName);
    if (aktiverTab) {
        aktiverTab.classList.add('border-blue-500', 'text-white');
        aktiverTab.classList.remove('text-gray-400');
    }

    // Tab-Inhalt aktualisieren
    document.querySelectorAll('[id^="inhalt-"]').forEach(div => {
        div.classList.add('hidden');
    });

    const inhalt = document.getElementById('inhalt-' + tabName);
    if (inhalt) {
        inhalt.classList.remove('hidden');
    }

    // Tab-spezifische Aktionen
    if (tabName === 'verlauf') {
        ladeVerlauf();
    } else if (tabName === 'alarme') {
        ladeAlarme();
    }
}

/**
 * Lädt Verlaufsdaten für Charts
 */
async function ladeVerlauf() {
    const sensorId = document.getElementById('verlauf-sensor')?.value || 'temperatur';
    const stunden = parseInt(document.getElementById('verlauf-zeitraum')?.value || '24');

    try {
        const [messungen, statistik] = await Promise.all([
            window.api.getMessungen(sensorId, 100),
            window.api.getStatistik(sensorId, stunden)
        ]);

        // Chart aktualisieren
        if (window.aktualisiereVerlaufChart) {
            window.aktualisiereVerlaufChart(messungen, sensorId);
        }

        // Statistik anzeigen
        if (statistik) {
            document.getElementById('stat-avg').textContent = statistik?.durchschnitt?.toFixed(1) || '--';
            document.getElementById('stat-min').textContent = statistik?.min?.toFixed(1) || '--';
            document.getElementById('stat-max').textContent = statistik?.max?.toFixed(1) || '--';
        }
    } catch (error) {
        console.error('Fehler beim Laden der Verlaufsdaten:', error);
    }
}

/**
 * Lädt Alarm-Liste
 */
async function ladeAlarme() {
    const filter = document.getElementById('alarm-filter')?.value || 'alle';

    try {
        const alarme = await window.api.getAlarme(filter);
        zeigeAlarmTabelle(alarme);
    } catch (error) {
        console.error('Fehler beim Laden der Alarme:', error);
    }
}

/**
 * Zeigt Alarm-Tabelle
 */
function zeigeAlarmTabelle(alarme) {
    const tbody = document.getElementById('alarm-tabelle');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (!alarme || alarme.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-gray-500 py-4">Keine Alarme vorhanden</td></tr>';
        return;
    }

    alarme.forEach(alarm => {
        const tr = document.createElement('tr');
        tr.className = 'border-b border-gray-700';

        const statusClass = alarm.status === 'aktiv' ? 'text-red-500' : 'text-gray-500';
        const statusIcon = alarm.status === 'aktiv' ? '🔴' : '🟢';

        tr.innerHTML = `
            <td class="py-3 pr-4"><span class="${statusClass}">${statusIcon}</span></td>
            <td class="py-3 pr-4">${alarm.sensor_id || '--'}</td>
            <td class="py-3 pr-4">${alarm.alarm_typ || '--'}</td>
            <td class="py-3 pr-4">${alarm.wert ?? '--'}</td>
            <td class="py-3 pr-4">${alarm.created_at ? new Date(alarm.created_at).toLocaleString('de-DE') : '--'}</td>
            <td class="py-3">
                ${alarm.status === 'aktiv' ? '<button onclick="quittiereAlarm(' + alarm.id + ')" class="text-blue-400 hover:text-blue-300">Quittieren</button>' : '--'}
            </td>
        `;

        tbody.appendChild(tr);
    });
}

/**
 * Zeigt Einstellungen
 */
function zeigeEinstellungen() {
    wechselTab('einstellungen');
}

/**
 * Speichert die Einstellungen
 */
function speichereEinstellungen() {
    const apiEndpoint = document.getElementById('api-endpunkt')?.value;
    const refreshInterval = document.getElementById('refresh-intervall')?.value;

    if (apiEndpoint) {
        window.api.setApiBaseUrl(apiEndpoint);
    }

    if (refreshInterval) {
        localStorage.setItem('refreshInterval', refreshInterval);
    }

    alert('Einstellungen gespeichert!');

    // Seite neu laden für Änderungen
    location.reload();
}

/**
 * Lädt Schwellwerte aus der API
 */
async function ladeSchwellwerte() {
    try {
        const sensoren = await window.api.getSensoren();
        console.log('Sensoren geladen:', sensoren);
    } catch (error) {
        console.error('Fehler beim Laden der Schwellwerte:', error);
    }
}

/**
 * Formatiert einen Zeitstempel
 */
function formatZeitstempel(zeit) {
    if (!zeit) return '--';

    try {
        const jahr = zeit.substring(0, 4);
        const monat = zeit.substring(4, 6);
        const tag = zeit.substring(6, 8);
        const stunde = zeit.substring(8, 10);
        const minute = zeit.substring(10, 12);
        const sekunde = zeit.substring(12, 14);

        return tag + '.' + monat + '.' + jahr + ' ' + stunde + ':' + minute + ':' + sekunde;
    } catch {
        return zeit;
    }
}

// Globale Funktionen für HTML onclick
window.quittiereAlarm = quittiereAlarm;
window.quittiereAlleAlarme = quittiereAlleAlarme;
window.wechselTab = wechselTab;
window.ladeVerlauf = ladeVerlauf;
window.ladeAlarme = ladeAlarme;
window.zeigeEinstellungen = zeigeEinstellungen;
window.speichereEinstellungen = speichereEinstellungen;
