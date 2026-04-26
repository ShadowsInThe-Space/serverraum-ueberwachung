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

    // WLAN-Signal Simulation starten
    starteWifiSignalSimulation();

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
 * Startet die Simulation des WLAN-Signals
 */
function starteWifiSignalSimulation() {
    // Initiales WLAN-Signal setzen
    simuliereWifiSignal();

    // Alle 5 Sekunden aktualisieren
    setInterval(simuliereWifiSignal, 5000);
}

/**
 * Simuliert ein WLAN-Signal (RSSI Wert zwischen -45 und -75 dBm)
 */
function simuliereWifiSignal() {
    // Typischer WLAN RSSI Bereich: -30 (sehr gut) bis -90 (schwach)
    // Wir simulieren einen relativ stabilen Wert mit kleinen Schwankungen
    const basisWert = -55;
    const schwankung = Math.floor(Math.random() * 20) - 10; // -10 bis +10
    const rssi = basisWert + schwankung;

    const wifiElement = document.getElementById('wifi-signal');
    if (wifiElement) {
        wifiElement.textContent = rssi + ' dBm';

        // Farbe basierend auf Signalstärke
        if (rssi >= -50) {
            wifiElement.style.color = '#22c55e'; // Grün - Sehr gut
        } else if (rssi >= -65) {
            wifiElement.style.color = '#eab308'; // Gelb - Gut
        } else if (rssi >= -75) {
            wifiElement.style.color = '#f97316'; // Orange - Mittel
        } else {
            wifiElement.style.color = '#ef4444'; // Rot - Schwach
        }
    }
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

    // Sensor-Typen für lesbare Namen
    const sensorTypNamen = {
        'ds18b20': 'Temperatur (DS18B20)',
        'sht31': 'Temperatur/Feuchtigkeit (SHT31)',
        'mq2': 'Rauchgas (MQ2)',
        'pir': 'Bewegung (PIR)',
        'PIR': 'Bewegung (PIR)'
    };

    sensoren.forEach(sensor => {
        const option = document.createElement('option');
        option.value = sensor.sensor_id;
        // Name aus DB oder generiert aus Typ
        const typName = sensorTypNamen[sensor.sensor_typ] || sensor.sensor_typ;
        option.textContent = sensor.name || sensor.sensor_id + ' (' + typName + ')';
        dropdown.appendChild(option);
    });
}

/**
 * Bestimmt den Status-Label-Text basierend auf dem Sensor-Status
 */
function getStatusLabel(status) {
    switch (status) {
        case 'alarm': return 'Alarm';
        case 'warnung': return 'Warnung';
        case 'inaktiv': return 'Inaktiv';
        default: return 'Normal';
    }
}

/**
 * Bestimmt die CSS-Klasse für den Status
 */
function getStatusColorClass(status) {
    switch (status) {
        case 'alarm': return 'status-alarm';
        case 'warnung': return 'status-warning';
        case 'inaktiv': return 'status-inactive';
        default: return 'status-normal';
    }
}

/**
 * Aktualisiert die Sensor-Karten mit barrierefreier Struktur
 */
function aktualisiereSensorKarten(sensoren) {
    const container = document.getElementById('sensor-karten');
    if (!container) return;

    container.innerHTML = '';

    // Sensor-Konfiguration - IDs müssen mit der DB übereinstimmen
    // DB: ds18b20_01, sht31_temp_01, sht31_feuchte_01, mq2_01, pir_01
    const sensorConfig = [
        { id: 'ds18b20_01', name: 'Temperatur (DS18B20)', einheit: '°C' },
        { id: 'sht31_temp_01', name: 'Temperatur (SHT31)', einheit: '°C' },
        { id: 'sht31_feuchte_01', name: 'Feuchtigkeit (SHT31)', einheit: '%' },
        { id: 'mq2_01', name: 'Rauchgas (MQ2)', einheit: 'ppm' },
        { id: 'pir_01', name: 'Bewegung (PIR)', einheit: '' }
    ];

    sensorConfig.forEach(config => {
        const sensor = sensoren.find(s => s.sensor_id === config.id);
        const wert = sensor && sensor.letzte_messung !== null ? sensor.letzte_messung : '--';
        const status = sensor && sensor.letzte_messung !== null ? 'normal' : 'inaktiv';
        const statusLabel = getStatusLabel(status);
        const statusColorClass = getStatusColorClass(status);
        const borderClass = status === 'alarm' ? 'border-l-status-alarm' :
                           status === 'warnung' ? 'border-l-status-warning' :
                           status === 'inaktiv' ? 'border-l-status-inactive' : 'border-l-status-normal';

        // Karte erstellen mit Semantic HTML und ARIA
        const card = document.createElement('article');
        card.className = `rounded-xl p-6 status-card border-l-4 ${borderClass}`;
        card.style.backgroundColor = 'var(--bg-secondary)';
        card.setAttribute('role', 'listitem');
        card.setAttribute('aria-labelledby', `sensor-${config.id}-name`);

        // Zeitstempel formatieren
        const zeitstempel = sensor && sensor.letzte_zeit ? formatZeitstempel(sensor.letzte_zeit) : 'Keine Daten';
        const zeitstempelISO = sensor && sensor.letzte_zeit ? sensor.letzte_zeit.replace(/(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6') : '';

        // Trend-Indikator (simplifiziert - basierend auf.previous_wert wenn verfügbar)
        let trendLabel = '';
        let trendAria = '';
        if (sensor && sensor.previous_wert !== undefined && sensor.letzte_messung !== null) {
            const diff = sensor.letzte_messung - sensor.previous_wert;
            if (diff > 0.5) {
                trendLabel = 'steigend';
                trendAria = ', Tendenz: steigend';
            } else if (diff < -0.5) {
                trendLabel = 'fallend';
                trendAria = ', Tendenz: fallend';
            } else {
                trendLabel = 'stabil';
                trendAria = ', Tendenz: stabil';
            }
        }

        card.innerHTML = `
            <header class="mb-4">
                <h3 id="sensor-${config.id}-name" class="text-sm font-medium uppercase tracking-wider" style="color: var(--text-secondary);">
                    ${config.name}
                </h3>
            </header>

            <div class="sensor-wert mb-4" aria-live="polite">
                <span class="text-4xl font-bold" id="sensor-${config.id}-wert" aria-label="Aktueller Wert: ${wert} ${config.einheit}" style="color: var(--text-primary);">
                    ${wert}
                </span>
                <span class="text-xl ml-1" style="color: var(--text-secondary);">${config.einheit}</span>
            </div>

            <div class="sensor-status ${statusColorClass} flex items-center gap-2 mb-4" role="status">
                <span class="status-punkt bg-${statusColorClass}" aria-hidden="true"></span>
                <span class="status-label text-sm font-medium" aria-label="Status: ${statusLabel}${trendAria}">
                    ${statusLabel}${trendLabel ? ' (' + trendLabel + ')' : ''}
                </span>
            </div>

            <footer>
                <time
                    class="text-xs"
                    datetime="${zeitstempelISO}"
                    aria-label="Letzte Messung: ${zeitstempel}"
                    style="color: var(--text-muted);"
                >
                    ${zeitstempel}
                </time>
            </footer>
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
            div.className = 'alarm-card rounded-lg p-4 flex justify-between items-center';

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
        ladeAlarmEmails();
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
 * Zeigt Alarm-Tabelle mit barrierefreier Struktur
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

        const istAktiv = alarm.status === 'aktiv';
        const statusClass = istAktiv ? 'text-status-alarm' : 'text-gray-500';
        const statusLabel = istAktiv ? 'Aktiv' : 'Quittiert';

        tr.innerHTML = `
            <td class="py-3 pr-4">
                <div class="flex items-center gap-2 ${statusClass}" role="status">
                    <span class="status-punkt ${istAktiv ? 'bg-status-alarm' : 'bg-gray-500'}" aria-hidden="true"></span>
                    <span>${statusLabel}</span>
                </div>
            </td>
            <td class="py-3 pr-4">${alarm.sensor_id || '--'}</td>
            <td class="py-3 pr-4">${alarm.alarm_typ || '--'}</td>
            <td class="py-3 pr-4">${alarm.wert ?? '--'}</td>
            <td class="py-3 pr-4">${alarm.created_at ? new Date(alarm.created_at).toLocaleString('de-DE') : '--'}</td>
            <td class="py-3">
                ${istAktiv ? `
                <select
                    onchange="handleAlarmAktion(${alarm.id}, this.value); this.value='';"
                    class="rounded px-2 py-1 text-sm cursor-pointer focus-visible:ring-2 focus-visible:ring-blue-500"
                    style="background-color: var(--bg-tertiary); border-color: var(--border-color); color: var(--text-primary);"
                    aria-label="Aktion für Alarm ${alarm.id}"
                >
                    <option value="">Aktion...</option>
                    <option value="quittieren">Quittieren</option>
                    <option value="email">Per Email senden</option>
                    <option value="loeschen">Löschen</option>
                </select>
                ` : (alarm.letzte_aktion || '--')}
            </td>
        `;

        tbody.appendChild(tr);
    });
}

/**
 * Behandelt Alarm-Aktionen aus dem Dropdown
 */
async function handleAlarmAktion(alarmId, aktion) {
    if (!aktion) return;

    switch (aktion) {
        case 'quittieren':
            await window.api.quittiereAlarm(alarmId);
            ladeAlarme();
            ladeAlarmEmails();
            break;
        case 'email':
            try {
                await window.api.sendeAlarmEmail(alarmId);
                alert('Erinnerungs-Email wurde gesendet!');
                ladeAlarmEmails();
            } catch (error) {
                console.error('Fehler beim Senden:', error);
                alert('Email senden fehlgeschlagen!');
            }
            break;
        case 'loeschen':
            if (confirm('Alarm wirklich löschen? Dies kann nicht rückgängig gemacht werden.')) {
                try {
                    await window.api.loescheAlarm(alarmId);
                    ladeAlarme();
                    ladeAlarmEmails();
                } catch (error) {
                    console.error('Fehler beim Löschen:', error);
                    alert('Löschen fehlgeschlagen!');
                }
            }
            break;
    }
}

/**
 * Lädt Alarm-Emails
 */
async function ladeAlarmEmails() {
    const filter = document.getElementById('alarm-filter')?.value || 'alle';

    try {
        const emails = await window.api.getAlarmEmails();
        zeigeAlarmEmailsTabelle(emails);
    } catch (error) {
        console.error('Fehler beim Laden der Alarm-Emails:', error);
    }
}

/**
 * Zeigt Alarm-Emails-Tabelle mit barrierefreier Struktur
 */
function zeigeAlarmEmailsTabelle(emails) {
    const tbody = document.getElementById('alarm-email-tabelle');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (!emails || emails.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-gray-500 py-4">Keine Alarm-Emails vorhanden</td></tr>';
        return;
    }

    emails.forEach(email => {
        const tr = document.createElement('tr');
        tr.className = 'border-b border-gray-700';

        // Status-Badge für Email
        const statusClass = email.sende_status === 'erfolgreich' ? 'text-green-500' :
                          email.sende_status === 'fehlgeschlagen' ? 'text-red-500' : 'text-yellow-500';
        const statusLabel = email.sende_status === 'erfolgreich' ? 'Erfolgreich' :
                          email.sende_status === 'fehlgeschlagen' ? 'Fehlgeschlagen' : 'Ausstehend';

        // Antwort-Indikator
        const antwortBadge = email.hat_geantwortet ?
            `<span class="bg-green-600 text-white text-xs px-2 py-1 rounded" title="${email.anzahl_antworten} Antwort(en)">Ja (${email.anzahl_antworten})</span>` :
            '<span class="text-gray-500 text-sm">Nein</span>';

        // Zeit formatieren
        const zeitpunkt = email.created_at ? new Date(email.created_at).toLocaleString('de-DE') : '--';

        tr.innerHTML = `
            <td class="py-3 pr-4 text-sm" style="color: var(--text-primary);">${zeitpunkt}</td>
            <td class="py-3 pr-4 text-sm" style="color: var(--text-primary);">${email.sensor_id || '--'}</td>
            <td class="py-3 pr-4 text-sm" style="color: var(--text-primary);">${email.alarm_typ || '--'}</td>
            <td class="py-3 pr-4 text-sm" style="color: var(--text-primary);">${email.empfaenger || '--'}</td>
            <td class="py-3 pr-4">
                <span class="${statusClass} text-sm font-medium">${statusLabel}</span>
            </td>
            <td class="py-3">
                ${antwortBadge}
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
window.ladeAlarmEmails = ladeAlarmEmails;
window.handleAlarmAktion = handleAlarmAktion;
window.zeigeEinstellungen = zeigeEinstellungen;
window.speichereEinstellungen = speichereEinstellungen;
