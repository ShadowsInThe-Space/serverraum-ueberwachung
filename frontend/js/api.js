/**
 * API-Client für Serverraum-Überwachung
 * ================================
 * Kommuniziert mit dem FastAPI Backend
 *
 * @author Marc-Dennis Haberland
 * @date 04.03.2026
 * Projekt: Serverraum-Überwachung (IHK-Abschlussprojekt)
 */

// Basis-URL für API (kann in Einstellungen geändert werden)
let apiBaseUrl = window.location.origin.replace(/\/$/, '');

/**
 * Setzt die API-Basis-URL
 * @param {string} url - Neue URL
 */
function setApiBaseUrl(url) {
    apiBaseUrl = url.replace(/\/$/, ''); // Entferne trailing slash
    localStorage.setItem('apiEndpoint', apiBaseUrl);
}

/**
 * Generischer API-Request
 * @param {string} endpoint - API-Endpoint
 * @param {string} method - HTTP-Methode
 * @param {object} data - Daten für POST/PUT
 * @returns {Promise}
 */
async function apiRequest(endpoint, method = 'GET', data = null) {
    const url = `${apiBaseUrl}${endpoint}`;

    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();

    } catch (error) {
        console.error(`API Fehler: ${endpoint}`, error);
        throw error;
    }
}

/**
 * Holt System-Status
 * @returns {Promise<object>}
 */
async function getStatus() {
    return await apiRequest('/status');
}

/**
 * Holt Liste aller Sensoren
 * @returns {Promise<array>}
 */
async function getSensoren() {
    return await apiRequest('/sensoren');
}

/**
 * Holt Messungen für einen Sensor
 * @param {string} sensorId - Sensor-ID
 * @param {number} limit - Anzahl Messungen
 * @returns {Promise<array>}
 */
async function getMessungen(sensorId, limit = 100) {
    return await apiRequest(`/sensoren/${sensorId}/messungen?limit=${limit}`);
}

/**
 * Holt Statistik für einen Sensor
 * @param {string} sensorId - Sensor-ID
 * @param {number} stunden - Zeitraum in Stunden
 * @returns {Promise<object>}
 */
async function getStatistik(sensorId, stunden = 24) {
    return await apiRequest(`/sensoren/${sensorId}/statistik?stunden=${stunden}`);
}

/**
 * Holt alle Alarme
 * @param {string} status - Filter: 'aktiv', 'quittiert', 'alle'
 * @param {number} limit - Anzahl
 * @returns {Promise<array>}
 */
async function getAlarme(status = 'alle', limit = 100) {
    let endpoint = `/alarme?limit=${limit}`;
    if (status && status !== 'alle') {
        endpoint += `&status=${status}`;
    }
    return await apiRequest(endpoint);
}

/**
 * Quittiert einen Alarm
 * @param {number} alarmId - Alarm-ID
 * @returns {Promise}
 */
async function quittiereAlarm(alarmId) {
    return await apiRequest(`/alarme/${alarmId}/quittieren`, 'POST');
}

/**
 * Löscht einen Alarm
 * @param {number} alarmId - Alarm-ID
 * @returns {Promise}
 */
async function loescheAlarm(alarmId) {
    return await apiRequest(`/alarme/${alarmId}`, 'DELETE');
}

/**
 * Sendet eine Alarm-Erinnerung per Email
 * @param {number} alarmId - Alarm-ID
 * @returns {Promise}
 */
async function sendeAlarmEmail(alarmId) {
    return await apiRequest(`/alarme/${alarmId}/email`, 'POST');
}

/**
 * Holt alle gesendeten Alarm-Emails
 * @param {number} limit - Anzahl
 * @returns {Promise<array>}
 */
async function getAlarmEmails(limit = 100) {
    return await apiRequest(`/alarm-emails?limit=${limit}`);
}

/**
 * Prüft ob API erreichbar ist
 * @returns {Promise<boolean>}
 */
async function checkApiConnection() {
    try {
        await getStatus();
        return true;
    } catch {
        return false;
    }
}

// Exportiere Funktionen für globale Nutzung
window.api = {
    setApiBaseUrl,
    getStatus,
    getSensoren,
    getMessungen,
    getStatistik,
    getAlarme,
    quittiereAlarm,
    loescheAlarm,
    sendeAlarmEmail,
    getAlarmEmails,
    checkApiConnection,
    get baseUrl() { return apiBaseUrl; }
};
