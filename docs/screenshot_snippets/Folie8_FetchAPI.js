/**
 * @file Folie8_FetchAPI.js
 * Fetch-API Aufruf für Sensordaten
 */

// Generischer API-Request mit Fetch
async function apiRequest(endpoint, method = 'GET', data = null) {
    const url = `${apiBaseUrl}${endpoint}`;

    const options = {
        method: method,
        headers: { 'Content-Type': 'application/json' }
    };

    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);  // Fetch!

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.error(`API Fehler: ${endpoint}`, error);
        throw error;
    }
}

// Sensordaten abrufen
async function getSensoren() {
    return await apiRequest('/sensoren');
}
